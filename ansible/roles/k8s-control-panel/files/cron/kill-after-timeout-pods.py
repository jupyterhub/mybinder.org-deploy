"""Kill pods in Kubernetes cluster after timeout"""

import argparse
import datetime
import logging

from kubernetes import client, config

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("kill-after-timeout-pods")
logger.setLevel(logging.WARNING)

NAMESPACE = "gesis"
BINDER_TIME_OUT = 6  # hours


def get_timed_out_pods():
    """Get list of all timed out pods that are single user running pod"""
    time_now = datetime.datetime.now(datetime.timezone.utc)
    all_timed_out_pods = []

    api_response = v1.list_namespaced_pod(NAMESPACE)
    for pod in api_response.items:
        pod_run_time = time_now - pod.metadata.creation_timestamp
        pod_run_time_in_hours = pod_run_time.total_seconds() / 3600
        logger.debug(
            "Pod %s (%s) is running for %.1f hours.",
            pod.metadata.name,
            pod.status.phase,
            pod_run_time_in_hours,
        )
        if (
            pod.metadata.name.startswith("jupyter-")
            and pod_run_time_in_hours > BINDER_TIME_OUT
        ):
            all_timed_out_pods.append(pod)
            logger.debug("Pod %s added to the list.", pod.metadata.name)

    return all_timed_out_pods


def kill_pod(pod):
    """Kill single pod"""
    logger.info("Requesting delete of pod %s ...", pod.metadata.name)
    try:
        api_response = v1.delete_namespaced_pod(pod.metadata.name, NAMESPACE)
        logger.info("Pod %s deleted.", api_response.metadata.name)
    except client.exceptions.ApiException as exception:
        logger.info("Fail to delete pod %s due %s", pod.metadata.name, exception)


def kill_timed_out_pods():
    """Kill timed out pods"""
    logger.info("Starting inspection of Kubernetes pod ...")
    all_timed_out_pods = get_timed_out_pods()
    for timed_out_pod in all_timed_out_pods:
        kill_pod(timed_out_pod)
    logger.info("%s pods deleted.", len(all_timed_out_pods))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Open Research Computing v2 Kill Timed Out Pods Cron Job",
        description="Cron job to kill Kubernetes pods that timed out",
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

    kill_timed_out_pods()
