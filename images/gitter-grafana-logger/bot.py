import argparse
import json
import os
import threading
import time

import requests


def create_annotation(grafana_url, grafana_api_key, text):
    """
    Create annotation in a grafana instance.
    """
    tags = ['operations log']
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


def stream_chat(gitter_url, grafana_url, GITTER_KEY, GRAFANA_KEY):
    r = requests.get(gitter_url,
                     stream=True,
                     headers={
                         'Authorization': f'Bearer {GITTER_KEY}'
                     })

    for line in r.iter_lines():
        # filter out empty lines
        if line:
            decoded_line = line.decode('utf-8')

            try:
                msg = json.loads(decoded_line)
            except json.decoder.JSONDecodeError:
                continue

            text = msg['text'].strip()
            if text.startswith("!log"):
                name = msg['fromUser']['username']
                print(f"{name}: {text}")
                create_annotation(grafana_url, GRAFANA_KEY, f"{name}: {text}")


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--grafana-url',
        help='URL of the grafana instance to use',
        default='https://grafana.mybinder.org'
    )
    argparser.add_argument(
        '--gitter-url',
        help='URL of the gitter room',
        default='https://stream.gitter.im/v1/rooms/5b618e23d73408ce4fa31667/chatMessages'
    )
    args = argparser.parse_args()

    GRAFANA_KEY = os.environ['GRAFANA_API_KEY']
    GITTER_KEY = os.environ['GITTER_API_KEY']

    stream_chat(args.gitter_url, args.grafana_url, GITTER_KEY, GRAFANA_KEY)


if __name__ == '__main__':
    main()
