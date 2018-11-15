#!/usr/bin/env python3
from datetime import datetime, timedelta
import time
import os
import json

from archiver import archive_events
from indexer import index_events

with open('/etc/analytics-publisher/analytics-publisher.json') as f:
    config = json.load(f)

project_name = config['project']

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
            log_name=config['events']['logName'],
            source_bucket=config['events']['sourceBucket'],
            destination_bucket=config['events']['destinationBucket'],
            date=yesterday
        )

    print("Archiving today's events {}".format(now.strftime('%Y-%m-%d')))
    archive_events(
        project=project_name,
        log_name=config['events']['logName'],
        source_bucket=config['events']['sourceBucket'],
        destination_bucket=config['events']['destinationBucket'],
        date=now
    )

    print("Generating index")
    index_events(project_name, config['events']['destinationBucket'])
    print('Sleeping for 2h')
    time.sleep(2 * 60 * 60)