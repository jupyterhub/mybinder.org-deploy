#!/usr/bin/env python3
"""
minesweeper script

Continuous process, on each node via DaemonSet,
to identify processes that could be considered for termination:

- determine which processes are "suspicious" (see herorat.py)
- produce report on suspicious pods:
    - show running processes (`ps aux`)
    - tail pod logs
- automatically terminate pods likely to be abuse, etc.
"""

import asyncio
import copy
import glob
import json
import os
import pprint
import re
import signal
import socket
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from operator import attrgetter
from textwrap import indent

# herorat located in secrets/minesweeper/
import herorat
import kubernetes.client
import kubernetes.config
import psutil
from herorat import inspect_pod, inspect_process
from kubernetes.stream import stream

kubernetes.config.load_incluster_config()
kube = kubernetes.client.CoreV1Api()
local = threading.local()
config = {}
hostname = os.environ.get("NODE_NAME", socket.gethostname())

default_config = {
    "userid": 1000,
    "inspect_procs_without_pod": False,
    "inspect_dind": True,
    "threads": 8,
    "interval": 300,
    "namespace": os.environ.get("NAMESPACE", "default"),
    "pod_selectors": {
        "label_selector": "component=singleuser-server",
        "field_selector": f"spec.nodeName={hostname}",
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
    """Proc is a dict subclass with attribute-access for keys

    suspicious and should_terminate are added via inspection.
    They can be booleans or truthy strings explaining
    why they are suspicious or should be terminated.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("suspicious", False)
        kwargs.setdefault("should_terminate", False)
        super().__init__(**kwargs)

        # secondary derived fields
        # cmd is the command-line as a single string
        self["cmd"] = " ".join(self["cmdline"])
        # cpu_total is the sum of cpu times (user, system, children, etc.)
        self["cpu_total"] = sum(kwargs.get("cpu_times", []))

    def __repr__(self):
        key_fields = ", ".join(
            [
                f"{key}={self.get(key)}"
                for key in [
                    "pid",
                    "status",
                    "suspicious",
                    "should_terminate",
                    "cmd",
                ]
                if self.get(key) is not None
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
        # TODO: should we filter to userid?
        # For now: skip userid filtering, because we
        # want to catch all processes in pods, even if they
        # ran setuid
        # if p.info["uids"].real != userid:
        #     continue
        if not p.info["cmdline"]:
            # ignore empty commands, e.g. kernel processes
            continue

        proc = Proc(**p.info)
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


def get_all_pod_uids():
    """Return mapping of pid to pod uid"""

    pod_uids = {}
    for cgroup_file in glob.glob("/proc/[0-9]*/cgroup"):
        pid = int(cgroup_file.split("/")[-2])

        try:
            with open(cgroup_file) as f:
                cgroups = f.read()

        except FileNotFoundError:
            # process deleted, ignore
            continue

        m = re.search("/pod([^/]+)", cgroups)
        if m is None:
            # not a pod proc
            continue
        pod_uids[pid] = m.group(1)
    return pod_uids


def get_dind_procs():
    """Return list of dind container processes

    Identified by cgroup
    """

    procs = []
    for cgroup_file in glob.glob("/proc/[0-9]*/cgroup"):
        pid = int(cgroup_file.split("/")[-2])

        try:
            with open(cgroup_file) as f:
                cgroups = f.read()

        except FileNotFoundError:
            # process deleted, ignore
            continue
        # the dind-created cgroups for build containers
        # are nested under an extra /docker/ level below the dind pod's own cgroup
        # dind pod itself: /kubepods/burstable/pod{u-u-i-d}/{abc123}
        # container run by dind: {dind_pod_cgroup}/docker/{def456}
        m = re.search("/pod[^/]+/[^/]+/docker/(.+)", cgroups)
        if m is None:
            # not a dind proc
            continue

        try:
            proc_dict = psutil.Process(pid).as_dict(config["proc_attrs"])
        except psutil.NoSuchProcess:
            pass
        procs.append(Proc(**proc_dict))
    return procs


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
    pod_uids = get_all_pod_uids()
    for proc in procs:
        pod_uid = pod_uids.get(proc.pid)
        pod = pods.get(pod_uid)
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
            command=["ps", "aux"],
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

    # inspect all procs in our pods
    user_procs = []
    for pod in pods.values():
        user_procs.extend(pod["minesweeper"]["procs"])
        pod["minesweeper"]["procs"] = [
            inspect_process(p) for p in pod["minesweeper"]["procs"]
        ]
    print(f"Total user pods for {hostname}: {len(pods)}\n", end="")
    print(f"Total user processes for {hostname}: {len(user_procs)}\n", end="")
    suspicious_pods = [pod for pod in pods.values() if inspect_pod(pod)["suspicious"]]

    print(f"Pods of interest for {hostname}: {len(suspicious_pods)}")

    # report on all suspicious pods
    report_futures = []
    for pod in suspicious_pods:
        fut = asyncio.ensure_future(report_pod(pod))
        report_futures.append(fut)
        await asyncio.sleep(0)

    # report on suspicious processes with no matching pod
    suspicious_procs_without_pod = []
    if config["inspect_procs_without_pod"]:
        procs_without_pod = [inspect_process(p) for p in procs_without_pod]
        suspicious_procs_without_pod = [p for p in procs_without_pod if p.suspicious]

    if suspicious_procs_without_pod:
        print(
            f"No pods found for {len(suspicious_procs_without_pod)} suspicious processes on {hostname}:"
        )
        for proc in suspicious_procs_without_pod:
            print(f"  {proc.pid}: {proc.cmd}")

    # report on suspicious dind processes
    if config["inspect_dind"]:
        dind_procs = [inspect_process(p) for p in get_dind_procs()]
        print(f"Total dind processes for {hostname}: {len(dind_procs)}")
        for proc in dind_procs:
            if proc.should_terminate:
                print(f"dind process should terminate: {proc}")
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except OSError as e:
                    print(f"Failed to kill {proc}: {e}")
            elif proc.suspicious:
                print(f"dind process is suspicious: {proc}")
        # FIXME: flake8 detected suspicious_dind_procs_without_pod to not be
        #        used, it seems like something partially implemented.
        suspicious_dind_procs_without_pod = [
            p for p in procs_without_pod if p.suspicious
        ]

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
    prior_config = copy.deepcopy(config)
    config.update(default_config)
    config_file = "/etc/minesweeper/minesweeper.json"
    if os.path.isfile(config_file):
        with open(config_file) as f:
            file_config = json.load(f)
        config.update(file_config)
        # sync global config with herorat
        herorat.config = config
    else:
        print(f"No such file: {config_file}")

    if config != prior_config:
        print("Loaded config:")
        pprint.pprint(config)

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
