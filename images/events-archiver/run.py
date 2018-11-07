#!/usr/bin/env python3
from datetime import datetime, timedelta
import time
import os

from archiver import archive_events
from indexer import index_events

project_name = os.environ['PROJECT_NAME']
log_name = 'binderhub-events-text'
source_bucket = os.environ['SOURCE_BUCKET']
destination_bucket = os.environ['DESTINATION_BUCKET']


while True:
    now = datetime.utcnow()

    if now.hour < 5:
        # For first 5h of the day, archive yesterday's events too.
        # Stackdriver pushes out logs to GCS once every hour, and we run archiver every 2h.
        # Running last day's for first 5h makes sure we catch last day's events, even if an
        # archiving run is disrupted for any reason
        yesterday = now - timedelta(days=1)
        print("Archiving yesterday's events {}".format(yesterday.strftime('%Y-%m-%d')))
        archive_events(
            project=project_name,
            log_name=log_name,
            source_bucket=source_bucket,
            destination_bucket=destination_bucket,
            date=yesterday
        )

    print("Archiving today's events {}".format(now.strftime('%Y-%m-%d')))
    archive_events(
        project=project_name,
        log_name=log_name,
        source_bucket=source_bucket,
        destination_bucket=destination_bucket,
        date=now
    )

    print("Generating index")
    index_events(project_name, destination_bucket)
    print('Sleeping for 2h')
    time.sleep(2 * 60 * 60)