#!/usr/bin/env python3
"""
minesweeper script

Continuous process, on each node via DaemonSet,
to identify processes that could be considered for termination:

- determine which processes are "suspicious" (see herorat.py)
- produce report on suspicious pods:
    - show running processes (`ps -f -u$uid`)
    - tail pod logs
- automatically terminate pods likely to be abuse, etc.
"""

import asyncio
import json
import os
import pprint
import re
import socket
import sys
import threading
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from operator import attrgetter
from subprocess import check_output
from textwrap import indent

import kubernetes.client
import kubernetes.config
from kubernetes.stream import stream

# herorat located in secrets/minesweeper/
import herorat
from herorat import inspect_pod
from herorat import inspect_process


kubernetes.config.load_incluster_config()
kube = kubernetes.client.CoreV1Api()
local = threading.local()
config = {}
hostname = os.environ.get("NODE_NAME", socket.gethostname())

default_config = {
    "userid": 1000,
    "threads": 8,
    "interval": 300,
    "namespace": os.environ.get("NAMESPACE", "default"),
    "log_tail_lines": 100,
}

default_config.update(herorat.default_config)


def get_kube():
    """Get thread-local kubernetes client

    kubernetes client objects aren't threadsafe, I guess
    """
    if not hasattr(local, "kube"):
        local.kube = kubernetes.client.CoreV1Api()
    return local.kube


def get_output(cmd, **kwargs):
    """Wrapper for check_output that returns text"""
    return check_output(cmd, **kwargs).decode("utf8", "replace")


@dataclass
class Proc:
    """Class for containing information about a process"""

    # from parsing ps output
    # required fields
    uid: int
    pid: int
    state: str
    cmd: str
    # default fields
    cpu: int = 0
    ppid: int = 0
    vsz: int = 0
    rss: int = 0
    stime: float = 0
    time: float = 0

    # derived fields from inspection with herorat
    suspicious: bool = False
    should_terminate: bool = False

    # class attributes:

    # ps columns:
    # should be a corresponding attribute on the dataclass for each
    ps_columns = [
        "uid",
        "pid",
        "ppid",
        "c",
        "vsz",
        "rss",
        "stat",
        "stime",
        "time",
        # cmd *must* be last
        "cmd",
    ]

    # map ps column names to dataclass attributes
    # only for fields where we want them to differ
    _ps_column_map = {
        "c": "cpu",
        "stat": "state",
    }

    @classmethod
    def attr_for_column(cls, key):
        """Map a ps column to an attribute name

        default: use column name
        """
        return cls._ps_column_map.get(key, key)


def parse_t(timestring):
    """Parse a [HH:]MM:SS time string into a float of seconds (inf if unparseable)"""
    if ":" not in timestring:
        return float("inf")

    if "-" in timestring:
        print("Weird time: %s" % timestring)
        return float("inf")

    parts = [int(part) for part in timestring.split(":")]
    seconds = parts[-1]
    seconds += 60 * parts[-2]
    if len(parts) == 3:
        seconds += 3600 * parts[-3]
    return seconds


def parse_ps(out):
    """parse ps output into Proc objects"""
    column_names = Proc.ps_columns
    n_columns = len(column_names)

    for line in out.splitlines()[1:]:
        fields = line.split(None, n_columns - 1)
        kwargs = {}
        for col, value in zip(column_names, fields):
            key = Proc.attr_for_column(col)
            if key in {"stime", "time"}:
                try:
                    value = parse_t(value)
                except Exception as e:
                    print(e)
                    print(line)
                    raise
            elif Proc.__annotations__[key] is int:
                # cast int fields
                value = int(value)
            kwargs[key] = value

        if "Z" in kwargs["state"]:
            # ignore zombie processes
            continue

        yield Proc(**kwargs)


def get_procs(userid):
    """Get all container processes running with a given user id"""
    procs = []
    columns = ",".join(Proc.ps_columns)
    for proc in parse_ps(get_output(["ps", f"-o{columns}", f"-u{userid}"])):
        procs.append(inspect_process(proc))
    procs = sorted(procs, key=attrgetter("cpu"), reverse=True)
    return procs


def get_pods():
    """Get all the pods in our namespace"""
    kube = get_kube()
    namespace = config["namespace"]
    # _preload_content=False doesn't even json-parse list results??
    resp = kube.list_namespaced_pod(namespace, _preload_content=False)
    return json.loads(resp.read().decode("utf8"))["items"]


def pods_by_uid(pods):
    """Construct a dict of pods, keyed by pod uid"""
    return {pod["metadata"]["uid"]: pod for pod in pods}


def get_pod_for_proc(proc, pods):
    """Identify the pod for a process"""
    if "defunct" in proc.cmd:
        return

    try:
        with open(f"/proc/{proc.pid}/cgroup") as f:
            cgroups = f.read()
    except Exception:
        if proc.suspicious:
            print(f"Couldn't find pod for {proc}\n", end="")
        return

    m = re.search("/pod([^/]+)", cgroups)
    if m is None:
        if proc.suspicious:
            print(f"Couldn't find pod for {proc}: {cgroups}\n", end="")
        return

    pod_uid = m.group(1)

    pod = pods.get(pod_uid)
    if not pod:
        if proc.suspicious:
            print(f"Couldn't find pod for {proc}: {pod_uid}\n", end="")
    return pod


def associate_pods_procs(pods, procs):
    """Associate pods and processes
    For all pods, defines pod["minesweeper"]["procs"] = list_of_procs_in_pod

    Returns (pods, procs_without_pods)
    """
    for pod in pods.values():
        pod["minesweeper"] = {
            "procs": [],
        }
    procs_without_pods = []
    for proc in procs:
        pod = get_pod_for_proc(proc, pods)
        if not pod:
            procs_without_pods.append(proc)
        else:
            pod["minesweeper"]["procs"].append(proc)

    return pods, procs_without_pods


def ps_pod(pod, userid=1000):
    """Get ps output from a single pod"""
    kube = get_kube()
    try:
        client = stream(
            kube.connect_get_namespaced_pod_exec,
            pod["metadata"]["name"],
            namespace=pod["metadata"]["namespace"],
            command=["ps", "-f", f"-u{userid}"],
            stderr=True,
            stdin=False,
            stdout=True,
            _preload_content=False,
        )
        client.run_forever(timeout=60)
        stderr = client.read_stderr()
        if stderr.strip():
            print(f"err! {stderr}", file=sys.stderr)
        stdout = client.read_stdout()

        returncode = client.returncode
        if returncode:
            raise RuntimeError(f"stdout={stdout}\nstderr={stderr}")
        return stdout
    except Exception as e:
        return f"Error reporting on ps in {pod['metadata']['name']}: {e}"


def log_pod(pod):
    """Return the logs for a suspicious pod"""
    kube = get_kube()
    try:
        return kube.read_namespaced_pod_log(
            pod["metadata"]["name"],
            namespace=pod["metadata"]["namespace"],
            tail_lines=config["log_tail_lines"],
        )
    except Exception as e:
        return f"Error collecting logs for {pod['metadata']['name']}: {e}"


async def report_pod(pod):
    """Produce a report on a single pod"""
    pod_name = pod["metadata"]["name"]
    ps_future = in_pool(lambda: ps_pod(pod))
    logs_future = in_pool(lambda: log_pod(pod))
    ps, logs = await asyncio.gather(ps_future, logs_future)
    print(
        "\n".join(
            [
                pod_name,
                f"ps {pod_name}:",
                indent(ps, "    "),
                f"logs {pod_name}:",
                indent(logs, "    "),
            ]
        )
    )


def terminate_pod(pod):
    """Call in a thread to terminate a pod"""
    namespace = pod["metadata"]["namespace"]
    name = pod["metadata"]["name"]
    print(f"Deleting pod {name}")
    kube = get_kube()
    kube.delete_namespaced_pod(name=name, namespace=namespace)


async def node_report(pods=None, userid=1000):
    """Print a report of suspicious processes on a single node"""
    if pods is None:
        pods = pods_by_uid(await in_pool(get_pods))
    procs = await in_pool(lambda: get_procs(userid))
    print(f"Total processes for {hostname}: {len(procs)}\n", end="")
    pods, procs_without_pod = associate_pods_procs(pods, procs)
    suspicious_pods = [pod for pod in pods.values() if inspect_pod(pod)["suspicious"]]
    suspicious_procs_without_pod = [p for p in procs_without_pod if p.suspicious]
    # filter to only suspicious processes
    procs = [p for p in procs if p.suspicious]
    print(f"Processes of interest for {hostname}: {len(procs)}")
    print(f"Pods of interest for {hostname}: {len(suspicious_pods)}")

    # report on all suspicious pods
    report_futures = []
    for pod in suspicious_pods:
        fut = asyncio.ensure_future(report_pod(pod))
        report_futures.append(fut)
        await asyncio.sleep(0)

    # report on suspicious processes with no matching pod
    if suspicious_procs_without_pod:
        print(
            f"No pods found for {len(suspicious_procs_without_pod)} suspicious processes on {hostname}:"
        )
        for proc in suspicious_procs_without_pod:
            print(f"  {proc.pid}: {proc.cmd}")

    if report_futures:
        await asyncio.gather(*report_futures)

    # finally, terminate pods that meet the immediate termination condition
    pods_to_terminate = [
        pod for pod in suspicious_pods if pod["minesweeper"]["should_terminate"]
    ]
    if pods_to_terminate:
        terminate_futures = [
            in_pool(partial(terminate_pod, pod)) for pod in pods_to_terminate
        ]
        await asyncio.gather(*terminate_futures)


def get_pool(n=None):
    """Get the global thread pool executor"""
    if get_pool._pool is None:
        get_pool._pool = ThreadPoolExecutor(config["threads"])
    return get_pool._pool


get_pool._pool = None


def in_pool(func):
    f = get_pool().submit(func)
    return asyncio.wrap_future(f)


def load_config():
    """load config from mounted config map

    may change during run, so reload from file each time
    """
    global config
    config.update(default_config)
    config_file = "/etc/minesweeper/minesweeper.json"
    if os.path.isfile(config_file):
        with open(config_file) as f:
            file_config = json.load(f)
        config.update(file_config)
        # sync global config with herorat
        herorat.config = config
        print("Loaded config:")
        pprint.pprint(config)
    else:
        print(f"No such file: {config_file}")

    return config


async def main():
    """Main entrypoint: run node_report periodically forever"""
    while True:
        # reload since configmap can change
        load_config()
        await node_report(userid=config["userid"])
        await asyncio.sleep(config["interval"])


if __name__ == "__main__":
    asyncio.run(main())
