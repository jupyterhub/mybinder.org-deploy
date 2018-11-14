#!/usr/bin/env python3
"""
Cleanup images that don't match the current image prefix.

Currently deletes all images that don't match the current prefix,
as well as old builds of the binderhub-ci-repos.

Requires aiohttp and tqdm:

    pip3 install aiohttp aiodns tqdm

Usage:

./scripts/delete-old-images.py [staging|prod]

"""

import asyncio
from collections import defaultdict
from functools import partial
import os
from pprint import pformat
import time

import aiohttp
import tqdm
import yaml

HERE = os.path.dirname(__file__)

# delete builds used for CI, as well
CI_STRINGS = ["binderhub-ci-repos-", "binderhub-2dci-2drepos-"]


class RequestFailed(Exception):
    """Nicely formatted error for failed requests"""

    def __init__(self, code, method, url, content, action=""):
        self.code = code
        self.content = content
        self.method = method
        self.url = url
        self.action = action

    def __str__(self):
        return (
            f"{self.action} {self.method} {self.url}"
            f" failed with {self.code}:\n  {self.content}"
        )


async def raise_for_status(r, action=""):
    """raise an informative error on failed requests"""
    if r.status < 400:
        return
    if r.headers.get("Content-Type") == "application/json":
        # try to parse json error messages
        content = await r.json()
        if isinstance(content, dict) and "errors" in content:
            messages = []
            for error in content["errors"]:
                messages.append(f"{error.get('code')}: {error.get('message')}")
            content = "\n".join(messages)
        else:
            content = pformat(content)
    else:
        content = await r.text()
    raise RequestFailed(r.status, r.request_info.method, r.request_info.url, content)


async def list_images(session, project):
    """List the images for a project"""
    images = []
    first = True
    url = "https://gcr.io/v2/_catalog"
    while url:
        async with session.get(url) as r:
            await raise_for_status(r, "listing images")
            resp = await r.json()
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
        await raise_for_status(r, f"Getting tags for {image}")
        return await r.json()


async def delete_image(session, image, digest, tags):
    """Delete a single image

    Tags must be removed before deleting the actual image
    """
    manifests = f"https://gcr.io/v2/{image}/manifests"
    # delete tags first (required)
    for tag in tags:
        async with session.delete(f"{manifests}/{tag}") as r:
            await raise_for_status(r, f"Deleting tag {image}@{tag}")

    # this is the actual deletion
    async with session.delete(f"{manifests}/{digest}") as r:
        await raise_for_status(r, f"Deleting image {image}@{digest}")


async def main(release="staging", project=None, concurrency=20):
    if not project:
        project = f"binder-{release}"
    with open(os.path.join(HERE, os.pardir, "config", release + ".yaml")) as f:
        config = yaml.safe_load(f)

    prefix = config["binderhub"]["config"]["BinderHub"]["image_prefix"]

    with open(
        os.path.join(HERE, os.pardir, "secrets", "config", release + ".yaml")
    ) as f:
        config = yaml.safe_load(f)

    password = config["binderhub"]["registry"]["password"]

    start = time.perf_counter()
    semaphores = defaultdict(lambda: asyncio.BoundedSemaphore(concurrency))

    async def bounded(f, *args, **kwargs):
        """make an async call, bounding the concurrent calls with a semaphore

        Limits the number of outstanding calls of any given function to `concurrency`.
        Too many concurrent requests results in timeouts
        since the timeout starts when the Python code is called,
        not when the request actually initiates.

        The concurrency limit is *per function*,
        so with concurrency=20, there can be 20 outstanding calls to get_manifest
        *and* 20 outstanding calls to delete_image.

        This avoids the two separate queues contending with each other for slots.
        """

        async with semaphores[f]:
            return await f(*args, **kwargs)

    async with aiohttp.ClientSession(
        auth=aiohttp.BasicAuth("_json_key", password),
        connector=aiohttp.TCPConnector(limit=2 * concurrency),
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
            tag_futures.append(
                asyncio.ensure_future(bounded(get_manifest, session, image))
            )
        if not matches:
            raise RuntimeError(
                f"No images matching prefix {prefix}. Would delete all images!"
            )
        print(f"Not deleting {matches} images starting with {prefix}")
        if not tag_futures:
            print("Nothing to delete")
            return
        print(f"{len(tag_futures)} images to delete (not counting tags)")

        delete_futures = set()
        print("Fetching tags")
        delete_progress = tqdm.tqdm(
            total=len(tag_futures), position=2, unit_scale=True, desc="builds deleted"
        )
        delete_byte_progress = tqdm.tqdm(
            total=0, position=3, unit="B", unit_scale=True, desc="bytes deleted"
        )

        try:
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
                        bounded(delete_image, session, image, digest, info["tag"])
                    )
                    delete_futures.add(f)
                    # update progress when done
                    f.add_done_callback(lambda f: delete_progress.update(1))
                    f.add_done_callback(
                        partial(
                            lambda nbytes, f: delete_byte_progress.update(nbytes),
                            nbytes,
                        )
                    )
                done, delete_futures = await asyncio.wait(delete_futures, timeout=0)
                if done:
                    # collect possible errors
                    await asyncio.gather(*done)

            if delete_futures:
                await asyncio.gather(*delete_futures)
        finally:
            delete_progress.close()
            delete_byte_progress.close()
            print("\n\n\n\n")
            print(f"deleted {delete_progress.n} images")
            print(
                f"deleted {delete_byte_progress.n} bytes (not counting shared layers)"
            )
            print(f"in {int(time.perf_counter() - start)} seconds")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "release",
        type=str,
        nargs="?",
        default="staging",
        help="The release whose images should be cleaned up (staging or prod)",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="",
        help="The gcloud project to use; only needed if not of the form `binder-{release}`.",
    )
    parser.add_argument(
        "-j",
        "--concurrency",
        type=int,
        default=20,
        help="The number of concurrent requests to make. "
        "Too high and there may be timeouts. Default is 20.",
    )
    opts = parser.parse_args()
    asyncio.get_event_loop().run_until_complete(
        main(opts.release, opts.project, opts.concurrency)
    )
