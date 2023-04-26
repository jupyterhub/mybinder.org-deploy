import sys
from pathlib import Path

import pytest
import yaml

# make sure repo root is on path so we can import from `deploy`
here = Path(__file__).parent.resolve()
repo_root = here.parent
sys.path.insert(0, str(repo_root))

from deploy import get_config_files


def pytest_addoption(parser):
    parser.addoption(
        "--release",
        default="staging",
        help="Name of the federation member release. For loading configuration",
    )


def _helm_merge(a, b):
    """Merge two items, similar to helm

    - dicts are merged
    - lists and scalars are overridden without merge
    - 'a' is modified in place, if a merge occurs
    """
    if not (isinstance(b, dict) and isinstance(a, dict)):
        # if either one is not a dict,
        # there's no merging to do: use 'b'
        return b
    for key, value in b.items():
        if key in a:
            a[key] = _helm_merge(a[key], value)
        else:
            a[key] = value
    return a


@pytest.fixture(scope="session")
def release(request):
    return request.config.getoption("--release")


@pytest.fixture(scope="session")
def helm_config(release):
    """Load the helm values"""
    config = {}
    for config_file in [repo_root / "mybinder/values.yaml"] + get_config_files(release):
        # don't load secret config
        if "secrets" in str(config_file):
            continue
        with open(config_file) as f:
            loaded = yaml.safe_load(f)
        config = _helm_merge(config, loaded)
    return config


@pytest.fixture
def binder_url(helm_config):
    if not helm_config["binderhubEnabled"]:
        pytest.skip("binderhub not enabled")
    return "https://" + helm_config["binderhub"]["ingress"]["hosts"][0]


@pytest.fixture
def hub_url(helm_config):
    if not helm_config["binderhubEnabled"]:
        pytest.skip("binderhub not enabled")
    return helm_config["binderhub"]["config"]["BinderHub"]["hub_url"]


@pytest.fixture
def federation_url(helm_config):
    if not helm_config["federationRedirect"]["enabled"]:
        pytest.skip("federationRedirect not enabled")
    return "https://" + helm_config["federationRedirect"]["host"]
