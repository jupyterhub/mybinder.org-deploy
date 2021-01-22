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

GCP_PROJECTS = {
    "staging": "binderhub-288415",
    "prod": "binderhub-288415",
}

GCP_ZONES = {
    "staging": "us-central1-a",
    "prod": "us-central1",
}


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


def setup_auth_gcloud(release, cluster=None):
    """
    Set up GCloud + Kubectl authentication for talking to a given cluster
    """
    # Authenticate to GoogleCloud using a service account
    subprocess.check_output([
        "gcloud", "auth", "activate-service-account",
        f"--key-file=secrets/gke-auth-key-{release}.json"
    ])

    if not cluster:
        cluster = release

    project = GCP_PROJECTS[release]
    zone = GCP_ZONES[release]

    # Use gcloud to populate ~/.kube/config, which kubectl / helm can use
    subprocess.check_call(
        [
            "gcloud",
            "container",
            "clusters",
            "get-credentials",
            cluster,
            f"--zone={zone}",
            f"--project={project}",
        ]
    )


def assert_helm_v3():
    """Asserts helm is available at all and of the required major version."""
    c = subprocess.run(["helm", "--help"], capture_output=True)
    assert c.returncode == 0, "Helm 3 is required, but helm doesn't seem to be installed!"

    c = subprocess.run(
        ["helm", "version", "--short"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert c.returncode == 0 and "v3." in c.stdout, "Helm 3 is required, but a different version seem to be installed!"


def deploy(release, name=None):
    """Deploys a federation member to a k8s cluster.

    The deployment is done in the following steps:

        1. Run secrets/ban.py to update network bans
        2. Deploy cert-manager
        3. Deploy mybinder helm chart
        4. Await deployed deployment and daemonsets to become Ready
    """
    print(BOLD + GREEN + f"Updating network-bans for {release}" + NC, flush=True)
    if not name:
        name = release
    if release == "turing" or release == "ovh":
        subprocess.check_call(
            ["python3", "secrets/ban.py", release,]
        )
    else:
        subprocess.check_call([
            "python3",
            "secrets/ban.py",
        ])

    setup_certmanager()

    print(BOLD + GREEN + f"Starting helm upgrade for {release}" + NC, flush=True)
    helm = [
        "helm",
        "upgrade",
        "--install",
        "--namespace",
        name,
        name,
        "mybinder",
        "--cleanup-on-fail",
        "--create-namespace",
        "-f",
        os.path.join("config", release + ".yaml"),
        "-f",
        os.path.join("secrets", "config", "common.yaml"),
        "-f",
        os.path.join("secrets", "config", release + ".yaml"),
    ]

    subprocess.check_call(helm)
    print(BOLD + GREEN + f"SUCCESS: Helm upgrade for {release} completed" + NC, flush=True)

    # Explicitly wait for all deployments and daemonsets to be fully rolled out
    print(
        BOLD
        + GREEN
        + f"Waiting for all deployments and daemonsets in {name} to be ready"
        + NC,
        flush=True,
    )
    deployments_and_daemonsets = (
        subprocess.check_output(
            [
                "kubectl",
                "--namespace",
                name,
                "get",
                "deployments,daemonsets",
                "-o",
                "name",
            ]
        )
        .decode()
        .strip()
        .split("\n")
    )

    for d in deployments_and_daemonsets:
        subprocess.check_call(
            [
                "kubectl",
                "rollout",
                "status",
                "--namespace",
                name,
                "--timeout",
                "10m",
                "--watch",
                d,
            ]
        )


def setup_certmanager():
    """Install cert-manager separately

    cert-manager docs and CRD assumptions say that cert-manager must never be a sub-chart,
    always installed on its own in a cert-manager namespace
    """

    # TODO: cert-manager chart >= 0.15
    # has `installCRDs` option, which should eliminate the separate CRD step
    # however, upgrade notes say this *must not* be used
    # when upgrading, only for fresh deployments,
    # and requires helm >=3.3.1 and kubernetes >=1.16.14

    version = os.environ["CERT_MANAGER_VERSION"]

    manifest_url = f"https://github.com/jetstack/cert-manager/releases/download/{version}/cert-manager.crds.yaml"
    print(BOLD + GREEN + f"Installing cert-manager CRDs {version}" + NC, flush=True)

    subprocess.check_call(
        ["kubectl", "apply", "-f", manifest_url]
    )

    print(BOLD + GREEN + f"Installing cert-manager {version}" + NC, flush=True)
    subprocess.check_call(
        ["helm", "repo", "add", "jetstack", "https://charts.jetstack.io"]
    )

    subprocess.check_call(
        ["helm", "repo", "update"]
    )

    helm_upgrade = [
        "helm",
        "upgrade",
        "--install",
        "--create-namespace",
        "--namespace",
        "cert-manager",
        "cert-manager",
        "jetstack/cert-manager",
        "--version",
        version,
        "-f",
        "config/cert-manager.yaml",
    ]

    subprocess.check_call(helm_upgrade)


def main():
    # parse command line args
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "release",
        help="Release to deploy",
        choices=["staging", "prod", "ovh", "turing"],
    )
    argparser.add_argument(
        "--name", help="Override helm release name, if different from RELEASE",
    )
    argparser.add_argument(
        "cluster", help="Cluster to do the deployment in", nargs="?", type=str,
    )
    argparser.add_argument(
        '--local',
        action='store_true',
        help="If the script is running locally, skip auth step"
    )

    args = argparser.parse_args()

    assert_helm_v3()

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
            setup_auth_turing(args.release)
        else:
            setup_auth_gcloud(args.release, args.cluster)

    deploy(args.release, args.name)


if __name__ == '__main__':
    main()
