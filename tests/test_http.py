"""Basic HTTP tests to make sure things are running"""
import pprint

import pytest
import requests


def test_binder_up(binder_url):
    """
    Binder Hub URL is up & returning sensible text
    """
    resp = requests.get(binder_url)
    assert resp.status_code == 200
    assert "GitHub" in resp.text


def test_hub_health(hub_url):
    """check JupyterHubHub health endpoint"""
    resp = requests.get(hub_url + "/hub/api/health")
    print(resp.text)
    assert resp.status_code == 200


def test_binder_health(binder_url):
    """check BinderHub health endpoint"""
    resp = requests.get(binder_url + "/health")
    pprint.pprint(resp.json())
    assert resp.status_code == 200


# the proxy-patches pod can take up to 30 seconds
# to register its route after a proxy restart
@pytest.mark.flaky(reruns=3, reruns_delay=10)
def test_hub_user_redirect(hub_url):
    """Requesting a Hub URL for a non-running user"""
    # this should *not* redirect for now,
    resp = requests.get(hub_url + "/user/doesntexist")
    assert resp.status_code == 424
    assert "Binder not found" in resp.text

    resp = requests.get(hub_url + "/other/doesntexist")
    assert resp.status_code == 404
    assert "Binder not found" in resp.text
