#!/usr/bin/env python3
import argparse
import subprocess
import yaml
import os


def deploy(release):
    # Set up helm!
    subprocess.check_call(['helm', 'repo', 'update'])

    subprocess.check_call(['helm', 'dep', 'up'], cwd='mybinder')

    helm = [
        'helm', 'upgrade', '--install',
        '--namespace', release,
        release,
        'mybinder',
        '--wait',
        '-f', os.path.join('config', release + '.yaml'),
        '-f', os.path.join('secrets', 'config', release + '.yaml')
    ]

    subprocess.check_call(helm)


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
