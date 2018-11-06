#!/usr/bin/env python3
"""Cleanup images that don't match the current image prefix"""

import asyncio
import json
from functools import partial
import os
import sys
import time
import traceback

import aiohttp
import tqdm
import yaml

HERE = os.path.dirname(__file__)

# delete builds used for CI, as well
CI_STRINGS = ["binderhub-ci-repos-", "binderhub-2dci-2drepos-"]


async def list_images(session, project):
    """List the images for a project"""
    images = []
    first = True
    url = "https://gcr.io/v2/_catalog"
    while url:
        async with session.get(url) as r:
            text = await r.text()
            try:
                r.raise_for_status()
            except Exception:
                print(text)
                raise
        resp = json.loads(text)
        for image in resp["repositories"]:
            if image.startswith(project + "/"):
                yield image
        url = resp.get("next")


async def get_manifest(session, image):
    """List the tags for an image

    Returns a dict of the form:
    {
        'sha:digest': {
            imageSizeBytes: '123',
            tag: ['tags'],
            ...
        }
    """
    async with session.get(f"https://gcr.io/v2/{image}/tags/list") as r:
        text = await r.text()
        try:
            r.raise_for_status()
        except Exception:
            print(text)
            raise
    return json.loads(text)


async def delete_image(session, image, digest, tags):
    manifests = f"https://gcr.io/v2/{image}/manifests"
    # delete tags first (required)
    for tag in tags:
        async with session.delete(f"{manifests}/{tag}") as r:
            text = await r.text()
            try:
                r.raise_for_status()
            except Exception:
                print(text)
                raise

    # this is the actual deletion
    async with session.delete(f"{manifests}/{digest}") as r:
        text = await r.text()
        try:
            r.raise_for_status()
        except Exception:
            print(text)
            raise


async def main(release="staging", project=None):
    if not project:
        project = f"binder-{release}"
    with open(os.path.join(HERE, os.pardir, "config", release + ".yaml")) as f:
        config = yaml.safe_load(f)

    prefix = config["binderhub"]["registry"]["prefix"]

    with open(
        os.path.join(HERE, os.pardir, "secrets", "config", release + ".yaml")
    ) as f:
        config = yaml.safe_load(f)

    password = config["binderhub"]["registry"]["password"]

    start = time.perf_counter()

    async with aiohttp.ClientSession(
        auth=aiohttp.BasicAuth("_json_key", password)
    ) as session:

        print(f"Fetching images")
        tag_futures = []
        matches = 0
        total_images = 0
        async for image in list_images(session, project):
            total_images += 1
            if f"gcr.io/{image}".startswith(prefix) and not any(
                ci_string in image for ci_string in CI_STRINGS
            ):
                matches += 1
                continue
            # don't call ensure_future here
            # because we don't want to kick off everything before
            tag_futures.append(asyncio.ensure_future(get_manifest(session, image)))
        if not matches:
            raise RuntimeError(
                f"No images matching prefix {prefix}. Would delete all images!"
            )
        print(f"Not deleting {matches} images starting with {prefix}")
        if not tag_futures:
            print("Nothing to delete")
            return
        print(f"{len(tag_futures)} images to delete (not counting tags)")

        delete_futures = []
        print("Fetching tags")
        delete_progress = tqdm.tqdm(
            total=len(tag_futures), position=2, unit_scale=True, desc="builds deleted"
        )
        delete_byte_progress = tqdm.tqdm(
            total=0, position=3, unit="B", unit_scale=True, desc="bytes deleted"
        )
        for f in tqdm.tqdm(
            asyncio.as_completed(tag_futures),
            total=len(tag_futures),
            position=1,
            desc="images retrieved",
        ):
            manifest = await f
            image = manifest["name"]
            if len(manifest["manifest"]) > 1:
                delete_progress.total += len(manifest["manifest"]) - 1
            for digest, info in manifest["manifest"].items():
                nbytes = int(info["imageSizeBytes"])
                delete_byte_progress.total += nbytes
                f = asyncio.ensure_future(
                    delete_image(session, image, digest, info["tag"])
                )
                delete_futures.append(f)
                # update progress when done
                f.add_done_callback(lambda f: delete_progress.update(1))
                f.add_done_callback(
                    partial(
                        lambda nbytes, f: delete_byte_progress.update(nbytes), nbytes
                    )
                )

                def stop_on_failure(image, digest, f):
                    error = f.exception()
                    if error:
                        tb = error.__traceback__
                        traceback.print_exception(error.__class__, error, tb)
                        sys.exit(f"Failed to delete {image}@{digest}")

                f.add_done_callback(partial(stop_on_failure, image, digest))

        if delete_futures:
            await asyncio.wait(delete_futures)
        delete_progress.close()
        delete_byte_progress.close()
        print("\n\n\n\n")
        print(f"Deleted {len(tag_futures)} images ({delete_progress.total} tags)")
        print(
            f"Deleted {delete_byte_progress.total} bytes (not counting shared layers)"
        )
        print(f"in {int(time.perf_counter() - start)} seconds")


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
    opts = parser.parse_args()
    asyncio.get_event_loop().run_until_complete(main(opts.release, opts.project))
