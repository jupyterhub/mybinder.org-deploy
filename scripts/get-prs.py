#!/usr/bin/env python
import os
import re
import uuid
from argparse import ArgumentParser

import github


def extract_gitref(s):
    """
    Extract git ref from a container registry tag or Helm chart version

    Examples:
    - 2022.02.0 -> 2022.02.0
    - 2022.02.0-90.g0345a86 -> 0345a86
    - 0.2.0 -> 0.2.0
    - 0.2.0-n1011.hb49edf6 -> b49edf6
    - 0.2.0-0.dev.git.2752.h3450e52 -> 3450e52
    """
    m = re.match(r"[\d\.]+-[\w\.]+[gh]([0-9a-f]+)", s)
    if m:
        return m.group(1)
    return s


token = os.getenv("GITHUB_TOKEN")

parser = ArgumentParser(description="Summarise PRs from a repo")
parser.add_argument("repo", help="The repository in format user/repo")
parser.add_argument("start", help="commit or image/chart version from which to start")
parser.add_argument("end", help="commit or image/chart version to which to end")
parser.add_argument(
    "--write-github-actions-output",
    help="Name of a GitHub Action's output variable to write to",
)
parser.add_argument(
    "--max-commits",
    type=int,
    default=100,
    help="Maximum number of commits to check",
)

args = parser.parse_args()

gh = github.Github(token)
r = gh.get_repo(args.repo)

start = extract_gitref(args.start)
end = extract_gitref(args.end)

prs = set()
git_compare = r.compare(start, end)
commits = list(git_compare.commits)
if len(commits) > args.max_commits:
    pr_summaries = [
        f"{len(commits)} commits between {start} and {end}, not searching for PRs"
    ]
else:
    for c in commits:
        prs.update(c.get_pulls())
    pr_summaries = [
        f"- [#{pr.number}]({pr.html_url}) {pr.title}"
        for pr in sorted(prs, key=lambda pr: pr.number)
    ]

md = ["# PRs"] + pr_summaries + ["", f"{r.html_url}/compare/{start}...{end}"]
md = "\n".join(md)

if args.write_github_actions_output:
    # GitHub Actions docs on setting a output variable with a multiline string:
    # https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#multiline-strings
    #
    eof_marker = str(uuid.uuid4()).replace("-", "_")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        print(f"{args.write_github_actions_output}<<{eof_marker}", file=f)
        print(md, file=f)
        print(eof_marker, file=f)
else:
    print(md)
