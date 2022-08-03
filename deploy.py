#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
import subprocess
import sys

# Color codes for colored output!
if os.environ.get("TERM"):
    BOLD = subprocess.check_output(["tput", "bold"]).decode()
    GREEN = subprocess.check_output(["tput", "setaf", "2"]).decode()
    NC = subprocess.check_output(["tput", "sgr0"]).decode()
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

# Mapping of cluster names (keys) to resource group names (values) for Azure deployments
AZURE_RGs = {"turing-prod": "binder-prod", "turing-staging": "binder-staging"}


def setup_auth_turing(cluster):
    """
    Set up authentication with Turing k8s cluster on Azure.
    """
    # Read in auth info
    azure_file = os.path.join(ABSOLUTE_HERE, "secrets", "turing-auth-key-prod.json")
    with open(azure_file) as stream:
        azure = json.load(stream)

    # Login in to Azure
    login_cmd = [
        "az",
        "login",
        "--service-principal",
        "--username",
        azure["sp-app-id"],
        "--password",
        azure["sp-app-key"],
        "--tenant",
        azure["tenant-id"],
    ]
    subprocess.check_output(login_cmd)

    # Set kubeconfig
    creds_cmd = [
        "az",
        "aks",
        "get-credentials",
        "--name",
        cluster,
        "--resource-group",
        AZURE_RGs[cluster],
    ]
    stdout = subprocess.check_output(creds_cmd)
    print(stdout.decode("utf-8"))


def setup_auth_ovh(release, cluster):
    """
    Set up authentication with 'ovh' K8S from the ovh-kubeconfig.yml
    """
    print(f"Setup the OVH authentication for namespace {release}")

    ovh_kubeconfig = os.path.join(ABSOLUTE_HERE, "secrets", "ovh-kubeconfig.yml")
    os.environ["KUBECONFIG"] = ovh_kubeconfig
    print(f"Current KUBECONFIG='{ovh_kubeconfig}'")
    stdout = subprocess.check_output(["kubectl", "config", "use-context", cluster])
    print(stdout.decode("utf8"))


def setup_auth_gcloud(release, cluster=None):
    """
    Set up GCloud + Kubectl authentication for talking to a given cluster
    """
    # Authenticate to GoogleCloud using a service account
    subprocess.check_output(
        [
            "gcloud",
            "auth",
            "activate-service-account",
            f"--key-file=secrets/gke-auth-key-{release}.json",
        ]
    )

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


def deploy(release, name=None):
    """Deploys a federation member to a k8s cluster.

    The deployment is done in the following steps:

        1. Run secrets/ban.py to update network bans
        2. Deploy cert-manager
        3. Deploy mybinder helm chart
        4. Await deployed deployment and daemonsets to become Ready
    """
    if not name:
        name = release

    print(BOLD + GREEN + f"Updating network-bans for {release}" + NC, flush=True)

    # some members have special logic in ban.py,
    # in which case they must be specified on the command-line
    ban_command = [sys.executable, "secrets/ban.py"]
    if release in {"turing-prod", "turing-staging", "turing", "ovh"}:
        ban_command.append(release)

    subprocess.check_call(ban_command)

    setup_certmanager()

    print(BOLD + GREEN + f"Starting helm upgrade for {release}" + NC, flush=True)
    helm = [
        "helm",
        "upgrade",
        "--install",
        "--cleanup-on-fail",
        "--create-namespace",
        f"--namespace={name}",
        name,
        "mybinder",
    ]

    # common config files
    config_files = sorted(glob.glob(os.path.join("config", "common", "*.yaml")))
    config_files.extend(
        sorted(glob.glob(os.path.join("secrets", "config", "common", "*.yaml")))
    )
    # release-specific config files
    for config_dir in ("config", "secrets/config"):
        config_files.append(os.path.join(config_dir, release + ".yaml"))
    # add config files to helm command
    for config_file in config_files:
        helm.extend(["-f", config_file])

    subprocess.check_call(helm)
    print(
        BOLD + GREEN + f"SUCCESS: Helm upgrade for {release} completed" + NC, flush=True
    )

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
                "get",
                f"--namespace={name}",
                "--output=name",
                "deployments,daemonsets",
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
                f"--namespace={name}",
                "--timeout=10m",
                "--watch",
                d,
            ]
        )


def setup_certmanager():
    """
    Install cert-manager separately into its own namespace and `kubectl apply`
    its CRDs each time as helm won't attempt to handle changes to CRD resources.

    To `kubectl apply` the CRDs manually before `helm upgrade` is the typical
    procedure recommended by cert-manager. Sometimes cert-manager provides
    additional upgrade notes, see https://cert-manager.io/docs/release-notes/
    before you upgrade to a new version.
    """
    version = os.environ["CERT_MANAGER_VERSION"]

    manifest_url = f"https://github.com/jetstack/cert-manager/releases/download/{version}/cert-manager.crds.yaml"
    print(BOLD + GREEN + f"Installing cert-manager CRDs {version}" + NC, flush=True)

    # Sometimes 'replace' is needed for upgrade (e.g. 1.1->1.2)
    subprocess.check_call(["kubectl", "apply", "-f", manifest_url])

    print(BOLD + GREEN + f"Installing cert-manager {version}" + NC, flush=True)
    helm_upgrade = [
        "helm",
        "upgrade",
        "--install",
        "--create-namespace",
        "--namespace=cert-manager",
        "--repo=https://charts.jetstack.io",
        "cert-manager",
        "cert-manager",
        f"--version={version}",
        "--values=config/cert-manager.yaml",
    ]

    subprocess.check_call(helm_upgrade)


def main():
    # parse command line args
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "release",
        help="Release to deploy",
        choices=["staging", "prod", "ovh", "turing-prod", "turing-staging", "turing"],
    )
    argparser.add_argument(
        "--name",
        help="Override helm release name, if different from RELEASE",
    )
    argparser.add_argument(
        "cluster",
        help="Cluster to do the deployment in",
        nargs="?",
        type=str,
    )
    argparser.add_argument(
        "--local",
        action="store_true",
        help="If the script is running locally, skip auth step",
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
                raise ValueError("Unrecognised input. Expecting either yes or no.")

        # script is running on CI, proceed with auth and helm setup
        cluster = args.cluster or args.release

        if cluster == "ovh":
            setup_auth_ovh(args.release, cluster)
        elif cluster in AZURE_RGs:
            setup_auth_turing(cluster)
        elif cluster in GCP_PROJECTS:
            setup_auth_gcloud(args.release, cluster)
        else:
            raise Exception("Cloud cluster not recognised!")

    deploy(args.release, args.name)


if __name__ == "__main__":
    main()
