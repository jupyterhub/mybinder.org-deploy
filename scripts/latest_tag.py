"""get the latest tag for a docker repo

Sorts parsed versions.

Expects valid Python version strings,
but accepts normalizing `-build` suffix back to `+build`,
since `+build` isn't valid in docker tags (repo2docker does this).
"""

import json
import re
import subprocess
import sys

from packaging.version import InvalidVersion, Version


def get_tags(repo: str) -> list[str]:
    """return tags for repo as a list

    Calls skopeo list-tags
    """
    out = subprocess.check_output(
        [
            "docker",
            "run",
            "--rm",
            "quay.io/skopeo/stable",
            "list-tags",
            f"docker://{repo}",
        ],
        text=True,
    )
    return json.loads(out)["Tags"]


likely_version_pat = re.compile(r"v?\d", re.IGNORECASE)


def version_key(tag: str) -> Version:
    """never-fails sort-key for sorting version tags

    Uses packaging.version to parse version strings.

    re-normalizes build string suffixes that may have been
    manged to be valid docker tags.

    Ignores any tag that doesn't start `[v]N`, e.g. 'latest'.
    """
    if not likely_version_pat.match(tag):
        # ignore branch names, etc.
        return Version("0.0")

    try:
        # first, try as-is
        return Version(tag)
    except InvalidVersion:
        # reverse the +/- substitution for the build tag
        # because `+` is not legal in docker tags
        try:
            return Version(tag.replace("-", "+"))
        except InvalidVersion:
            print(f"Ignoring invalid version: {tag}", file=sys.stderr)
            return Version("0.0")


def main(repo: str):
    tags = get_tags(repo)
    sorted_tags = sorted(tags, key=version_key)
    # send full sorted list to stderr
    for tag in sorted_tags:
        print(f"  {tag}", file=sys.stderr)

    # send only latest tag to stdout for piping purposes
    print(sorted_tags[-1])


if __name__ == "__main__":
    main(sys.argv[1])
