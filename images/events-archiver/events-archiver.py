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
        'source_bucket',
        help='GCS bucket to read exported stackdriver events from'
    )

    argparser.add_argument(
        'destination_bucket',
        help='GCS bucket to write archived events to'
    )

    argparser.add_argument(
        '--date',
        help='Date to archive events for. Defaults to today',
        type=parse,
        default=datetime.utcnow().isoformat()
    )

    argparser.add_argument(
        '--object-name-template',
        help='Template to use when outputting archived events. {date} is substituted',
        default='events-{date}.jsonl'
    )

    args = argparser.parse_args()


    storage_client = storage.Client()
    src_bucket = storage.Bucket(storage_client, args.source_bucket)
    dest_bucket = storage.Bucket(storage_client, args.destination_bucket)


    prefix = args.log_name + '/' + args.date.strftime('%Y/%m/%d')
    print(f'Finding blobs with prefix {prefix}')
    src_blobs = src_bucket.list_blobs(prefix=prefix)

    count = 0
    with tempfile.TemporaryFile(mode='w+') as out:
        for src_blob in src_blobs:
            with tempfile.TemporaryFile(mode='wb+') as temp:
                src_blob.download_to_file(temp)
                temp.seek(0)

                for line in temp:
                    event = json.loads(line)['jsonPayload']['message']
                    out.write(event + '\n')
                    count += 1

        out.seek(0)
        blob_name = args.object_name_template.format(date=args.date.strftime('%Y-%m-%d'))
        blob = dest_bucket.blob(blob_name)
        blob.upload_from_file(out)
        print(f'Uploaded {args.destination_bucket}/{blob_name} with {count} events')


if __name__ == '__main__':
    main()