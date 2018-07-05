import argparse
import json
import time
import random
import pickle

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


Launch = namedtuple('Launch', 'idx start end status')


def build_binder(repo,
                  ref='master',
                  binder_url='https://mybinder.org'):
    """Launch a binder"""
    url = binder_url + '/build/gh/{repo}/{ref}'.format(repo=repo, ref=ref)
    r = requests.get(url, stream=True)
    r.raise_for_status()
    for line in r.iter_lines():
        line = line.decode('utf8', 'replace')
        if line.startswith('data:'):
            yield json.loads(line.split(':', 1)[1])


def launch_binder(n, repo, ref='master', binder_url='https://mybinder.org'):
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
            url = "{url}?token={token}".format(**evt)
            ready_at = time.time()
            print(n, "ready at %s" % url)
            return Launch(n, launched_at, ready_at, 'success')

    else:
        failed_at = time.time()
        print(n, "never launched.")
        return Launch(n, launched_at, failed_at, 'fail')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=str, help="The GitHub repo to build")
    parser.add_argument(
        '--ref', default='master', help="The ref of the repo to build")
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
            results[executor.submit(launch_binder, n, opts.repo)] = n

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
                if launch.status == 'success':
                    print('Launch %r succeeded and took %is' % (idx,
                                                                launch.end - launch.start))
                else:
                    print('Launch %r failed and took %is' % (idx,
                                                             launch.end - launch.start))

    with open(opts.results, 'wb') as f:
        pickle.dump({'gun_time': gun_time,
                     'results': launches},
                    f)
