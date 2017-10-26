#!/bin/bash
set -euo pipefail
# Used by travis to trigger deployments
# Keeping this here rather than make travis.yml too complex

TARGET="${TRAVIS_BRANCH}"

echo "Starting deploy..."

# Unlock our secret files!
# Travis allows encrypting only one file per repo (boo) so we use it to
# encrypt our git-crypt key
openssl aes-256-cbc -K $encrypted_510e3970077d_key -iv $encrypted_510e3970077d_iv -in travis/crypt-key.enc -out travis/crypt-key -d
git-crypt unlock travis/crypt-key


# Authenticate to gcloud & get it to authenticate to kubectl!
gcloud auth activate-service-account --key-file=secrets/gke-auth-key-${TARGET}.json
gcloud container clusters get-credentials ${TARGET} --zone=us-central1-a --project=binder-${TARGET}


# Make sure we have our helm repo!
helm init --client-only
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/

python3 ./deploy.py deploy ${TARGET}

# Run some tests to make sure we really did pass!
py.test --binder-url=https://${TARGET}.mybinder.org --hub-url=https://hub.${TARGET}.mybinder.org tests/

echo "Done!"
