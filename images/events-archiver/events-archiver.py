"""
Read event logs from stackdriver & export them to Google Cloud Storage
"""
from datetime import datetime
import time
import json
import argparse
from dateutil.parser import parse
from google.cloud import logging, storage
import tempfile


def fetch_events(project, log_name, start_time, end_time):
    client = logging.Client()
    filter = f"""
    logName="projects/{project}/logs/{log_name}" AND
    timestamp >= "{start_time}" AND timestamp <= "{end_time}"
    """

    for page in client.list_entries(filter_=filter).pages:
        for entry in page:
            yield entry.payload['message']
        # API limit is 1 read request per second for whole project
        # We sleep 5s between requests to be nicer
        # https://cloud.google.com/logging/quotas
        time.sleep(5)

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'project',
        help='Name of the GCP project to read logs from'
    )
    argparser.add_argument(
        'log_name',
        help='Name of log to read from'
    )

    argparser.add_argument(
        'start_time',
        help='Read events emitted during & after this timestamp' 
    )

    argparser.add_argument(
        'end_time',
        help='Read events emitted during & until this timestamp' 
    )

    argparser.add_argument(
        'bucket_name',
        help='GCS bucket to archive events to'
    )

    argparser.add_argument(
        'object_name',
        help='Name of GCS object to archive to'
    )

    args = argparser.parse_args()

    count = 0
    with tempfile.TemporaryFile(mode='w') as f:
        for event in fetch_events(
            args.project, args.log_name,
            parse(args.start_time).isoformat() + 'Z', parse(args.end_time).isoformat() + 'Z'
        ):
            f.write(event + '\n')
            count += 1
            if count % 100 == 0:
                print(f'Wrote {count} lines')


        print(f'Total {count} lines written')

        f.flush()
        f.seek(0)

        storage_client = storage.Client()
        bucket = storage_client.get_bucket(args.bucket_name)
        blob = bucket.blob(args.object_name)
        blob.upload_from_file(f)

        print(f'File uploaded to {args.bucket_name}/{args.object_name}')





if __name__ == '__main__':
    main()