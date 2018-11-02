#!/bin/bash

set -eu

while true
do
    python3 events-archiver.py \
            ${PROJECT_NAME} \
            binderhub-events-text \
            ${SOURCE_BUCKET} \
            ${DESTINATION_BUCKET} \
    sleep 2h
done