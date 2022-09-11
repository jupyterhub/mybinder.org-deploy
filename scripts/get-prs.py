#!/usr/bin/env python
import os
import re
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
    "--github-action-escape",
    action="store_true",
    help="Escape output for GitHub Action",
)

args = parser.parse_args()

gh = github.Github(token)
r = gh.get_repo(args.repo)

start = extract_gitref(args.start)
end = extract_gitref(args.end)

prs = set()
git_compare = r.compare(start, end)
for c in git_compare.commits:
    s = gh.search_issues("", type="pr", repo=args.repo, sha=c.sha)
    prs.update(s)


pr_summaries = [
    f"- [#{pr.number}]({pr.html_url}) {pr.title}"
    for pr in sorted(prs, key=lambda pr: pr.number)
]
if args.github_action_escape:
    print("%0A".join(pr_summaries))
else:
    print("\n".join(pr_summaries))
