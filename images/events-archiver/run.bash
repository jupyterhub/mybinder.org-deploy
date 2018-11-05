#!/bin/bash

set -eu

while true
do
    python3 events-archiver.py \
            ${PROJECT_NAME} \
            binderhub-events-text \
            ${SOURCE_BUCKET} \
            ${DESTINATION_BUCKET}
    python3 events-indexer.py \
            ${PROJECT_NAME} \
            ${DESTINATION_BUCKET}
    sleep 2h
done