"""Kill succeeded pods in Kubernetes cluster"""

import argparse
import logging

from kubernetes import client, config

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("kill-succeeded-pods")
logger.setLevel(logging.WARNING)

NAMESPACE = "gesis"


def get_succeeded_pods():
    """Get list of all succeeded pods that are single user running pod"""
    all_succeeded_pods = []

    api_response = v1.list_namespaced_pod(NAMESPACE)
    for pod in api_response.items:
        logger.debug("Pod %s is %s", pod.metadata.name, pod.status.phase)
        if pod.status.phase == "Succeeded" and pod.metadata.name.startswith("jupyter-"):
            all_succeeded_pods.append(pod)

    return all_succeeded_pods


def kill_pod(pod):
    """Kill single pod"""
    logger.info("Requesting delete of pod %s ...", pod.metadata.name)
    try:
        api_response = v1.delete_namespaced_pod(pod.metadata.name, NAMESPACE)
        logger.info("Pod %s deleted.", api_response.metadata.name)
    except client.exceptions.ApiException as exception:
        logger.info("Fail to delete pod %s due %s", pod.metadata.name, exception)


def kill_succeeded_pods():
    """Kill succeeded pods"""
    logger.info("Starting inspection of Kubernetes pod ...")
    all_succeeded_pods = get_succeeded_pods()
    for succeeded_pod in all_succeeded_pods:
        kill_pod(succeeded_pod)
    logger.info("%s pods deleted.", len(all_succeeded_pods))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Open Research Computing v2 Kill Succeeded Pods Cron Job",
        description="Cron job to kill Kubernetes pods in Succeeded status that are very old",
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

    kill_succeeded_pods()
