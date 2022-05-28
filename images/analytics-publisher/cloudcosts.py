"""
Produces daily summaries of GCP spending data.
"""
import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile

from dateutil.parser import parse
from google.cloud import storage


def totals_from_csv(file):
    totals = {}
    reader = csv.DictReader(file)
    for row in reader:
        time_range = (row['Start Time'], row['End Time'])
        totals[time_range] = totals.get(time_range, 0) + float(row['Cost'])

    return totals


def totals_from_json(file):
    totals = {}
    for item in json.load(file):
        cost = float(item['cost']['amount'])
        time_range = (item['start_time'], item['end_time'])
        totals[time_range] = totals.get(time_range, 0) + cost

    return totals

def publish_daily_cost(
        billing_bucket_name, target_bucket_name, target_object_name,
        kind='json', debug=False, dry_run=False
    ):
    totals = {}
    client = storage.Client()

    bucket = storage.Bucket(client, billing_bucket_name)
    if kind == 'csv':
        prefix='report-'
    else:
        prefix='billing-'
    blobs = bucket.list_blobs(prefix=prefix)

    for blob in blobs:
        buffer = io.StringIO(blob.download_as_string().decode())

        if kind == 'csv':
            current_totals = totals_from_csv(buffer)
        else:
            current_totals = totals_from_json(buffer)

        for time_range, cost in current_totals.items():
            totals[time_range] = totals.get(time_range, 0) + cost


    # We want to push out sorted jsonl
    sorted_items = [
        {
            'version': 1,
            'start_time': start_time,
            'end_time': end_time,
            'cost': cost
        }
        for (start_time, end_time), cost in totals.items()
    ]

    sorted_items.sort(key=lambda d: d['start_time'])

    if debug:
        for item in sorted_items:
            print(json.dumps(item))

    if not dry_run:
        target_bucket = storage.Bucket(client, target_bucket_name)
        blob = target_bucket.blob(target_object_name)

        target_buffer = io.StringIO()
        for item in sorted_items:
            target_buffer.write(json.dumps(item) + '\n')

        target_buffer.seek(0)

        blob.upload_from_file(target_buffer)

    return sorted_items

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'billing_bucket_name',
        help='Name of bucket GCP billing data is exported to'
    )
    argparser.add_argument(
        'target_bucket_name',
        help='Name of bucket to push aggregate daily data to'
    )
    argparser.add_argument(
        'target_object_name',
        help='Name of object to output containing aggregate daily data'
    )
    argparser.add_argument(
        '--kind',
        choices=('csv', 'json'),
        help='Content Type of billing data export available in bucket',
        default='json'
    )
    argparser.add_argument(
        '--debug',
        help='Print daily billing data to stdout',
        action='store_true',
        default=False
    )
    argparser.add_argument(
        '--dry-run',
        help='Do not push output to output GCS bucket',
        action='store_true',
        default=False
    )

    args = argparser.parse_args()
    publish_daily_cost(
        args.billing_bucket_name, args.target_bucket_name, args.target_object_name,
        args.kind, args.debug, args.dry_run
    )


if __name__ == '__main__':
    main()