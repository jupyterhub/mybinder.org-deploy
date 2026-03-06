import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from subprocess import run

import requests
import yaml

# requires local checkout of binderhub
from binderhub.app import BinderHub
from binderhub.builder import _safe_build_slug
from binderhub.repoproviders import (
    DataverseProvider,
    FigshareProvider,
    HydroshareProvider,
    ZenodoProvider,
)
from tqdm import tqdm

# repo providers that need to resolve ref to get image
_needs_resolved_ref = (
    DataverseProvider,
    FigshareProvider,
    HydroshareProvider,
    ZenodoProvider,
)

values_yaml = Path("/etc/binderhub/config/values.yaml")

CONCURRENCY = int(os.environ.get("CONCURRENCY") or 4)
DAYS = int(os.environ.get("DAYS") or 2)
DRY_RUN = os.environ.get("DRY_RUN", "") not in {"", "0"}
DEST_PREFIX = os.environ.get("DEST_PREFIX", "oci.2i2c.mybinder.org/mybinder-builds/")
REGISTRIES = os.environ.get(
    "REGISTRIES", "registry.gesis.mybinder.org,registry.2i2c.mybinder.org"
).split(",")
ORIGINS = os.environ.get("ORIGINS", "gesis.mybinder.org,2i2c.mybinder.org").split(",")
RETRY_TIMES = int(os.environ.get("RETRY_TIMES") or 5)

interactive = sys.stdin.isatty()


def load_incluster_config():
    with values_yaml.open() as f:
        values = yaml.safe_load(f)
    return values


def load_local_config(cluster_name: str):
    """load config from a local checkout of mybinder.org-deploy"""
    root = Path(__file__).resolve().parents[2]
    config_dir = root / "config"
    with (config_dir / f"{cluster_name}.yaml").open() as f:
        config = yaml.safe_load(f)["binderhub"]
    return config


if values_yaml.exists():
    values = load_incluster_config()
else:
    values = load_local_config("hetzner-2i2c")

image_prefix = values["config"]["BinderHub"]["image_prefix"]
registry, *_ = image_prefix.partition("/")

providers = {
    provider.name.get_default_value(): provider
    for provider in BinderHub().repo_providers.values()
}


# must copy logic from binderhub.launch image hashing
async def compute_image(build_event: dict):
    ref = build_event["ref"]
    spec = build_event["spec"]
    Provider = providers[build_event["provider"]]
    provider = Provider(spec=spec)
    if isinstance(provider, _needs_resolved_ref):
        # most providers don't need resolved ref for build slug,
        # but some do
        ref = await provider.get_resolved_ref()

    build_slug = provider.get_build_slug()
    # build_name = _generate_build_name(
    #     build_slug, ref, prefix="build-"
    # )
    safe_build_slug = _safe_build_slug(build_slug, limit=255 - len(image_prefix))

    image_name = (
        "{prefix}{build_slug}:{ref}".format(
            prefix=image_prefix, build_slug=safe_build_slug, ref=ref
        )
        .replace("_", "-")
        .lower()
    )
    return image_name


async def list_recent_images(days: int = 2, members=set()):
    seen_events = set()
    seen_images = set()
    today = date.today()
    for i in range(days):
        day = today - timedelta(days=i)
        url = f"https://archive.analytics.mybinder.org/events-{day.strftime("%Y-%m-%d")}.jsonl"
        for line in requests.get(url).text.splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except Exception:
                print(f"ERROR loading event: {line}")
                continue
            key = (event["provider"], event["spec"], event["ref"], event["origin"])
            if key in seen_events:
                continue
            else:
                seen_events.add(key)
            if event["origin"] not in ORIGINS:
                continue
            image = await compute_image(event)
            if image in seen_images:
                continue
            else:
                seen_images.add(image)
            yield image


def migrate_image(src_image: str, dest_prefix: str, stream):
    registry, _, image = src_image.partition("/")
    dest_image = f"{dest_prefix}{image}"
    stream.write(f"{'DRY RUN: ' * DRY_RUN}copying {src_image} -> {dest_image}")
    if DRY_RUN:
        p = run(
            [
                "skopeo",
                "inspect",
                f"docker://{src_image}",
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        info = json.loads(p.stdout)
        total_bytes = sum(layer["Size"] for layer in info["LayerData"])
        print(f"{src_image}: {total_bytes / 1e9:.1f}GB")
        return

    p = run(
        [
            "skopeo",
            "copy",
            "--dest-precompute-digests",
            "--preserve-digests",
            "--all",
            f"--retry-times={RETRY_TIMES}",
            f"docker://{src_image}",
            f"docker://{dest_image}",
        ],
        capture_output=not interactive,
        check=False,
    )
    if p.returncode:
        stream.write(f"Error copying {src_image} -> {dest_image}")
        if p.stdout:
            stream.write(p.stdout)
        if p.stderr:
            stream.write(p.stderr)

    return p.returncode


def skopeo_login(registry: str, cluster_name: str):
    """Login to one registry with skopeo

    Can be used to generate auth.json

    Not currently used in the script.
    """
    _registry, _, cluster_origin = registry.partition(".")
    root = Path(__file__).resolve().parents[2]
    secret_config_dir = root / "secrets/config"
    with (secret_config_dir / f"{cluster_name}.yaml").open() as f:
        config = yaml.safe_load(f)
    registry_config = config["binderhub"]["registry"]
    username = registry_config["username"]
    password = registry_config["password"]
    run(
        [
            "skopeo",
            "login",
            registry,
            "--username",
            username,
            "--password-stdin",
            "--authfile=./auth.json",
        ],
        input=password,
        text=True,
        check=True,
    )


@contextmanager
def cancel_on_error(pool):
    try:
        yield
    except Exception as e:
        print("Exception!", e)
        raise
    finally:

        pool.shutdown(wait=True, cancel_futures=True)


async def main():
    loop = asyncio.get_running_loop()
    futures = set()
    pool = ThreadPoolExecutor(CONCURRENCY)
    start = time.monotonic()
    with tqdm(desc="found", disable=False) as image_progress, tqdm(
        desc="copied", total=0, disable=False
    ) as copy_progress, tqdm(
        desc="errors", total=0, disable=False
    ) as error_progress, cancel_on_error(
        pool
    ):

        async for image in list_recent_images(DAYS):
            image_progress.update(1)
            copy_progress.total += 1
            f = loop.run_in_executor(
                pool, migrate_image, image, DEST_PREFIX, copy_progress
            )
            futures.add(f)

            def handle_done(f):
                copy_progress.update(1)
                if f.exception():
                    error_progress.update(1)
                else:
                    result = f.result()
                    if result:
                        error_progress.update(1)

            if False and not interactive:
                duration = time.monotonic() - start
                td = timedelta(seconds=int(duration))
                total = image_progress.total or "?"
                print(f"Duration: {td}")
                print(f"copied: {copy_progress.n} / {total}")
                print(f"errors: {error_progress.n} / {copy_progress.n}")

            f.add_done_callback(handle_done)
            done, futures = await asyncio.wait(futures, timeout=0)
            await asyncio.gather(*done)
        image_progress.total = image_progress.n
        copy_progress.total = image_progress.n
        error_progress.total = image_progress.n
        image_progress.close()
        await asyncio.gather(*futures)


if __name__ == "__main__":
    asyncio.run(main())
