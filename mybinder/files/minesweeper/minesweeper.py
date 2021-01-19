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
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from operator import attrgetter
from textwrap import indent

import kubernetes.client
import kubernetes.config
from kubernetes.stream import stream

import psutil

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
    "pod_selectors": {
        "label_selector": "component=singleuser-server",
    },
    "log_tail_lines": 100,
    # process attributes to retrieve
    # see psutil.as_dict docs for available fields:
    # https://psutil.readthedocs.io/en/latest/#psutil.Process.as_dict
    "proc_attrs": [
        "cmdline",
        "cpu_percent",
        "cpu_times",
        "exe",
        "memory_info",
        "name",
        "pid",
        "ppid",
        "status",
        "uids",
    ],
}

default_config.update(herorat.default_config)


def get_kube():
    """Get thread-local kubernetes client

    kubernetes client objects aren't threadsafe, I guess
    """
    if not hasattr(local, "kube"):
        local.kube = kubernetes.client.CoreV1Api()
    return local.kube


class Proc(dict):
    """Proc is a dict subclass with attribute-access for keys"""

    def __init__(self, **kwargs):
        kwargs.setdefault("suspicious", False)
        kwargs.setdefault("should_terminate", False)
        super().__init__(**kwargs)

        # secondary derived fields
        self["cmd"] = " ".join(self["cmdline"])

    def __repr__(self):
        key_fields = ", ".join(
            [
                f"{key}={self.get(key)}"
                for key in [
                    "pid",
                    "status",
                    "suspicious",
                    "should_terminate",
                ]
            ]
        )
        return f"{self.__class__.__name__}({key_fields})"

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


def get_procs(userid):
    """Get all container processes running with a given user id"""
    procs = []
    for p in psutil.process_iter(attrs=config["proc_attrs"]):
        if not p.info["exe"]:
            # ignore empty commands, e.g. kernel processes
            continue
        if p.info["uids"].real != userid:
            continue

        proc = inspect_process(Proc(**p.info))
        procs.append(proc)

    procs = sorted(procs, key=attrgetter("cpu_percent"), reverse=True)
    return procs


def get_pods():
    """Get all the pods in our namespace"""
    kube = get_kube()
    namespace = config["namespace"]
    # _preload_content=False doesn't even json-parse list results??
    resp = kube.list_namespaced_pod(
        namespace,
        _preload_content=False,
        **config["pod_selectors"],
    )
    return json.loads(resp.read().decode("utf8"))["items"]


def pods_by_uid(pods):
    """Construct a dict of pods, keyed by pod uid"""
    return {pod["metadata"]["uid"]: pod for pod in pods}


def get_pod_for_proc(proc, pods):
    """Identify the pod for a process"""
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
