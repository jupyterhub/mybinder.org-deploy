#!/usr/bin/env python3
"""
Script to post [Grafana Annotations](https://grafana.com/docs/grafana/latest/dashboards/annotations/)

This is primarily used to annotate deployments in Grafana,
which can be very useful when displayed alongside various graphs.

This script requires:

- An environment variable GRAFANA_API_KEY with a grafana
  [API Key](https://grafana.com/docs/grafana/latest/http_api/auth/#create-api-token)
  with at least Editor permissions
- The requests library
"""
import argparse
import os
import time

import requests


def create_annotation(grafana_url, grafana_api_key, tags, text):
    """
    Create annotation in a grafana instance.
    """
    return requests.post(
        grafana_url + "/api/annotations",
        json={
            'tags': tags,
            'text': text,
            'time': int(time.time() * 1000),
            'isRegion': False
        },
        headers={
            'Authorization': f'Bearer {grafana_api_key}'
        }
    ).text


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--grafana-url',
        help='URL of the grafana instance to use'
    )

    argparser.add_argument(
        '--tag',
        help='Tags to add to the annotation',
        default=[],
        action='append',
        dest='tags'
    )

    argparser.add_argument(
        'text',
        help='Text to use for the annotation'
    )

    args = argparser.parse_args()
    print(create_annotation(
        args.grafana_url,
        os.environ['GRAFANA_API_KEY'],
        args.tags, 
        args.text
    ))

if __name__ == '__main__':
    main()
