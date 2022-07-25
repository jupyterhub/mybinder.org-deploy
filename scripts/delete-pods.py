#!/usr/bin/env python3
"""
Delete all user pods older than a given duration.

We use the Kubernetes cluster autoscaler, which
removes nodes from the kubernetes cluster when they have
been 'empty' for more than 10 minutes However, we
have issues where some pods get 'stuck' and never actually
die, sometimes forever. This causes nodes to not be
killed automatically.

This script makes it easier to find and delete pods that match a certain
name or age. By default, it only *finds* and lists these pods. If the `--delete` flag
is given, it will also *delete* those pods.

You need the `kubernetes` python library installed for this to work.
"""
import argparse
from datetime import datetime, timedelta, timezone

from kubernetes import client, config

# Setup our parameters
argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--older-than",
    type=float,
    default=0,
    help="Pods older than this many hours will be killed (can be fractions of an hour)",
)
argparser.add_argument(
    "--delete",
    action="store_true",
    help="Confirm deleting the pods rather than just printing info",
)
argparser.add_argument(
    "--namespace", default="prod", help="Namespace to perform actions in"
)
argparser.add_argument(
    "--pod-name", default="", help="Only delete pods with `pod-name` in the pod name."
)

kube_context_help = (
    "Context pointing to the cluster to use. To list the "
    "current activated context, run `kubectl config get-contexts`"
)
argparser.add_argument(
    "--kube-context",
    default="gke_binder-prod_us-central1-a_prod-a",
    help=kube_context_help,
)
args = argparser.parse_args()

if args.older_than == 0 and args.pod_name == "":
    raise ValueError("Must specify at least one of `pod-name` or `pod-age`.")

# Load and operate on current kubernetes config
config.load_kube_config(context=args.kube_context)

# Get list of pods with given label selector in the 'prod' namespace
core_api = client.CoreV1Api()

pods = core_api.list_namespaced_pod(
    args.namespace, label_selector="component=singleuser-server"
)
total_pods = []
for pod in pods.items:
    # API results always use UTC timezone
    age = datetime.now(timezone.utc) - pod.status.start_time.replace(
        tzinfo=timezone.utc
    )
    if age > timedelta(hours=args.older_than):
        # If pod-name isn't specified, this will always be true
        if args.pod_name not in pod.metadata.name:
            continue
        if args.delete:
            core_api.delete_namespaced_pod(
                pod.metadata.name, args.namespace, client.V1DeleteOptions()
            )
            print(
                f"Deleted {age.total_seconds() / 60 / 60:.1f}h old pod {pod.metadata.name}"
            )
            summary_text = "Deleted {} pods"
        else:
            print(
                f"Found {age.total_seconds() / 60 / 60:.1f}h old pod {pod.metadata.name}"
            )
            summary_text = "Found {} pods"

        total_pods.append(pod.metadata.name)

print("---", "\n", summary_text.format(len(total_pods)))
