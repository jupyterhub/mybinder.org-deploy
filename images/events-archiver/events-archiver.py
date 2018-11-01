"""
Read event logs from stackdriver & export them to Google Cloud Storage
"""
from datetime import datetime
import time
import json
import argparse
from dateutil.parser import parse
from google.cloud import logging


def fetch_events(project, log_name, start_time, end_time):
    client = logging.Client()
    filter = f"""
    logName="projects/{project}/logs/{log_name}" AND
    timestamp >= "{start_time}" AND timestamp <= "{end_time}"
    """

    for page in client.list_entries(filter_=filter).pages:
        for entry in page:
            yield json.loads(entry.payload['message'])
        time.sleep(10)

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'project',
        help='Name of the GCP project to read logs from'
    )
    argparser.add_argument(
        'log-name',
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

    args = argparser.parse_args()

    for event in fetch_events(
        'binder-prod', 'binderhub-events-text',
        parse(args.start_time).isoformat() + 'Z', parse(args.end_time).isoformat() + 'Z'
    ):
        print(event)

if __name__ == '__main__':
    main()