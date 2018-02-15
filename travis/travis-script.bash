#!/bin/bash
set -euo pipefail
# Used by travis to trigger deployments
# Keeping this here rather than make travis.yml too complex
# We deploy to staging, run some automated tests, and if they pass we deploy to production!

# Colors we gonna use for colored output
GREEN='\033[0;32m'
NC='\033[0m' # NC turns off colors


printf "${GREEN}Starting deployment process${NC}"

# Unlock our secret files!
# Travis allows encrypting only one file per repo (boo) so we use it to
# encrypt our git-crypt key
openssl aes-256-cbc -K $encrypted_510e3970077d_key -iv $encrypted_510e3970077d_iv -in travis/crypt-key.enc -out travis/crypt-key -d
git-crypt unlock travis/crypt-key
# ensure private keys have private permissions,
# otherwise ssh will ignore them
chmod 0600 secrets/*key
printf "${GREEN}SUCCESS: Decrypted secrets required for deployment${NC}"

# Make sure we have our helm repo!
helm init --client-only
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart
helm repo update
cd mybinder && helm dep up && cd ..
printf "${GREEN}SUCCESS: Set up helm chart repository${NC}"

function deploy {
    KIND="${1}"
    CLUSTER="${2}"
    BINDER_URL="${3}"
    HUB_URL="${4}"

    printf "${GREEN}Starting deployment to: ${KIND}${NC}"

    # Authenticate to gcloud & get it to authenticate to kubectl!
    gcloud auth activate-service-account --key-file=secrets/gke-auth-key-${KIND}.json
    gcloud container clusters get-credentials ${CLUSTER} --zone=us-central1-a --project=binder-${KIND}

    printf "${GREEN}SUCCESS: Credentials for deploying to ${KIND} activated${NC}"

    python3 ./deploy.py deploy ${KIND}

    printf "${GREEN}SUCCESS: Deployment push to ${KIND} completed${NC}"
    printf "${GREEN}Running tests to validate deployment...${NC}"
    # Run some tests to make sure we really did pass!
    py.test --binder-url=${BINDER_URL} --hub-url=${HUB_URL}
    printf "${GREEN}SUCCESS: Deployment to ${KIND} completed and verified!${NC}"
}

deploy "staging" "staging" https://staging.mybinder.org https://hub.staging.mybinder.org

deploy "prod" "prod-a" https://mybinder.org https://hub.mybinder.org