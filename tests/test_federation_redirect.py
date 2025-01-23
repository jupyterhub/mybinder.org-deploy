import requests


def test_active_hosts(helm_config, federation_url):
    r = requests.get(federation_url + "/active_hosts")
    r.raise_for_status()
    resp = r.json()
    assert "active_hosts" in resp
    # assert anything about the state of active hosts?
    # 'empty' is a valid state


def test_proxy_page(helm_config, federation_url):
    r = requests.get(federation_url)
    r.raise_for_status()
    assert '<div id="root"></div>' in r.text
