#!/bin/bash
set -euo pipefail
# Used by travis to trigger deployments
# Keeping this here rather than make travis.yml too complex

echo "Starting deploy..."

# Unlock all our secrets!
# Note that this has to be a tarball, since travis only allows encrypting
# *one* file per repo!
openssl aes-256-cbc -K $encrypted_510e3970077d_key -iv $encrypted_510e3970077d_iv -in travis/deploy-secrets.tar.gz.enc -out travis/deploy-secrets.tar.gz -d
tar xvf travis/deploy-secrets.tar.gz

# Authenticate to gcloud & get it to authenticate to kubectl!
gcloud auth activate-service-account --key-file=deploy-secrets/google-auth-key.json
gcloud container clusters get-credentials binder-hub --zone=us-central1-a --project=binder-testing

# Unlock our secret files!
git-crypt unlock deploy-secrets/crypt-key

# Make sure we have our helm repo!
helm init --client-only
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/

python3 ./deploy.py deploy ${TRAVIS_BRANCH}

# Run some tests to make sure we really did pass!
py.test --binder-url=https://${TRAVIS_BRANCH}.mybinder.org --hub-url=https://hub.${TRAVIS_BRANCH}.mybinder.org tests/

echo "Done!"
