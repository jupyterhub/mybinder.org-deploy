import json
import pytest
import requests
import subprocess
import tempfile
import time
import os
from contextlib import contextmanager


@contextmanager
def push_dummy_gh_branch(repo, branch, keyfile):
    """
    Makes a dummy commit on a given github repo as a given branch

    Requires that the branch not exist. keyfile should be an absolute path.

    Should be used as a contextmanager, it will delete the branch & the
    clone directory when done.
    """

    with tempfile.TemporaryDirectory() as gitdir:
        subprocess.check_call(['git', 'clone', repo, gitdir])
        branchfile = os.path.join(gitdir, 'branchname')
        with open(branchfile, 'w') as f:
            f.write(branch)
        subprocess.check_call(['git', 'add', branchfile], cwd=gitdir)
        subprocess.check_call(['git', 'commit', '-m', 'Dummy update for {}'.format(branch)], cwd=gitdir)
        subprocess.check_call(
            ['git', 'push', 'origin', 'HEAD:{}'.format(branch)],
            env={
                'GIT_SSH_COMMAND': 'ssh -i {}'.format(keyfile)
            },
            cwd=gitdir
        )

        yield
        # Delete the branch so we don't clutter!
        subprocess.check_call(
            ['git', 'push', 'origin', ':{}'.format(branch)],
            env={
                'GIT_SSH_COMMAND': 'ssh -i {}'.format(keyfile)
            },
            cwd=gitdir
        )



@pytest.mark.timeout(300)
def test_build_binder(binder_url):
    """
    We can launch an image that we know hasn't been built
    """
    branch = str(time.time())
    repo = 'binderhub-ci-repos/requirements'

    with push_dummy_gh_branch('git@github.com:/{}.git'.format(repo), branch, os.path.abspath('secrets/binderhub-ci-key')):
        build_url = binder_url + '/build/gh/{repo}/{ref}'.format(repo=repo, ref=branch)
        r = requests.get(build_url, stream=True)
        r.raise_for_status()
        for line in r.iter_lines():
            line = line.decode('utf8')
            if line.startswith('data:'):
                data = json.loads(line.split(':', 1)[1])
                if data['phase'] == 'ready':
                    notebook_url = data['url']
                    token = data['token']
                    break
        else:
            # This means we never got a 'Ready'!
            assert False

        r = requests.get(notebook_url + '/api', headers={
            'Authorization': 'token {}'.format(token)
        })
        assert r.status_code == 200
        assert 'version' in r.json()
