#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import re
import sys

import yaml

# Color codes for colored output!
if os.environ.get("TERM"):
    BOLD = subprocess.check_output(['tput', 'bold']).decode()
    GREEN = subprocess.check_output(['tput', 'setaf', '2']).decode()
    NC = subprocess.check_output(['tput', 'sgr0']).decode()
else:
    # no term, no colors
    BOLD = GREEN = NC = ""

HERE = os.path.dirname(__file__)
ABSOLUTE_HERE = os.path.dirname(os.path.realpath(__file__))

# Get helm version environment variable
HELM_VERSION = os.getenv("HELM_VERSION", None)
if HELM_VERSION is None:
    raise Exception("HELM_VERSION environment variable must be set")

def setup_auth_turing(cluster):
    """
    Set up authentication with Turing k8s cluster on Azure.
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
        "--name", cluster,
        "--resource-group", "binder-prod"

    ]
    stdout = subprocess.check_output(creds_cmd)
    print(stdout.decode('utf-8'))


def setup_auth_ovh(release, cluster):
    """
    Set up authentication with 'ovh' K8S from the ovh-kubeconfig.yml
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
    # First check the helm client and server versions
    client_helm_cmd = ["helm", "version", "-c", "--short"]
    client_version = subprocess.check_output(client_helm_cmd
        ).decode('utf-8').split(":")[1].split("+")[0].strip()

    server_helm_cmd = ["helm", "version", "-s", "--short"]
    server_version = subprocess.check_output(server_helm_cmd
        ).decode('utf-8').split(":")[1].split("+")[0].strip()

    print(BOLD + GREEN +
        f"Client version: {client_version}, Server version: {server_version}" +
        NC,
        flush=True
    )

    # Now check if the version of helm matches that which CI is expecting
    if client_version != HELM_VERSION:
        # The local helm version is not what was expected - user needs to change the installation
        raise Exception(
            f"You are not running helm {HELM_VERSION} which is the version our continuous deployment system uses.\n" +
            "Please change your installation and try again.\n"
        )
    elif (client_version == HELM_VERSION) and (client_version != server_version):
        # The correct local version of helm is installed, but the server side
        # has previously accidentally been upgraded. Perform a force-upgrade
        # to bring the server side back to matching version
        print(f"Upgrading helm from {server_version} to {HELM_VERSION}")
        subprocess.check_call(['helm', 'init', '--upgrade', '--force-upgrade'])
    elif (client_version == HELM_VERSION) and (client_version == server_version):
        # All is good! Perform normal helm init command.
        # We use the --client-only flag so that the Tiller installation is not affected.
        subprocess.check_call(['helm', 'init', '--client-only'])
    else:
        # This is a catch-all exception. Hopefully this doesn't execute!
        raise Exception("Please check your helm installation.")

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
    if release == 'turing' or release == 'ovh':
        subprocess.check_call([
            "python3",
            "secrets/ban.py",
            release,
        ])
    else:
        subprocess.check_call([
            "python3",
            "secrets/ban.py",
        ])

    setup_certmanager()

    print(BOLD + GREEN + f"Starting helm upgrade for {release}" + NC, flush=True)
    helm = [
        'helm', 'upgrade', '--install',
        '--namespace', release,
        release,
        'mybinder',
        '--force',
        '--cleanup-on-fail',
        '-f', os.path.join('config', release + '.yaml'),
        '-f', os.path.join('secrets', 'config', 'common.yaml'),
        '-f', os.path.join('secrets', 'config', release + '.yaml'),
    ]

    subprocess.check_call(helm)
    print(BOLD + GREEN + f"SUCCESS: Helm upgrade for {release} completed" + NC, flush=True)

    # Explicitly wait for all deployments and daemonsets to be fully rolled out
    print(BOLD + GREEN + f"Waiting for all deployments and daemonsets in {release} to be ready" + NC, flush=True)
    deployments_and_daemonsets = subprocess.check_output([
        'kubectl',
        '--namespace', release,
        'get', 'deployments,daemonsets',
        '-o', 'name'
    ]).decode().strip().split('\n')

    for d in deployments_and_daemonsets:
        subprocess.check_call([
            'kubectl', 'rollout', 'status',
            '--namespace', release,
            '--timeout', '5m',
            '--watch', d
        ])


def setup_certmanager():
    """Install cert-manager CRDs"""

    # TODO: cert-manager chart >= 0.15
    # has `installCRDs` option, which should elimnate this step
    # however, upgrade notes say this *must not* be used
    # when upgrading, only for fresh deployments,
    # and requires helm >=3.3.1 and kubernetes >=1.16.14

    requirements_yaml = os.path.join(ABSOLUTE_HERE, "mybinder", "requirements.yaml")
    with open(requirements_yaml, "r") as f:
        requirements = yaml.safe_load(f)

    for dep in requirements["dependencies"]:
        if dep["name"] == "cert-manager":
            cert_manager = dep
            break
    else:
        raise ValueError(f"cert-manager dependency not found in {requirements_yaml}")
    version = cert_manager["version"]
    manifest_url = f"https://github.com/jetstack/cert-manager/releases/download/{version}/cert-manager.yaml"
    print(BOLD + GREEN + f"Applying cert-manager {version} CRDs" + NC, flush=True)

    subprocess.check_call([
        'kubectl',
        'apply',
        '--validate=false',
        '-f',
        manifest_url,
    ])


def main():
    # parse command line args
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
    argparser.add_argument(
        '--local',
        action='store_true',
        help="If the script is running locally, skip auth and helm steps."
    )

    args = argparser.parse_args()

    # Check if the local flag is set
    if not args.local:
        # Check if the script is being run on CI
        if not os.environ.get("CI"):
            # Catch the case where the script is running locally but the --local flag
            # has not been set. Check that the user is sure that they want to do this!
            print(
                "You do not seem to be running on CI but have not set the --local flag."
            )

            # Use regex to match user input
            regex_no = re.compile("^[n|N][o|O]$")
            regex_yes = re.compile("^[y|Y][e|E][s|S]$")
            response = input("Are you sure you want to execute this script? [yes/no]: ")

            if regex_no.match(response):
                # User isn't sure - exit script
                print("Exiting script.")
                sys.exit()
            elif regex_yes.match(response):
                # User is sure - proceed
                pass
            else:
                # User wrote something that wasn't "yes" or "no"
                raise ValueError(
                    "Unrecognised input. Expecting either yes or no."
                )

        # script is running on CI, proceed with auth and helm setup
        if args.cluster == 'ovh':
            setup_auth_ovh(args.release, args.cluster)
        elif args.cluster == 'turing':
            setup_auth_turing(args.cluster)
        else:
            setup_auth_gcloud(args.release, args.cluster)
        setup_helm(args.release)

    deploy(args.release)


if __name__ == '__main__':
    main()
