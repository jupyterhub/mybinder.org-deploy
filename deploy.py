#!/usr/bin/env python3
import argparse
import json
import os
import subprocess

import yaml

# Color codes for colored output!
BOLD = subprocess.check_output(['tput', 'bold']).decode()
GREEN = subprocess.check_output(['tput', 'setaf', '2']).decode()
NC = subprocess.check_output(['tput', 'sgr0']).decode()
HERE = os.path.dirname(__file__)


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
        cluster, "--zone=us-central1-a", f"--project=binder-{release}"
    ])


def setup_helm(release):
    """ensure helm is up to date"""
    subprocess.check_call(['helm', 'init', '--upgrade'])

    deployment = json.loads(subprocess.check_output([
        'kubectl',
        '--namespace=kube-system',
        'get',
        'deployment',
        'tiller-deploy',
        '-o', 'json',
    ]).decode('utf8'))
    # patch tiller nodeSelector
    # helm init can set this with `--node-selectors`,
    # but it cannot be applied after upgrade
    # https://github.com/helm/helm/issues/4063
    with open(os.path.join(HERE, 'config', release + '.yaml')) as f:
        config = yaml.safe_load(f)
    node_selector = config.get('coreNodeSelector', None)
    current_node_selector = deployment['spec']['template']['spec'].get('nodeSelector')

    if current_node_selector != node_selector:
        patch = {'path': '/spec/template/spec/nodeSelector'}
        if not node_selector:
            patch['op'] = 'remove'
        if not current_node_selector:
            patch['op'] = 'add'
            patch['value'] = node_selector
        else:
            patch['op'] = 'replace'
            patch['value'] = node_selector
        subprocess.check_call([
            'kubectl',
            'patch',
            '--namespace',
            'kube-system',
            'deployment',
            'tiller-deploy',
            '--type=json',
            '-p',
            json.dumps([patch]),
        ])

    # wait for tiller to come up
    subprocess.check_call([
        'kubectl', 'rollout', 'status',
        '--namespace', 'kube-system',
        '--watch', 'deployment', 'tiller-deploy',
    ])


def deploy(release):
    """Deploy jupyterhub"""
    print(BOLD + GREEN + f"Updating network-bans for {release}" + NC, flush=True)
    subprocess.check_call([
        "python3",
        "secrets/ban.py",
    ])

    print(BOLD + GREEN + f"Starting helm upgrade for {release}" + NC, flush=True)
    helm = [
        'helm', 'upgrade', '--install',
        '--namespace', release,
        release,
        'mybinder',
        '--force',
        '--wait',
        '--timeout', '600',
        '-f', os.path.join('config', release + '.yaml'),
        '-f', os.path.join('secrets', 'config', 'common.yaml'),
        '-f', os.path.join('secrets', 'config', release + '.yaml'),
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
    setup_helm(args.release)
    deploy(args.release)


if __name__ == '__main__':
    main()
