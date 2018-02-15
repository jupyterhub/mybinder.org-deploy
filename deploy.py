#!/usr/bin/env python3
import argparse
import subprocess
import yaml
import os


def deploy(release):
    helm = [
        'helm', 'upgrade', '--install',
        '--namespace', release,
        release,
        'mybinder',
        '--wait',
        '--timeout', '600',
        '-f', os.path.join('config', release + '.yaml'),
        '-f', os.path.join('secrets', 'config', release + '.yaml')
    ]

    subprocess.check_call(helm)

    # Explicitly wait for all deployments and daemonsets to be fully rolled out

    deployments = subprocess.check_output([
        'kubectl',
        '--namespace', release,
        'get', 'deployments',
        '-o', 'name'
    ]).decode().strip().split('\n')

    daemonsets = subprocess.check_output([
        'kubectl',
        '--namespace', release,
        'get', 'daemonsets',
        '-o', 'name'
    ]).decode().strip().split('\n')

    for d in deployments + daemonsets:
        subprocess.check_call([
            'kubectl', 'rollout', 'status',
            '--namespace', release,
            '--watch', d
        ])


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--user-image-spec',
        default='berkeleydsep/datahub-user'
    )
    subparsers = argparser.add_subparsers(dest='action')

    deploy_parser = subparsers.add_parser('deploy', description='Deploy with helm')
    deploy_parser.add_argument('release', default='staging')


    args = argparser.parse_args()

    deploy(args.release)

main()
