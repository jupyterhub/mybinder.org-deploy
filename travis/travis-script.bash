#!/bin/bash
set -euo pipefail
# Used by travis to trigger deployments
# Keeping this here rather than make travis.yml too complex

TARGET="${TRAVIS_BRANCH}"

if [ "${TARGET}" = "prod" ]; then
    BINDER_URL="https://mybinder.org"
    HUB_URL="https://hub.mybinder.org"
    # Specify currently active cluster
    # FIXME: Deploy to multiple clusters?
    CLUSTER="prod-a"
else
    BINDER_URL="https://${TARGET}.mybinder.org"
    HUB_URL="https://hub.${TARGET}.mybinder.org"
    CLUSTER="${TARGET}"
fi

echo "Starting deploy..."

# Unlock our secret files!
# Travis allows encrypting only one file per repo (boo) so we use it to
# encrypt our git-crypt key
openssl aes-256-cbc -K $encrypted_510e3970077d_key -iv $encrypted_510e3970077d_iv -in travis/crypt-key.enc -out travis/crypt-key -d
git-crypt unlock travis/crypt-key
# ensure private keys have private permissions,
# otherwise ssh will ignore them
chmod 0600 secrets/*key


# Authenticate to gcloud & get it to authenticate to kubectl!
gcloud auth activate-service-account --key-file=secrets/gke-auth-key-${TARGET}.json
gcloud container clusters get-credentials ${CLUSTER} --zone=us-central1-a --project=binder-${TARGET}


# Make sure we have our helm repo!
helm init --client-only
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart

python3 ./deploy.py deploy ${TARGET}

# Run some tests to make sure we really did pass!
py.test --binder-url=${BINDER_URL} --hub-url=${HUB_URL}

echo "Done!"
