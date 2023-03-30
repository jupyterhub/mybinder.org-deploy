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
    fetch_progress: tqdm.tqdm = tqdm.tqdm(desc="fetching", unit="repo", total=0)
    prune_progress: tqdm.tqdm = tqdm.tqdm(desc="pruning", unit="repo", total=0)

    page = 1
    page_size = 100

    while True:
        page_deleted = 0
        r = requests.get(
            harbor_url + f"/projects/{project_name}/repositories",
            params=dict(sort="update_time", page_size=str(page_size), page=str(page)),
            auth=(username, password),
        )
        if not prune_progress.total and "X-Total-Count" in r.headers:
            prune_progress.total = fetch_progress.total = int(
                r.headers["X-Total-Count"]
            )

        repos: list[dict] = r.json()
        if not repos:
            break
        fetch_progress.update(len(repos))
        r.raise_for_status()
        for repo in repos:
            project_name, repo_name = repo["name"].split("/", 1)
            if repo["artifact_count"] == 0:
                r = requests.delete(
                    harbor_url + f"/projects/{project_name}/repositories/{repo_name}",
                    auth=(username, password),
                )
                r.raise_for_status()
                prune_progress.update(1)
                page_deleted += 1
        # if we deleted less than 90% of the images, request the next page
        # i.e. stay on the current page if we delete at least 50% of the repos
        # so we don't skip over them
        # the alternative is to fetch _all_ repos
        if page_deleted < page_size / 2:
            page += 1
    fetch_progress.close()
    prune_progress.close()
    print(f"Pruned {prune_progress.n} repositories with no artifacts")


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
