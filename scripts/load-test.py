import argparse
import json
import time
import random
import pickle

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


#https://mybinder.org/v2/gh/fboylu/binder/master?filepath=00_DevelopModel.ipynb
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
                  binder_url='https://mybinder.org'):
    delay = random.random() * 10
    time.sleep(delay)

    launched_at = time.time()

    for evt in build_binder(repo, ref=ref, binder_url=binder_url):
        if 'message' in evt:
            print(n, "[{phase}] {message}".format(
                phase=evt.get('phase', ''),
                message=evt['message'].rstrip(),
            ))
        if evt.get('phase') == 'ready':
            ready_at = time.time()
            s = requests.Session()

            if filepath is None:
                url = "{url}?token={token}".format(**evt)
            else:
                url = "{url}notebooks/{filepath}?token={token}".format(
                    filepath=filepath, **evt
                    )
            print(n, "ready at %s" % url)

            # GET the notebook
            r = s.get(url)
            r.raise_for_status()
            notebook_at = time.time()

            # spawn a kernel
            # POST {url}api/sessions?token={token}
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

            # biggest file in the session
            url = ("{url}nbextensions/jupyter-js-widgets/"
                   "extension.js?v=20180705212711&token={token}".format(**evt)
                   )
            r = s.get(url)
            r.raise_for_status()
            widgets_at = time.time()

            done_at = time.time()
            return {'idx': n,
                    'start': launched_at,
                    'ready': ready_at,
                    'kernel': kernel_at,
                    'notebook': notebook_at,
                    'widgets': widgets_at,
                    'end': done_at,
                    'status': 'success'}

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
        '--results', default='results.pkl', help="The file to store results in")
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
    with ThreadPoolExecutor(max_workers=10) as executor:
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
                print('%r generated an exception: %s' % (idx, exc))
            else:
                if launch['status'] == 'success':
                    print('Launch %r succeeded and took %is' %
                          (idx, launch['end'] - launch['start'])
                          )
                else:
                    print('Launch %r failed and took %is' %
                          (idx, launch['end'] - launch['start'])
                          )

    with open(opts.results, 'wb') as f:
        pickle.dump({'gun_time': gun_time,
                     'results': launches},
                    f)

    import pprint
    pprint.pprint(launches)
