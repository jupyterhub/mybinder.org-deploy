"""Script to identify when Docker-in-Docker stop working."""

import argparse
import datetime
import logging
import os

from fabric import Connection
from invoke import Responder
from kubernetes import client, config, watch

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("orc2-fix-dind-bot")
logger.setLevel(logging.WARNING)

NAMESPACE = "gesis"


def remove_docker_socket(host_IP):
    """Remove Docker socket"""
    ssh_password = os.getenv(f"PASSWORD_{host_IP.replace('.', '_')}")

    logger.info("Connecting to %s ...", host_IP)
    c = Connection(host_IP, user="ansible", connect_kwargs={"password": ssh_password})
    logger.info("Connected!", host_IP)

    logger.info("Removing Docker socket ...")
    sudopass = Responder(
        pattern=r"\[sudo\] password for .*:",
        response=f"{ssh_password}\n",
    )
    c.run("sudo rm -rf /var/run/dind/docker.sock/", pty=True, watchers=[sudopass])
    logger.info("Removed Docker socket.")


def remove_pods():
    """Remove Docker-in-Docker related pods"""
    logger.debug("Starting search for pods ...")
    api_response = v1.list_namespaced_pod(NAMESPACE)
    for pod in api_response.items:
        logger.debug("Pod %s is running on the cluster", pod.metadata.name)
        if pod.metadata.name.startswith(
            "binderhub-dind-"
        ) or pod.metadata.name.startswith("binderhub-image-cleaner-"):
            logger.info("Found pod %s", pod.metadata.name)
            pod_to_delete_name = pod.metadata.name
            logger.info("Requesting delete of pod %s ...", pod_to_delete_name)
            try:
                api_response = v1.delete_namespaced_pod(pod_to_delete_name, NAMESPACE)
                logger.info("Pod %s deleted.", pod_to_delete_name)
            except client.exceptions.ApiException as exception:
                logger.info(
                    "Fail to delete pod %s due %s", pod_to_delete_name, exception
                )
    logger.debug("Completed search for pods!")


def get_node_running_pod(pod_name):
    """Get node host's IP address running pod"""
    pod_status = v1.read_namespaced_pod(pod_name, namespace=NAMESPACE)
    logger.debug(pod_status)
    host_IP = pod_status.status.host_ip
    logger.info("%s is running on %s", pod_name, host_IP)
    return host_IP


def monitor_cluster():
    """Monitor pod"""
    while True:
        logger.info("Start monitoring ...")

        w = watch.Watch()
        for event in w.stream(v1.list_namespaced_event, namespace=NAMESPACE):
            pod_name = event["object"].involved_object.name
            if pod_name.startswith("binderhub-dind-"):
                if event["object"].type == "Warning":
                    logger.info("Found Warning event in %s", pod_name)
                    if event["object"].reason == "BackOff":
                        time_since_last_timestamp = (
                            datetime.datetime.now(datetime.timezone.utc)
                            - event["object"].last_timestamp
                        )

                        if time_since_last_timestamp.seconds > 5:
                            logger.info(
                                "Skipping because event old (%d > 5 seconds).",
                                time_since_last_timestamp.seconds,
                            )
                        else:
                            logger.info("Removing Docker-in-Docker socket and pods ...")
                            try:
                                node_IP_address = get_node_running_pod(pod_name)
                                remove_docker_socket(node_IP_address)
                                remove_pods()
                            except Exception as exception:
                                logger.info(
                                    "Fail to delete pod %s due %s", pod_name, exception
                                )

                elif event["object"].type == "Normal":
                    logger.debug(
                        "Found Normal event in %s ... skipping!",
                        event["object"].metadata.name,
                    )
                else:
                    logger.debug(
                        "Found %s event in %s ... ignoring!",
                        event["object"].type,
                        ["object"].metadata.name,
                    )

        logger.info("Stop monitoring!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Open Research Computing v2 Fix JupyterHub Bot",
        description="Monitoring Kubernetes cluster to restart JupyterHub",
    )
    parser.add_argument(
        "-c",
        "--kube-config",
        type=str,
        default="~/.kube/config",
        help="Location of Kubernetes configuration file",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Display log information"
    )
    parser.add_argument(
        "-vv", "--debug", action="store_true", help="Display debug information"
    )
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    config.load_kube_config(config_file=args.kube_config)

    v1 = client.CoreV1Api()

    monitor_cluster()
