#!/usr/bin/env python3
import argparse
import subprocess
import yaml
import os

# Color codes for colored output!
BOLD = subprocess.check_output(['tput', 'bold']).decode()
GREEN = subprocess.check_output(['tput', 'setaf', '2']).decode()
NC = subprocess.check_output(['tput', 'sgr0']).decode()

def setup_auth(release, cluster):
    """
    Set up GCloud + Kubectl authentication for talking to a given cluster
    """
    # Authenticate to GoogleCloud using a service account
    subprocess.check_output([
        "gcloud", "auth", "activate-service-account",
        f"--key-file=secrets/gke-auth-key-{release}.json"
    ])

    # Use gcloud to populate ~/.kube/config, which kubectl / helm can use
    subprocess.check_call([
        "gcloud", "container", "clusters", "get-credentials",
        cluster, "--zone=us-central1-a", f"--project=binder-{release}""
    ])


def deploy(release):
    print(BOLD + GREEN + f"Starting helm upgrade for {release}" + NC, flush=True)
    helm = [
        'helm', 'upgrade', '--install',
        '--namespace', release,
        release,
        'mybinder',
        '--wait',
        '--timeout', '600',
        '-f', os.path.join('config', release + '.yaml'),
        '-f', os.path.join('secrets', 'config', release + '.yaml')
    ]

    subprocess.check_call(helm)
    print(BOLD + GREEN + f"SUCCESS: Helm upgrade for {release} completed" + NC, flush=True)

    # Explicitly wait for all deployments and daemonsets to be fully rolled out
    print(BOLD + GREEN + f"Waiting for all deployments and daemonsets in {release} to be ready" + NC, flush=True)
    deployments = subprocess.check_output([
        'kubectl',
        '--namespace', release,
        'get', 'deployments',
        '-o', 'name'
    ]).decode().strip().split('\n')

    daemonsets = subprocess.check_output([
        'kubectl',
        '--namespace', release,
        'get', 'daemonsets',
        '-o', 'name'
    ]).decode().strip().split('\n')

    for d in deployments + daemonsets:
        subprocess.check_call([
            'kubectl', 'rollout', 'status',
            '--namespace', release,
            '--watch', d
        ])


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'release',
        help="Release to deploy",
        choices=['staging', 'prod']
    )
    argparser.add_argument(
        'cluster',
        help='Cluster to do the deployment in'
    )

    args = argparser.parse_args()

    setup_auth(args.release, args.cluster)
    deploy(args.release)

main()
