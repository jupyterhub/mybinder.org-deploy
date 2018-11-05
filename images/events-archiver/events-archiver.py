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


def process_event(event):
    """
    Post process event if needed.

    Takes in a dict representing event, returns dict back.
    """
    if 'timestamp' in event:
        # Trim timestamp to minute resolution before making public
        # Should hopefully make it harder to de-anonymize users by observing timing
        event['timestamp'] = parse(event['timestamp']).replace(
            second=0, microsecond=0
        ).isoformat() + 'Z'
    return event


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
    src_bucket = storage.Bucket(storage_client, args.source_bucket)
    dest_bucket = storage.Bucket(storage_client, args.destination_bucket)


    prefix = args.log_name + '/' + args.date.strftime('%Y/%m/%d')
    print(f'Finding blobs with prefix {prefix}')
    src_blobs = src_bucket.list_blobs(prefix=prefix)

    count = 0
    all_events = []
    for src_blob in src_blobs:
        with tempfile.TemporaryFile(mode='wb+') as temp:
            src_blob.download_to_file(temp)
            temp.seek(0)

            for line in temp:
                event = process_event(json.loads(json.loads(line)['jsonPayload']['message']))
                if args.debug:
                    print(event)
                if not args.dry_run:
                    all_events.append(event)
                count += 1

    if not args.dry_run:
        # Timestamp is ISO8601 in UTC, so can be sorted lexicographically
        all_events.sort(key=lambda event: event['timestamp'])
        with tempfile.TemporaryFile(mode='w+') as out:
            for event in all_events:
                out.write(json.dumps(event) + '\n')
            out.seek(0)
            blob_name = args.object_name_template.format(date=args.date.strftime('%Y-%m-%d'))
            blob = dest_bucket.blob(blob_name)
            # Set metadata on the object so we know when this archive is for & how many events there are
            blob.metadata = {
                'Events-Date': args.date.strftime('%Y-%m-%d'),
                'Events-Count': len(all_events)
            }
            blob.upload_from_file(out)
            print(f'Uploaded {args.destination_bucket}/{blob_name} with {count} events')


if __name__ == '__main__':
    main()