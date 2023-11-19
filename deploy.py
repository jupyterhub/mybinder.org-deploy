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

# Mapping of config name to cluster name for AWS EKS deployments
AWS_DEPLOYMENTS = {"curvenote": "binderhub"}

# Mapping of cluster names (keys) to resource group names (values) for Azure deployments
AZURE_RGs = {}


def check_call(cmd, dry_run):
    """
    Print a command if dry_run is true, otherwise run it with subprocess.check_call
    """
    if dry_run:
        print("dry-run:", " ".join(cmd))
    else:
        subprocess.check_call(cmd)


def check_output(cmd, dry_run):
    """
    Print a command if dry_run is true, otherwise run it with subprocess.check_output
    and return decoded output
    """
    if dry_run:
        print("dry-run:", " ".join(cmd))
        return ""
    else:
        out = subprocess.check_output(cmd)
        return out.decode("utf-8")


def setup_auth_azure(cluster, dry_run=False):
    """
    Set up authentication with a k8s cluster on Azure.
    """
    # Read in auth info. Note that we assume a file name convention of
    # secrets/{CLUSTER_NAME}-auth-key-prod.json
    azure_file = os.path.join(ABSOLUTE_HERE, "secrets", f"{cluster}-auth-key-prod.json")
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
    check_output(login_cmd, dry_run)

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
    stdout = check_output(creds_cmd, dry_run)
    print(stdout)


def setup_auth_ovh(release, cluster, dry_run=False):
    """
    Set up authentication with 'ovh' K8S from the ovh-kubeconfig.yml
    """
    print(f"Setup the OVH authentication for namespace {release}")

    ovh_kubeconfig = os.path.join(ABSOLUTE_HERE, "secrets", f"{release}-kubeconfig.yml")
    os.environ["KUBECONFIG"] = ovh_kubeconfig
    print(f"Current KUBECONFIG='{ovh_kubeconfig}'")
    stdout = check_output(["kubectl", "config", "use-context", cluster], dry_run)
    print(stdout)


def setup_auth_gcloud(release, cluster=None, dry_run=False):
    """
    Set up GCloud + Kubectl authentication for talking to a given cluster
    """
    # Authenticate to GoogleCloud using a service account
    check_output(
        [
            "gcloud",
            "auth",
            "activate-service-account",
            f"--key-file=secrets/gke-auth-key-{release}.json",
        ],
        dry_run,
    )

    project = GCP_PROJECTS[release]
    zone = GCP_ZONES[release]

    # Use gcloud to populate ~/.kube/config, which kubectl / helm can use
    check_call(
        [
            "gcloud",
            "container",
            "clusters",
            "get-credentials",
            cluster,
            f"--zone={zone}",
            f"--project={project}",
        ],
        dry_run,
    )


def setup_auth_aws(cluster, dry_run=False):
    """
    Set up authentication for EKS on AWS

    Assumes you already have an AWS CLI profile setup with access to EKS,
    and that either this is the default profile (e.g. on CI) or you have set the
    AWS_PROFILE environment variable.
    """
    print(BOLD + GREEN + f"Obtaining AWS EKS kubeconfig for {cluster}" + NC, flush=True)

    eks_kubeconfig = [
        "aws",
        "eks",
        "update-kubeconfig",
        "--name",
        AWS_DEPLOYMENTS[cluster],
    ]
    stdout = check_output(eks_kubeconfig, dry_run)
    print(stdout)


def update_networkbans(cluster, dry_run=False):
    """
    Run secrets/ban.py to update network bans
    """

    print(BOLD + GREEN + f"Updating network-bans for {cluster}" + NC, flush=True)

    # some members have special logic in ban.py,
    # in which case they must be specified on the command-line
    ban_command = [sys.executable, "secrets/ban.py"]
    if cluster in {"ovh", "ovh2"}:
        ban_command.append(cluster)

    check_call(ban_command, dry_run)


def get_config_files(release, config_dir="config"):
    """Return the list of config files to load"""
    # common config files
    config_files = sorted(glob.glob(os.path.join(config_dir, "common", "*.yaml")))
    config_files.extend(
        sorted(glob.glob(os.path.join("secrets", config_dir, "common", "*.yaml")))
    )
    # release-specific config files
    for config_dir in (config_dir, os.path.join("secrets", config_dir)):
        f = os.path.join(config_dir, release + ".yaml")
        if os.path.exists(f):
            config_files.append(f)
    return config_files


def deploy(release, name=None, dry_run=False):
    """Deploys a federation member to a k8s cluster.

    Waits for deployments and daemonsets to become Ready
    """
    if not name:
        name = release

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

    config_files = get_config_files(release)
    # add config files to helm command
    for config_file in config_files:
        helm.extend(["-f", config_file])

    check_call(helm, dry_run)
    print(
        BOLD + GREEN + f"SUCCESS: Helm upgrade for {release} completed" + NC, flush=True
    )

    wait_for_deployments_daemonsets(name, dry_run)


def wait_for_deployments_daemonsets(name, dry_run=False):
    """
    Wait for all deployments and daemonsets to be fully rolled out
    """
    print(
        BOLD
        + GREEN
        + f"Waiting for all deployments and daemonsets in {name} to be ready"
        + NC,
        flush=True,
    )
    deployments_and_daemonsets = (
        check_output(
            [
                "kubectl",
                "get",
                f"--namespace={name}",
                "--output=name",
                "deployments,daemonsets",
            ],
            dry_run,
        )
        .strip()
        .split("\n")
    )

    for d in deployments_and_daemonsets:
        check_call(
            [
                "kubectl",
                "rollout",
                "status",
                f"--namespace={name}",
                "--timeout=10m",
                "--watch",
                d,
            ],
            dry_run,
        )


def setup_certmanager(dry_run=False):
    """
    Install cert-manager separately into its own namespace and `kubectl apply`
    its CRDs each time as helm won't attempt to handle changes to CRD resources.

    To `kubectl apply` the CRDs manually before `helm upgrade` is the typical
    procedure recommended by cert-manager. Sometimes cert-manager provides
    additional upgrade notes, see https://cert-manager.io/docs/release-notes/
    before you upgrade to a new version.
    """
    version = os.getenv("CERT_MANAGER_VERSION")
    if not version:
        raise RuntimeError("CERT_MANAGER_VERSION not set. Source cert-manager.env")

    manifest_url = f"https://github.com/jetstack/cert-manager/releases/download/{version}/cert-manager.crds.yaml"
    print(BOLD + GREEN + f"Installing cert-manager CRDs {version}" + NC, flush=True)

    # Sometimes 'replace' is needed for upgrade (e.g. 1.1->1.2)
    check_call(["kubectl", "apply", "-f", manifest_url], dry_run)

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

    check_call(helm_upgrade, dry_run)


def patch_coredns(dry_run=False):
    """Patch coredns resource allocation

    OVH2 coredns does not have sufficient memory by default after our ban patches
    """
    print(BOLD + GREEN + "Patching coredns resources" + NC, flush=True)
    check_call(
        [
            "kubectl",
            "set",
            "resources",
            "-n",
            "kube-system",
            "deployments/coredns",
            "--limits",
            "memory=250Mi",
            "--requests",
            "memory=200Mi",
        ],
        dry_run,
    )


def deploy_system_charts(release, name=None, dry_run=False):
    """
    Some charts must be deployed into other namespaces
    """
    if not name:
        name = release

    charts = ["mybinder-kube-system", "mybinder-tigera-operator"]

    for chart in charts:
        log_name = f"{chart} {release}"
        ns = chart[9:]

        config_files = get_config_files(release, config_dir=f"system-config/{ns}")
        if not config_files:
            print(
                BOLD + GREEN + f"No config files found for {log_name}" + NC, flush=True
            )
            return

        print(BOLD + GREEN + f"Starting helm upgrade for {log_name}" + NC, flush=True)
        helm = [
            "helm",
            "upgrade",
            "--install",
            "--cleanup-on-fail",
            f"--namespace={ns}",
            "--create-namespace",
            name,
            chart,
        ]
        for config_file in config_files:
            helm.extend(["-f", config_file])

        check_call(helm, dry_run)
        print(
            BOLD + GREEN + f"SUCCESS: Helm upgrade for {log_name} completed" + NC,
            flush=True,
        )

        wait_for_deployments_daemonsets(ns, dry_run)


def main():
    # parse command line args
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "release",
        help="Release to deploy",
        choices=[
            "staging",
            "prod",
            "ovh",
            "ovh2",
            "curvenote",
        ],
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
    argparser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands, but don't run them",
    )
    stages = ["all", "auth", "networkban", "system", "certmanager", "mybinder"]
    argparser.add_argument(
        "--stage",
        choices=stages,
        default=stages[0],
        help="Stage to deploy, default all",
    )

    args = argparser.parse_args()

    # if one argument given make cluster == release
    cluster = args.cluster or args.release

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

        if args.stage in ("all", "auth"):
            if cluster.startswith("ovh"):
                setup_auth_ovh(args.release, cluster, args.dry_run)
                patch_coredns(args.dry_run)
            elif cluster in AZURE_RGs:
                setup_auth_azure(cluster, args.dry_run)
            elif cluster in GCP_PROJECTS:
                setup_auth_gcloud(args.release, cluster, args.dry_run)
            elif cluster in AWS_DEPLOYMENTS:
                setup_auth_aws(cluster, args.dry_run)
            else:
                raise Exception("Cloud cluster not recognised!")

    if args.stage in ("all", "networkban"):
        update_networkbans(cluster, args.dry_run)
    if args.stage in ("all", "system"):
        deploy_system_charts(args.release, args.name, args.dry_run)
    if args.stage in ("all", "certmanager"):
        setup_certmanager(args.dry_run)
    if args.stage in ("all", "mybinder"):
        deploy(args.release, args.name, args.dry_run)


if __name__ == "__main__":
    main()
