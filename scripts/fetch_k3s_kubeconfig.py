"""
Fetch k3s.yaml into secrets/{cluster}-kubeconfig.yml

- ensures client credentials are up-to-date
- rewrites server ip to public ip of the host
- rewrites 'default' fields to cluster name for stackable KUBECONFIG

k3s client credentials expire every year.
This script should be run for new k3s clusters and again
when client certificates are reissued.
"""

import socket
import sys
from pathlib import Path
from subprocess import check_call

import yaml

# the names of our k3s clusters
k3s_clusters = ["staging", "bids-ovh", "hetzner-gesis", "hetzner-2i2c"]

repo = Path(__file__).resolve().parents[1]
secrets = repo / "secrets"


def fetch_cluster_kubeconfig(cluster_name):
    cluster_key = secrets / f"{cluster_name}.key"
    cluster_config = repo / "config" / f"{cluster_name}.yaml"
    cluster_kubeconfig = secrets / f"{cluster_name}-kubeconfig.yaml"
    print(f"Updating {cluster_kubeconfig}")

    with cluster_config.open() as f:
        cluster_cfg = yaml.safe_load(f)
        host = cluster_cfg["binderhub"]["ingress"]["hosts"][0]

    # fetch current kubeconfig.yaml
    check_call(
        [
            "scp",
            "-i",
            cluster_key,
            f"root@{host}:/etc/rancher/k3s/k3s.yaml",
            cluster_kubeconfig,
        ]
    )
    # rewrite kubeconfig.yaml for remote use
    with cluster_kubeconfig.open() as f:
        config = yaml.safe_load(f)

    # rewrite ip
    cluster_ip = socket.gethostbyname(host)
    cluster = config["clusters"][0]
    cluster["name"] = cluster_name
    server = cluster["cluster"]["server"]
    cluster["cluster"]["server"] = server.replace("127.0.0.1", cluster_ip)
    # rename context/user/cluster so our KUBECONFIGs are mergeable
    config["contexts"][0] = {
        "name": cluster_name,
        "context": {
            "cluster": cluster_name,
            "namespace": cluster_name,
            "user": cluster_name,
        },
    }
    config["current-context"] = cluster_name
    config["users"][0]["name"] = cluster_name
    with cluster_kubeconfig.open("w") as f:
        yaml.dump(config, f)


if __name__ == "__main__":
    for cluster_name in sys.argv[1:] or k3s_clusters:
        fetch_cluster_kubeconfig(cluster_name)
