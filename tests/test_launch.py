import json
import pytest
import requests

@pytest.mark.timeout(300)
def test_launch_binder(binder_url):
    """
    We can launch an image that most likely already has been built.
    """
    # Known good version of this repo
    repo = 'binder-examples/requirements'
    ref = '082b794'
    build_url = binder_url + '/build/gh/{repo}/{ref}'.format(repo=repo, ref=ref)
    r = requests.get(build_url, stream=True)
    r.raise_for_status()
    for line in r.iter_lines():
        line = line.decode('utf8')
        if line.startswith('data:'):
            data = json.loads(line.split(':', 1)[1])
            if data.get('phase') == 'ready':
                notebook_url = data['url']
                token = data['token']
                break
    else:
        # This means we never got a 'Ready'!
        assert False

    headers = {
        'Authorization': 'token {}'.format(token)
    }
    r = requests.get(notebook_url + '/api', headers=headers)
    assert r.status_code == 200
    assert 'version' in r.json()

    r = requests.post(notebook_url + '/api/shutdown', headers=headers)
    assert r.status_code == 200
