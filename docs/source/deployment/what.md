# What does a MyBinder.org deployment do?

This document tries to explain _what_ is going on when a deployment
to mybinder.org happens. For _how_ to do a deploy, please see [how](how).

The deployment happens in various **stages**, each of which comprise of
a series of **steps**. Each step of the deployment is
controlled by `.travis.yml`, which should be considered the authoritative
source of truth for deployment. _If this document disagrees with it,`.travis.yml` is correct!_

If any of the steps in any stage fails, all following steps
are canceled and the deployment is marked as failed.

## Stage 1: Installing deployment tools

### Step 1: Install all the things!

#### Background

Deployment requires the following tools to be installed. Note:
since deployments are handled with _Travis CI_, you don't
need them on your local computer.

1. [`gcloud`](https://cloud.google.com/sdk/)

   mybinder.org currently runs on [Google Cloud](https://cloud.google.com)
   in a [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine/)
   cluster. We need `gcloud` to authenticate ourselves to this cluster.

2. [`helm`](https://helm.sh)

   `helm` is the package manager for Kubernetes. We use this for actually installing
   and upgrading the various components running mybinder.org (BinderHub, JupyterHub,
   extra mybinder.org-specific services, etc)

3. [`kubectl`](https://kubernetes.io/docs/reference/kubectl/)

   `kubectl` is the canonical command line client for interacting with the Kubernetes
   API. We primarily use it to explicitly wait for our deployment to complete
   before running our tests.

4. [`pytest`](https://docs.pytest.org)

   We use `pytest` to verify that our deployment successfully completed, by running
   a series of end-to-end tests (present in the `tests/` directory) against the
   new deployment. This makes sure that both builds and launches are working,
   and is an important part of giving us confidence to do continuous deployment.

5. [`git-crypt`](https://github.com/AGWA/git-crypt)

   We have a bunch of secrets (in `secrets/`) in our deployment - things like
   cloud credentials, etc. We use `git-crypt` to keep them in this repository
   in an encrypted form. We use the [encrypted travis file](https://docs.travis-ci.com/user/encrypting-files/)
   for our repository to store the `git-crypt` decryption key.

#### What happens

- All of the tools above are installed. We use the `before_deploy` section
  in `.travis.yml` to install these, mostly so we get nice log folding. The only exception
  is the `pytest` installation - that is in the `install` section, so we can leverage
  [travis caching](https://docs.travis-ci.com/user/caching/) to speed up our deploys.

#### What could go wrong?

All **Stage 1** failures can be attributed to one of the following causes:

1. Network connections from Travis are being flaky, leading to failed installations

   This is the most likely cause of Stage 1 failures. When this happens, we have no choice
   but to restart the Travis Build.

   If a restart also fails, there are two possible reasons:

   1. Travis is having some infrastructure issues. Check the [Travis Status Page](https://www.traviscistatus.com/)
      to see if this is the case.
   2. The method we are using to install any of these bits of software is
      having issues - either it no longer works due to some changes to the software, or
      the software installer is depending on things that are having temporary difficulties.
      Look at which software installation is failing, and debug that!

2. The commit we are trying to deploy modified `.travis.yml`, and introduced a bug / typo.

   The person who wrote the PR modifying `.travis.yml` should debug what
   the error is and fix it in a subsequent PR.

## Stage 2: Configuring deployment tools

### Step 1: Decrypting secrets

#### Background

The following secrets are present in encrypted form in the repository:

1. Secret config for the helm charts (under `secrets/config`). These contain various
   deployment secrets for staging and prod, such as proxy tokens, registry authentication,
   etc.
2. [Google Cloud Service Accounts](https://cloud.google.com/compute/docs/access/service-accounts)
   for both the staging and production Google cloud projects
   (as `secrets/gke-auth-key-staging.json` and `secrets/gke-auth-key-prod.json`).
   These have a [custom Role](https://cloud.google.com/iam/docs/understanding-roles)
   called `travis-deployer` that gives them _just_ the permissions needed to do
   deployments.
3. A [GitHub deploy key](https://developer.github.com/v3/guides/managing-deploy-keys/)
   for the [binderhub-ci-repos/cached-minimal-dockerfile](https://github.com/binderhub-ci-repos/cached-minimal-dockerfile)
   repo (as `secrets/binderhub-ci-repos-deploy-key`). This is used in our tests to force the
   deployed binderhub to do a build + launch, rather than just a launch (via
   `tests/test_build.py`)

The `git-crypt` symmetric key needed to decrypt these secrets is `travis/crypt-key.enc`,
encrypted with Travis's [encrypted file](https://docs.travis-ci.com/user/encrypting-files/)
support. Travis only supports one encrypted file per repo, and these are one-way encrypted
only (you can not get plain text back easily!), forcing us to use `git-crypt`.

#### What happens?

1. Decrypt the `git-crypt` key with the travis-provided `openssl` command
2. Decrypt all other secrets with the `git-crypt` key

At the end of this step, all the secrets required for a successful deployment
are available in unencrypted form.

#### What could go wrong?

1. Someone has used the `travis encrypt-file` command for this repository, overwriting
   the current travis encryption key (which is used to decrypt the `git-crypt` encryption
   key), and committed this change. This causes issues because `travis encrypt-file`
   can only encrypt one file per repo, so if you encrypt another file the first file
   becomes undecryptable.

   This will manifest as an error from the `openssl` command.

   The simplest fix is to revert the PR that encrypted another file. `git-crypt`
   should be used instead for encrypting additional files.

### Step 2: Setting up Helm

#### Background

We use _helm charts_
to configure mybinder.org. We use charts both from the
[official kubernetes charts repository](https://github.com/helm/charts),
as well as the [JupyterHub charts repository](https://jupyterhub.github.io/helm-chart).

#### What happens

To set up helm to do the deployment, we do the following:

1. Set up the helm client, allowing it to create the local config files it needs
   to function.
2. Set up the JupyterHub charts repository for use with this helm installation,
   and fetch the latest chart definitions.
3. Fetch all the dependencies of the `mybinder` deployment chart with the versions
   specified in `mybinder/Chart.yaml`, and store them locally to ready them
   for deployment.

At the end of this step, `helm` has been fully configured to do deployment of our
charts.

#### What could go wrong?

1. Invalid version for a dependency in `mybinder/Chart.yaml`

   This manifests as an error from `helm dep up` that looks like the following:

   ```
   Error: Can't get a valid version for repositories <dependency>. Try changing the version constraint in Chart.yaml
   ```

   `<dependency>` in the above error message should point to the erroring dependency
   whose version needs to be fixed.

   If this happens for the **binderhub** dependency, the most common reason is that
   you have not waited long enough after merging a PR in the binderhub repo before
   bumping the version here. Make sure the version of binderhub is visible in
   https://jupyterhub.github.io/helm-chart before merging a PR here.

### Step 3: Tell Grafana our deployment is starting

We create an [annotation](https://grafana.com/docs/grafana/latest/dashboards/annotations/)
in Grafana, recording the fact that a deployment is starting.

This is very useful when looking at dashboards, since you can see
the effects of deployments in various metrics.

## Stage 3: Deploy to staging

We have a [staging environment](https://staging.mybinder.org) that is configured
exactly like production, but smaller (to control costs). We use this to test all
deployments before they hit the production mybinder.org website.

### Step 1: Set up and do the helm upgrade

#### What happens

We use the `deploy.py` script to do the helm deployment. This script does the
following:

1. Use the Google Cloud Service Accounts we decrypted in Stage 2, Step 1 to get
   a valid [~/.kube/config](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
   file. This file is used by both `helm` and `kubectl` to access the cluster.
2. Use `helm upgrade`
   to actually do the deployment. This deploys whatever changes the commit has -
   new chart versions, changes to configuration, new repo2docker version, etc.
   We have a ten minute timeout here.
3. We use `kubectl rollout` to wait for all [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
   and [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
   objects to be fully ready. Theoretically the `--wait` param to `helm upgrade` does
   this - but it is not complete enough for our use case.

Once we have verified that all the `Deployment` and `DaemonSet` objects are ready,
the helm deployment is complete!

#### What could go wrong?

1. YAML formatting issue in one of the config files

   YAML syntax can be finnicky sometimes, and fail in non-obvious ways. The most common
   error is the presence of tab characters in YAML, which will make them always fail.

   Learn X in Y Minutes also has a nice [guide on YAML](https://learnxinyminutes.com/docs/yaml/).
   You can also use [yamllint](https://github.com/adrienverge/yamllint) locally to validate
   your YAML files.

   Remember to **not** copy paste any secret files into online YAML Linting applications
   for linting! That could possibly compromise mybinder.org.

2. Kubernetes cluster is having difficulties

   This is usually manifested by either `helm` or `kubectl` reporting connection errors.

3. Bugs in helm itself

   Fairly rare, but bugs in helm itself might cause failure.

4. Severe bugs in the version of binderhub, jupyterhub or any of the dependencies deployed.

   This will usually manifest as a `kubectl rollout` command hanging forever. This is
   caused by a bug in the component that `kubectl rollout` is waiting for constantly
   crashing, unable to stay up.

   Looking at what component it is, and perhaps in the logs, would help!

### Step 2: Validate the deployment

#### What happens

We run the tests in `tests/` with `pytest` to validate that the deployment succeeded.
These try to be as thorough as possible, simulating the tests a human would do to
ensure that the site works as required.

Look at the docstrings in the files under [`tests/`](https://github.com/jupyterhub/mybinder.org-deploy/tree/master/tests)
to see what are the tests being run.

If all the tests succeed, we can consider the staging deployment success!

#### What could go wrong?

1. Bugs in the version of binderhub or jupyterhub deployed, causing any of the tests
   in `tests/` to fail.

   The output should tell you which test fails. You can look at the docstring for the
   failing test to understand what it is was testing, and debug from there.

## Stage 4: Deploy to production

After deploying to `staging` and validating it with tests, we have a reasonable amount of confidence
that it is safe to deploy to production. Production deploy has the exact same steps as
`staging`, but targets production (branch and namespace `prod`) instead of staging.
