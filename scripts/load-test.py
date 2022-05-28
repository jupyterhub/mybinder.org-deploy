import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def build_binder(repo,
                 ref='master',
                 binder_url='https://mybinder.org'):
    """Launch a binder"""
    url = binder_url + f'/build/gh/{repo}/{ref}'
    r = requests.get(url, stream=True)
    r.raise_for_status()
    for line in r.iter_lines():
        line = line.decode('utf8', 'replace')
        if line.startswith('data:'):
            yield json.loads(line.split(':', 1)[1])


def launch_binder(n, repo, ref='master', filepath=None,
                  binder_url='https://mybinder.org',
                  delay=10):
    """Launch a new binder from `repo` at `ref`

    Use `delay` to delay the launch by a random amount in seconds.

    If `filepath` is set a notebook with that name will be fetched.
    """
    delay = random.random() * delay
    time.sleep(delay)

    launched_at = time.time()
    total_bytes = 0

    for evt in build_binder(repo, ref=ref, binder_url=binder_url):
        if 'message' in evt:
            pass
        if evt.get('phase') == 'ready':
            ready_at = time.time()
            s = requests.Session()

            if filepath is None:
                url = "{url}?token={token}".format(**evt)
            else:
                url = "{url}notebooks/{filepath}?token={token}".format(
                    filepath=filepath, **evt
                    )

            # GET the notebook
            r = s.get(url)
            r.raise_for_status()
            notebook_at = time.time()
            total_bytes += len(r.content)

            # spawn a kernel
            url = "{url}api/sessions?token={token}".format(**evt)
            r = s.post(url, json={"path": "Foobar.ipynb",
                                  "type": "notebook",
                                  "name": "",
                                  "kernel": {"id": None,
                                             "name": "python3"
                                             }
                                  }
                       )
            r.raise_for_status()
            kernel_at = time.time()
            total_bytes += len(r.content)

            # biggest file in the session
            url = ("{url}nbextensions/jupyter-js-widgets/"
                   "extension.js?v=20180705212711&token={token}".format(**evt)
                   )
            r = s.get(url)
            r.raise_for_status()
            widgets_at = time.time()
            total_bytes += len(r.content)

            done_at = time.time()
            return {'idx': n,
                    'start': launched_at,
                    'ready': ready_at,
                    'kernel': kernel_at,
                    'notebook': notebook_at,
                    'widgets': widgets_at,
                    'end': done_at,
                    'total_bytes': total_bytes,
                    'status': 'success',
                    }

    else:
        failed_at = time.time()
        print(n, "never launched.")
        return {'idx': n, 'start': launched_at, 'end': failed_at,
                'status': 'fail'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=str, help="The GitHub repo to build")
    parser.add_argument(
        '--ref', default='master', help="The ref of the repo to build")
    parser.add_argument(
        '--filepath', default=None, help="The notebook to open")
    parser.add_argument(
        '--results', default='results.json', help="File name to store results in")
    parser.add_argument(
        '--n-launches', default=5, help='Number of launches to perform',
        type=int)
    parser.add_argument(
        '--binder',
        default='https://mybinder.org',
        help="""
        The URL of the binder instance to use.
        Use `http://localhost:8585` if you are doing local testing.
    """)
    opts = parser.parse_args()

    gun_time = time.time()
    with ThreadPoolExecutor(max_workers=100) as executor:
        results = {}
        for n in range(opts.n_launches):
            job = executor.submit(launch_binder, n,
                                  opts.repo, opts.ref, opts.filepath)
            results[job] = n

        print('launching...')
        launches = []
        for future in as_completed(results):
            idx = results[future]
            try:
                launch = future.result()
                # save it for later
                launches.append(launch)
            except Exception as exc:
                print('{!r} generated an exception: {}'.format(idx, exc))
            else:
                if launch['status'] == 'success':
                    print('Launch %r succeeded and took %is' %
                          (idx, launch['end'] - launch['start'])
                          )
                else:
                    print('Launch %r failed and took %is' %
                          (idx, launch['end'] - launch['start'])
                          )

    with open(opts.results, 'w') as f:
        json.dump({'gun_time': gun_time,
                   'results': launches},
                  f)

    import pprint
    pprint.pprint(launches)
