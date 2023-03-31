#!/usr/bin/env python3
"""
Prune empty repositories in a Harbor registry

Harbor doesn't prune _repositories_, only _artifacts_.
There appears to be a cost to all the empty repos left over time.

This script prunes any repositories that lack any artifacts.
Artifacts are pruned by retention policy and garbage collection.

Requires:

- requests
- ruamel.yaml
- tqdm
"""

from argparse import ArgumentParser
from pathlib import Path

import requests
import tqdm
from ruamel.yaml import YAML

repo = Path(__file__).parent.parent.resolve()

yaml = YAML(typ="safe")

# harbor_url = "https://2lmrrh8f.gra7.container-registry.ovh.net/api/v2.0"
# project_name = "mybinder-builds"
#
# expires_days = 30


def prune_repositories(
    harbor_url: str,
    project_name: str,
    username: str,
    password: str,
) -> None:
    """Deletes all repositories with no activity older than 30 days

    These are often going to be repos with no content
    """
    print("Deleting repositories with no images")

    r = requests.get(
        harbor_url + f"/projects/{project_name}/summary",
        auth=(username, password),
    )
    r.raise_for_status()
    repo_count = r.json()["repo_count"]
    fetch_progress: tqdm.tqdm = tqdm.tqdm(
        desc="fetching", unit="repo", total=repo_count
    )
    prune_progress: tqdm.tqdm = tqdm.tqdm(desc="pruning", unit="repo", total=repo_count)

    page_size = 100

    def fetch_page(page: int = 1) -> list:
        r = requests.get(
            harbor_url + f"/projects/{project_name}/repositories",
            # sort by update_time because the oldest ones are the most likely to be empty
            # reversed (-) because we iterate from the back
            params=dict(sort="-update_time", page_size=str(page_size), page=str(page)),
            auth=(username, password),
        )
        r.raise_for_status()
        repos: list[dict] = r.json()
        fetch_progress.update(len(repos))
        return repos

    page = repo_count // page_size

    for page in range(repo_count // page_size + 1, 0, -1):
        for repo in fetch_page(page):
            # run deletions sequentially because harbor seems to have trouble under too much load
            project_name, repo_name = repo["name"].split("/", 1)
            if repo["artifact_count"] == 0:
                r = requests.delete(
                    harbor_url + f"/projects/{project_name}/repositories/{repo_name}",
                    auth=(username, password),
                )
                r.raise_for_status()
                prune_progress.update(1)
    fetch_progress.close()
    prune_progress.close()
    print(f"Pruned {prune_progress.n}/{repo_count} repositories with no artifacts")


def load_config(member: str) -> dict:
    """Load information necessary for connecting to the harbor instance

    Find URL, project from binderhub config

    Find credentials in secrets/{member}-harbor.yaml
    """

    config_file = repo / "config" / f"{member}.yaml"
    with config_file.open() as f:
        config = yaml.load(f)

    image_prefix = config["binderhub"]["config"]["BinderHub"]["image_prefix"]
    host, project_name, prefix = image_prefix.rsplit("/", 2)
    harbor_url = f"https://{host}/api/v2.0"
    harbor_config_file = repo / "secrets" / f"{member}-harbor.yaml"
    with harbor_config_file.open() as f:
        harbor_config = yaml.load(f)

    return dict(
        harbor_url=harbor_url,
        project_name=project_name,
        username=harbor_config["harbor"]["username"],
        password=harbor_config["harbor"]["password"],
    )


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "cluster", help="The federation member whose harbor should be pruned"
    )
    args = parser.parse_args()
    config = load_config(args.cluster)
    prune_repositories(**config)


if __name__ == "__main__":
    main()
