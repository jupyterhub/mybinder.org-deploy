#!/bin/bash

set -eu

while true
do
    python3 events-archiver.py \
            ${PROJECT_NAME} \
            binderhub-events-text \
            mybinder-events-raw-export \
            mybinder-events-archive
    sleep 2h
done