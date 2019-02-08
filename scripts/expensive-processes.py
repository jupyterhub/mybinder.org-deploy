#!/usr/bin/env python3

import asyncio
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
import json
from operator import attrgetter
import os
import pipes
import re
from subprocess import check_output, run
import sys

import kubernetes.client
import kubernetes.config

project = "binder-prod"
kube_ctx = "prod"
kube_ns = "prod"

kubernetes.config.load_kube_config()
kube = kubernetes.client.CoreV1Api()

Proc = namedtuple("Proc", ["pid", "ppid", "cpu", "stime", "time", "cmd"])


def gcloud(*args):
    cmd = ["gcloud", "--format=json", f"--project={project}"]
    cmd.extend(args)
    out = check_output(cmd).decode("utf8", "replace")
    return json.loads(out)


def ssh(instance, ssh_cmd):
    """execute a command via ssh on the remote host"""
    if isinstance(ssh_cmd, list):
        cmd = " ".join(map(pipes.quote, ssh_cmd))
    cmd = [
        "gcloud",
        f"--project={project}",
        "compute",
        "ssh",
        instance,
        "--zone=us-central1-a",
        "--ssh-flag=-T",
        "--",
        ssh_cmd,
    ]
    return check_output(cmd, stdin=open(os.devnull)).decode("utf8", "replace")


def get_instances():
    """Get the instance names"""
    instance_json = gcloud("compute", "instances", "list")
    instances = []
    for i in instance_json:
        name = i["name"]
        if any(x in name for x in ('g47m', '6h5b')):
            continue
        instances.append(name)
    return instances


def parse_t(timestring):
    """Parse a [HH:]MM:SS time string"""
    if ":" not in timestring:
        return float("inf")

    if '-' in timestring:
        print("Weird time: %s" % timestring)
        return float("inf")

    parts = [int(part) for part in timestring.split(":")]
    seconds = parts[-1]
    seconds += 60 * parts[-2]
    if len(parts) == 3:
        seconds += 3600 * parts[-3]
    return seconds


def parse_ps(out):
    """parse ps -fu output"""
    # UID        PID  PPID  C STIME TTY          TIME CMD
    for line in out.splitlines()[1:]:
        uid, pid, ppid, cpu, stime, tty, t, cmd = line.split(None, 7)
        pid = int(pid)
        ppid = int(pid)
        cpu = int(cpu)
        try:
            stime = parse_t(stime)
            t = parse_t(t)
        except Exception as e:
            print(e)
            print(line)
            raise

        yield Proc(pid, ppid, cpu, stime, t, cmd)


def get_procs(instance):
    """Get all container processes on an instance"""
    procs = list(parse_ps(ssh(instance, "ps -fu 1000")))
    procs = sorted(procs, key=attrgetter("cpu"), reverse=True)
    return procs


def get_pods():
    """Get all the pods in kubernetes"""
    return kube.list_pod_for_all_namespaces().items


def pods_by_uid(pods):
    """Construct a dict of pods by uid"""
    return {pod.metadata.uid: pod for pod in pods}


def get_pod(instance, proc, pods=None):
    """Identify the pod for a process"""
    if pods is None:
        pods = pods_by_uid(get_pods())
    if "defunct" in proc.cmd:
        return

    try:
        cgroups = ssh(instance, f"cat /proc/{proc.pid}/cgroup")
    except Exception:
        print(f"Couldn't find pod for {proc}\n", end="")
        return

    m = re.search("/pod([^/]+)", cgroups)
    if m is None:
        print(f"Couldn't find pod for {proc}: {cgroups}\n", end="")
        return

    pod_uid = m.group(1)

    pod = pods.get(pod_uid)
    if not pod:
        print(f"Couldn't find pod for {proc}: {pod_uid}\n", end="")
    return pod


def identify_miners(instance, procs=None, pods=None):
    if pods is None:
        pods = pods_by_uid(get_pods())
    if procs is None:
        procs = get_procs(instance)
    miners = [p for p in procs if suspicious_cmd(p.cmd) and "<defunct>" not in p.cmd]
    miner_pods = [get_pod(instance, p, pods) for p in miners]
    return miner_pods


def ps_pod(pod):
    try:
        return check_output(
            [
                "kubectl",
                f"--namespace={kube_ns}",
                "exec",
                pod.metadata.name,
                "--",
                "ps",
                "-f",
                "-u1000",
            ],
            stdin=open(os.devnull, "rb"),
        ).decode(
            "utf8", "replace"
        )

    # exec doesn't work in Python API
    # return kube.connect_get_namespaced_pod_exec(
    #     pod.metadata.name,
    #     kube_ns,
    #     command=["ps", "-f", "-u1000"],
    #     stdout=True,
    #     stderr=False,
    #     stdin=False,
    #     tty=True,
    # )
    except Exception as e:
        return f"Error reporting on {pod.metadata.name}: {e}"


async def report_pod(pod, instance):
    """Produce a report on a pod"""
    ps = await in_pool(lambda: ps_pod(pod))
    print("\n".join([pod.metadata.name, instance, ps]))


def suspicious_cmd(cmd):
    """Is a command suspicious?"""
    cmd = cmd.lower()
    if "xmrig" in cmd:
        return True

    if "socat" in cmd:
        return True

    if "onion" in cmd:
        return True

    if "base64" in cmd:
        return True

    if "./python" in cmd:
        return True


async def instance_report(instance, pods=None):
    if pods is None:
        pods = await in_pool(get_pods)
        pods = pods_by_uid(pods)
    procs = await in_pool(lambda: get_procs(instance))
    print(f"procs for {instance}: {len(procs)}\n", end="")
    procs = [p for p in procs if p.cpu > 25 or suspicious_cmd(p.cmd)]
    print(f"procs of interest for {instance}: {len(procs)}\n", end="")
    seen_pods = set()
    report_futures = []
    no_pods = []
    for proc in procs:
        pod = get_pod(instance, proc, pods)
        if pod and pod.metadata.name not in seen_pods:
            seen_pods.add(pod.metadata.name)
            report_futures.append(asyncio.ensure_future(report_pod(pod,
                                                                   instance)))
            await asyncio.sleep(0)
        else:
            no_pods.append(proc)
    if no_pods:
        print(f"No pods for")
        for proc in no_pods:
            print(f"  {proc.pid}: {proc.cmd}")
    if report_futures:
        await asyncio.gather(*report_futures)


async def all_reports(instances=None, pods=None):
    if instances is None:
        instances = get_instances()
    futures = []
    if pods is None:
        pods = pods_by_uid(get_pods())
    futures = []
    for instance in instances:
        futures.append(asyncio.ensure_future(instance_report(instance, pods)))
        await asyncio.sleep(0)
    await asyncio.gather(*futures)


def get_pool(n=8):
    """Get the global thread pool executor"""
    if get_pool._pool is None:
        get_pool._pool = ThreadPoolExecutor(n)
    return get_pool._pool


get_pool._pool = None


async def in_pool(func):
    f = get_pool().submit(func)
    return await asyncio.wrap_future(f)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(all_reports())
