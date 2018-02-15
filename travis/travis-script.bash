#!/bin/bash
set -euo pipefail
# Used by travis to trigger deployments
# Keeping this here rather than make travis.yml too complex
# We deploy to staging, run some automated tests, and if they pass we deploy to production!

# Colors we gonna use for colored output
GREEN=$(tput setaf 2)
BOLD=$(tput bold)
BOLDGREEN="${BOLD}${GREEN}"
NC=$(tput sgr0) # Reset to default

echo -e "${BOLDGREEN}Starting deployment process${NC}"

function deploy {
    KIND="${1}"
    CLUSTER="${2}"
    BINDER_URL="${3}"
    HUB_URL="${4}"

    echo -e "${BOLDGREEN}Starting deployment to: ${KIND}${NC}"

    # Authenticate to gcloud & get it to authenticate to kubectl!
    gcloud auth activate-service-account --key-file=secrets/gke-auth-key-${KIND}.json
    gcloud container clusters get-credentials ${CLUSTER} --zone=us-central1-a --project=binder-${KIND}

    echo -e "${BOLDGREEN}SUCCESS: Credentials for deploying to ${KIND} activated${NC}"

    python3 ./deploy.py ${KIND}

    echo -e "${BOLDGREEN}SUCCESS: Deployment push to ${KIND} completed${NC}"
    echo -e "${BOLDGREEN}Running tests to validate deployment...${NC}"
    # Run some tests to make sure we really did pass!
    py.test --binder-url=${BINDER_URL} --hub-url=${HUB_URL}
    echo -e "${BOLDGREEN}SUCCESS: Deployment to ${KIND} completed and verified!${NC}"
}

deploy "staging" "staging" https://staging.mybinder.org https://hub.staging.mybinder.org

deploy "prod" "prod-a" https://mybinder.org https://hub.mybinder.org