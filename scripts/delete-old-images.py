#!/usr/bin/env python3
"""Cleanup images that don't match the current image prefix"""

import asyncio
from asyncio.subprocess import create_subprocess_exec, PIPE
import json

jsonmod = json
from multiprocessing import cpu_count
import os
import pipes
from subprocess import check_call
import sys

import tqdm
import yaml

HERE = os.path.dirname(__file__)

# limit on the number of concurrent outstanding requests
# gcloud api uses a surprising large amount of CPU,
# so don't oversubscribe by default
process_pool = asyncio.BoundedSemaphore(cpu_count())


def setup_auth(release):
    return check_call(
        [
            "gcloud",
            "auth",
            "activate-service-account",
            f"--key-file=secrets/gke-auth-key-{release}.json",
        ]
    )


async def gcloud(cmd, **kwargs):
    """Run a gcloud command"""
    cmd = ["gcloud", "--format=json"] + cmd

    cmd_s = " ".join(map(pipes.quote, cmd))
    # print("> " + cmd_s)
    async with process_pool:
        p = await create_subprocess_exec(*cmd, stdout=PIPE, **kwargs)
        stdout, stderr = await p.communicate()
        exit_code = await p.wait()
    if exit_code:
        print(f"{cmd_s} exited with status {exit_code}")
        sys.exit(exit_code)
    return json.loads(stdout.decode("utf8"))


async def list_images(project):
    """List the images for a project"""
    return await gcloud(
        ["container", "images", "list", f"--repository=gcr.io/{project}"]
    )


async def list_tags(image):
    """List the tags for an image"""
    tags = await gcloud(["container", "images", "list-tags", image])
    return {"image": image, "tags": tags}


async def delete_tag(image, digest):
    await gcloud(
        [
            "container",
            "images",
            "delete",
            f"{image}@{digest}",
            "--force-delete-tags",
            "--quiet",
        ],
        stderr=PIPE,
    )


async def main(release="staging", project=None):
    if not project:
        project = f"binder-{release}"
    with open(os.path.join(HERE, os.pardir, "config", release + ".yaml")) as f:
        config = yaml.safe_load(f)

    prefix = config["binderhub"]["registry"]["prefix"]

    images = await list_images(project)
    tag_futures = []
    print("Fetching images")
    found = 0
    for image in images:
        if image["name"].startswith(prefix):
            # print(f"Not deleting current {image['name']}")
            found += 1
            continue
        tag_futures.append(list_tags(image["name"]))
    if not found:
        raise RuntimeError(
            f"No images matching prefix {prefix}. Would delete all images!"
        )
    print(f"Not deleting {found} images starting with {prefix}")
    if not images:
        print("Nothing to delete")
        return

    delete_futures = []
    print("Fetching tags")
    delete_progress = tqdm.tqdm(total=len(tag_futures), position=2, desc="tags deleted")
    for f in tqdm.tqdm(
        asyncio.as_completed(tag_futures),
        total=len(tag_futures),
        position=1,
        desc="images",
    ):
        taginfo = await f
        image = taginfo["image"]
        if len(taginfo["tags"]) > 1:
            delete_progress.total += len(taginfo["tags"]) - 1
        for tag in taginfo["tags"]:
            f = asyncio.ensure_future(delete_tag(image, tag["digest"]))
            f.add_done_callback(lambda f: delete_progress.update(1))
            delete_futures.append(f)

    print("Waiting to complete")
    if delete_futures:
        await asyncio.wait(delete_futures)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Delete images on unused prefixes")
    parser.add_argument(
        "release",
        type=str,
        nargs="?",
        default="staging",
        help="The release whose images should be cleaned up",
    )
    parser.add_argument("--project", type=str, default="", help="The project to use")
    parser.add_argument(
        "-j",
        "--concurrency",
        type=int,
        default=cpu_count(),
        help="The number of concurrent calls to the gcloud API.",
    )
    opts = parser.parse_args()
    process_pool = asyncio.BoundedSemaphore(opts.concurrency)
    asyncio.get_event_loop().run_until_complete(main(opts.release, opts.project))
