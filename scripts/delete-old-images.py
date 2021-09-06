#!/usr/bin/env python3
"""
Cleanup images that don't match the current image prefix.

Currently deletes all images that don't match the current prefix,
as well as old builds of the binderhub-ci-repos.

Requires aiohttp and tqdm:

    python3 -m pip install aiohttp aiodns tqdm aiohttp-client-cache aiosqlite

Usage:

./scripts/delete-old-images.py [staging|prod] [--dry-run]

"""

import asyncio
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import partial
from pprint import pformat

from dateutil.parser import parse as parse_date

from aiohttp_client_cache import CachedSession, SQLiteBackend
import aiohttp
import tqdm
import tqdm.asyncio
import yaml

HERE = os.path.dirname(__file__)

# delete builds used for CI, as well
CI_STRINGS = ["binderhub-ci-repos-", "binderhub-2dci-2drepos-"]

# don't delete images that *don't* appear to be r2d builds
# (image repository could have other images in it!)
R2D_STRINGS = ["r2d-"]

TODAY = datetime.now()
FIVE_YEARS_AGO = TODAY - timedelta(days=5 * 365)
TOMORROW = TODAY + timedelta(days=1)


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


async def raise_for_status(r, action="", allowed_errors=None):
    """raise an informative error on failed requests"""
    if r.status < 400:
        return
    if allowed_errors and r.status in allowed_errors:
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


def list_images(session, image_prefix):
    if image_prefix.count("/") == 1:
        # docker hub, can't use catalog endpoint
        docker_hub_user = image_prefix.split("/", 1)[0]
        return list_images_docker_hub(session, docker_hub_user)
    elif image_prefix.count("/") == 2:
        registry_host = image_prefix.split("/", 1)[0]
        registry_url = f"https://{registry_host}"
        return list_images_catalog(session, registry_url)


async def list_images_docker_hub(session, docker_hub_user):
    """List the images for a project"""
    url = f"https://hub.docker.com/v2/repositories/{docker_hub_user}/?page_size=100"
    while url:
        async with session.get(url) as r:
            await raise_for_status(r, "listing images")
            resp = await r.json()
        for image in resp["results"]:
            # filter-out not our images??
            yield f"{image['user']}/{image['name']}"
        url = resp.get("next")


async def list_images_catalog(session, registry_host):
    """List the images for a project"""
    url = f"{registry_host}/v2/_catalog"
    while url:
        async with session.get(url) as r:
            await raise_for_status(r, "listing images")
            resp = await r.json()
        for image in resp["repositories"]:
            # filter-out not our images??
            yield image
        if "next" in resp:
            url = resp["next"]
        elif "next" in r.links:
            url = r.links["next"]["url"]
        else:
            url = None



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


async def delete_image(session, image, digest, tags, dry_run=False):
    """Delete a single image

    Tags must be removed before deleting the actual image
    """
    if dry_run:
        fetch = session.get
        verb = "Checking"
    else:
        fetch = session.delete
        verb = "Deleting"

    manifests = f"https://gcr.io/v2/{image}/manifests"
    # delete tags first (required)
    for tag in tags:
        async with fetch(f"{manifests}/{tag}") as r:
            # allow 404 because previous delete  may have been cached
            await raise_for_status(r, f"{verb} tag {image}@{tag}", allowed_errors=[404])

    # this is the actual deletion
    async with fetch(f"{manifests}/{digest}") as r:
        # allow 404 because previous delete  may have been cached
        await raise_for_status(
            r, f"{verb} image {image}@{digest}", allowed_errors=[404]
        )


async def main(
    release="staging", project=None, concurrency=20, delete_before=None, dry_run=True
):
    if dry_run:
        print("THIS IS A DRY RUN.  NO IMAGES WILL BE DELETED.")
        to_be = "to be "
    else:
        to_be = ""

    if delete_before:
        # docker uses millisecond integer timestamps
        delete_before_ms = int(delete_before.timestamp()) * 1e3
    else:
        delete_before_ms = float("inf")

    if not project:
        project = "binderhub-288415"
    with open(os.path.join(HERE, os.pardir, "config", release + ".yaml")) as f:
        config = yaml.safe_load(f)

    prefix = config["binderhub"]["config"]["BinderHub"]["image_prefix"]

    with open(
        os.path.join(HERE, os.pardir, "secrets", "config", release + ".yaml")
    ) as f:
        config = yaml.safe_load(f)

    password = config["binderhub"]["registry"]["password"]
    username = config["binderhub"]["registry"].get("username", "_json_key")

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

    # TODO: basic auth is only sufficient for gcr
    # need to request a token for non-gcr endpoints (ovh, turing on docker hub)
    # e.g.
    auth_kwargs = {}
    print(prefix)
    if prefix.startswith("gcr.io"):
        auth_kwargs["auth"] = aiohttp.BasicAuth(username, password)
    else:
        # get bearer token
        if prefix.count("/") == 2:
            # ovh
            registry_host = prefix.split("/", 1)[0]
            token_url = f"https://{registry_host}/service/token?service=harbor-registry&scope=registry:catalog:*"
        else:
            # turing
            raise NotImplementedError("Can't get docker hub creds yet")

        async with aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(username, password)
        ) as session:
            response = await session.get(token_url)
            token_info = await response.json()
        auth_kwargs["headers"] = {"Authorization": f"Bearer {token_info['token']}"}

    async with CachedSession(
        connector=aiohttp.TCPConnector(limit=2 * concurrency),
        cache=SQLiteBackend(expire_after=24 * 3600),
        **auth_kwargs,
    ) as session:

        print("Fetching images")
        tag_futures = []
        matches = 0
        repos_to_keep = 0
        repos_to_delete = 0

        def should_delete_repository(image):
            """Whether we should delete the whole repository"""
            if f"gcr.io/{image}".startswith(prefix) and not any(
                ci_string in image for ci_string in CI_STRINGS
            ):
                return False

        def should_fetch_repository(image):
            if not any(substring in image for substring in R2D_STRINGS):
                # ignore non-r2d builds
                return False
            if delete_before or should_delete_repository(image):
                # if delete_before, we are deleting old builds of images we are keeping,
                # otherwise, only delete builds that don't match our image prefix
                return True
            else:
                return False

        async for image in tqdm.asyncio.tqdm(
            list_images(session, prefix),
            unit_scale=True,
            desc="listing images",
        ):
            if should_fetch_repository(image):
                if should_delete_repository(image):
                    repos_to_delete += 1
                else:
                    repos_to_keep += 1
                tag_futures.append(
                    asyncio.ensure_future(bounded(get_manifest, session, image))
                )
            else:
                repos_to_keep += 1

        if not repos_to_keep:
            raise RuntimeError(
                f"No images matching prefix {prefix}. Would delete all images!"
            )
        print(f"Not deleting {repos_to_keep} images starting with {prefix}")
        if not tag_futures:
            print("Nothing to delete")
            return
        print(f"{len(tag_futures)} images to delete (not counting tags)")

        delete_futures = set()
        done = set()
        print("Fetching tags")
        delete_progress = tqdm.tqdm(
            total=repos_to_delete,
            position=2,
            unit_scale=True,
            desc=f"builds {to_be}deleted",
        )
        delete_byte_progress = tqdm.tqdm(
            total=0,
            position=3,
            unit="B",
            unit_scale=True,
            desc=f"bytes {to_be}deleted",
        )

        def should_delete_tag(image, info):
            if should_delete_repository(image):
                return True
            if not delete_before:
                # no date cutoff
                return False

            # check cutoff
            image_ms = int(info["timeCreatedMs"])
            image_datetime = datetime.fromtimestamp(image_ms / 1e3)
            # sanity check timestamps
            if image_datetime < FIVE_YEARS_AGO or image_datetime > TOMORROW:
                raise RuntimeError(
                    f"Not deleting image with weird date: {image}, {info}, {image_datetime}"
                )
            if delete_before_ms > image_ms:
                # if dry_run:
                #     print(
                #         f"\nWould delete {image}:{','.join(info['tag'])} {image_datetime.isoformat()}"
                #     )
                return True
            else:
                return False

        try:
            for f in tqdm.tqdm(
                asyncio.as_completed(tag_futures),
                total=len(tag_futures),
                position=1,
                desc="images retrieved",
            ):
                manifest = await f
                image = manifest["name"]
                delete_whole_repo = should_delete_repository(image)
                if delete_whole_repo and len(manifest["manifest"]) > 1:
                    delete_progress.total += len(manifest["manifest"]) - 1
                for digest, info in manifest["manifest"].items():
                    if not should_delete_tag(image, info):
                        continue
                    if not delete_whole_repo:
                        # not counted yet
                        delete_progress.total += 1
                    nbytes = int(info["imageSizeBytes"])
                    delete_byte_progress.total += nbytes
                    f = asyncio.ensure_future(
                        bounded(
                            delete_image,
                            session,
                            image,
                            digest,
                            info["tag"],
                            dry_run=dry_run,
                        )
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
                if delete_futures:
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
            print(f"{to_be}deleted {delete_progress.n} images")
            print(
                f"{to_be}deleted {delete_byte_progress.n} bytes (not counting shared layers)"
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
        "--delete-before",
        type=lambda s: s and parse_date(s),
        default="",
        help="Delete any images older than this date. If unspecified, do not use date cutoff.",
    )
    parser.add_argument(
        "-j",
        "--concurrency",
        type=int,
        default=20,
        help="The number of concurrent requests to make. "
        "Too high and there may be timeouts. Default is 20.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do a dry-run (no images will be deleted)",
    )
    opts = parser.parse_args()
    asyncio.get_event_loop().run_until_complete(
        main(
            opts.release,
            opts.project,
            opts.concurrency,
            delete_before=opts.delete_before,
            dry_run=opts.dry_run,
        )
    )
