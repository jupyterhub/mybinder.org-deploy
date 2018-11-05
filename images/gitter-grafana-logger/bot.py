#!/usr/bin/env python3
import argparse
import json
import os
import time
import aiohttp
import asyncio


async def create_annotation(session, grafana_url, grafana_api_key, text):
    """
    Create annotation in a grafana instance.
    """
    tags = ['ops-log']
    async with session.post(
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
    ) as resp:
        return await resp.text()


async def stream_chat(session, gitter_room_id, grafana_url, GITTER_KEY, GRAFANA_KEY):
    gitter_stream_url = f'https://stream.gitter.im/v1/rooms/{gitter_room_id}/chatMessages'

    print(f'Started connection to Gitter Room {gitter_room_id}')
    async with session.get(
            gitter_stream_url,
            headers={'Authorization': f'Bearer {GITTER_KEY}'}
        ) as response:
        async for line in response.content:
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
                    print(f"Received {name}: {text}")
                    await create_annotation(session, grafana_url, GRAFANA_KEY, f"{name}: {text}")
                    print(f"Annotation created for {name}: {text}")


async def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--grafana-url',
        help='URL of the grafana instance to use',
        default='https://grafana.mybinder.org'
    )
    argparser.add_argument(
        '--gitter-room-id',
        help='IDs of rooms to watch',
        action='append'
    )
    args = argparser.parse_args()

    GRAFANA_KEY = os.environ['GRAFANA_API_KEY']
    GITTER_KEY = os.environ['GITTER_API_KEY']

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[
            asyncio.ensure_future(stream_chat(session, room_id, args.grafana_url, GITTER_KEY, GRAFANA_KEY))
            for room_id in args.gitter_room_id
        ])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())