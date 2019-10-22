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
ABSOLUTE_HERE = os.path.dirname(os.path.realpath(__file__))

def setup_auth_turing():
    """
    Set up athentication with Turing k8s cluster on Azure.
    """
    # Read in auth info
    azure_file = os.path.join(ABSOLUTE_HERE, "secrets", "turing-auth-key-prod.json")
    with open(azure_file, "r") as stream:
        azure = json.load(stream)

    # Login in to Azure
    login_cmd = [
        "az", "login", "--service-principal",
        "--username", azure["sp-app-id"],
        "--password", azure["sp-app-key"],
        "--tenant", azure["tenant-id"]
    ]
    subprocess.check_output(login_cmd)

    # Set kubeconfig
    creds_cmd = [
        "az", "aks", "get-credentials",
        "--name", "prod",
        "--resource-group", "binder-prod"

    ]
    stdout = subprocess.check_output(creds_cmd)
    print(stdout.decode('utf-8'))


def setup_auth_ovh(release, cluster):
    """
    Set up authentication with 'binder-ovh' K8S from the ovh-kubeconfig.yml
    """
    print(f'Setup the OVH authentication for namespace {release}')

    ovh_kubeconfig = os.path.join(ABSOLUTE_HERE, 'secrets', 'ovh-kubeconfig.yml')
    os.environ['KUBECONFIG'] = ovh_kubeconfig
    print(f'Current KUBECONFIG=\'{ovh_kubeconfig}\'')
    stdout = subprocess.check_output([
        'kubectl',
        'config',
        'use-context',
        cluster
    ])
    print(stdout.decode('utf8'))


def setup_ovh_ingress_link(release):
    """
    Setup the Ingress link ovh.mybinder.org -> binder.mybinder.ovh
    """
    ovh_ingress_path = os.path.join(ABSOLUTE_HERE, 'config', 'ovh', 'ovh_mybinder_org_ingress.yaml')
    stdout = subprocess.check_output([
        'kubectl',
        'apply',
        '-f',
        ovh_ingress_path,
        '-n',
        release
    ])
    print(stdout.decode('utf8'))


def setup_auth_gcloud(release, cluster):
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
        choices=['staging', 'prod', 'ovh', 'turing']
    )
    argparser.add_argument(
        'cluster',
        help='Cluster to do the deployment in'
    )

    args = argparser.parse_args()

    if args.cluster == 'binder-ovh':
        setup_auth_ovh(args.release, args.cluster)
    elif args.cluster == 'turing':
        setup_auth_turing()
    else:
        setup_auth_gcloud(args.release, args.cluster)

    setup_helm(args.release)
    deploy(args.release)


if __name__ == '__main__':
    main()
