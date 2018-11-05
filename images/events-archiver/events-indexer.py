#!/usr/bin/env python3
"""
Generate index.html & index.jsonl from Events GCS bucket

This script reads the bucket containing archived events
generating a human readable index.html & a machine readable
index.jsonl.
"""
import json
import argparse
import sys
from dateutil.parser import parse
from datetime import datetime
import tempfile
from google.cloud import logging, storage
import jinja2
import os
from glob import glob

HERE = os.path.dirname(os.path.abspath(__file__))

# Static files that should be uploaded by indexer
STATIC_FILES = glob(os.path.join(HERE, 'static', 'bootstrap-4.1.3.min.css'))

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'project',
        help='Name of the GCP project to read logs from'
    )

    argparser.add_argument(
        'bucket',
        help='GCS bucket to read archived event files from'
    )

    argparser.add_argument(
        '--debug',
        help='Print events when processing',
        action='store_true',
        default=False
    )

    argparser.add_argument(
        '--dry-run',
        help='Do not upload processed events to GCS',
        action='store_true',
        default=False
    )

    args = argparser.parse_args()


    storage_client = storage.Client()
    bucket = storage.Bucket(storage_client, args.bucket)

    blobs = bucket.list_blobs(prefix='events-')

    archives = []

    with open(os.path.join(HERE, 'index.html')) as f:
        html_template = jinja2.Template(f.read())

    for blob in blobs:
        archives.append({
            'name': blob.name,
            'date': blob.metadata['Events-Date'],
            'count': blob.metadata['Events-Count']
        })
    
    with tempfile.TemporaryFile(mode='w+') as htmlfile, \
         tempfile.TemporaryFile(mode='w+') as jsonlfile:

        html_index = html_template.render(
            archives=sorted(archives, key=lambda archive: archive['date'], reverse=True),
            generated_time=datetime.utcnow().isoformat() + 'Z'
        )

        if args.debug:
            print(html_index)

        htmlfile.write(html_index)

        for archive in archives:
            jsonlfile.write(json.dumps(archive) + '\n')

        htmlfile.seek(0)
        jsonlfile.seek(0)

        if not args.dry_run:
            bucket.blob('index.html').upload_from_file(htmlfile)
            bucket.blob('index.jsonl').upload_from_file(jsonlfile)


    print(STATIC_FILES, file=sys.stderr)
    # Upload static assets
    for static_file in STATIC_FILES:
        blob_name = os.path.relpath(static_file, HERE)
        bucket.blob(blob_name).upload_from_filename(static_file)

        

if __name__ == '__main__':
    main()