# How to deploy a change to mybinder.org?

This document explains **how** to deploy a change to mybinder.org.
For information on what exactly a deployment does, see [what](what.html).

When a new change has landed in either [BinderHub](https://github.com/jupyterhub/binderhub)
or [repo2docker](https://github.com/jupyter/repo2docker), they need to be explicitly
deployed to mybinder.org for users to benefit from them. This is the most common kind of
change deployed to mybinder.org.

The first two sections of this page cover how to upgrade either `repo2docker` or
`BinderHub`.

```eval_rst
.. note::
   Currently upgrades to BinderHub and repo2docker are automatically managed
   by the fantastic `henchbot <https://github.com/henchbot/mybinder.org-upgrades>`_ and manual intervention is rarely required.
   However, we have left the manual steps here for provenance or in case of emergency.
```

## Deployment policy

Deployments to mybinder.org should be:

1. **Safe**. We will have good, user friendly tooling + lots of safeguards,
so people can deploy without fear of accidentally breaking the site.

2. **Straightforward**. We want a lot of people to be involved in maintaining mybinder.org,
so we must make sure deployments are also easy to do. Most deployments should
not require specific sysadmin knowledge.

3. **Timely**. We deploy changes to repo2docker and BinderHub within a few days of
them being merged into master.

These are all **aspirational** - we strive for hitting the above points,
but recognize that work and life may get in the way of doing this perfectly.

## Updating BinderHub

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the BinderHub repo.

BinderHub, the Helm chart, is a dependency for the local `mybinder` Helm chart.
The version of the BinderHub Helm chart is declared in `mybinder/Chart.yaml`.
Upgrading the version of BinderHub that is used in mybinder.org corresponds to
updating the BinderHub Helm chart version, which we step through below.

1. Merge changes to BinderHub.
2. Open the [branches page for the BinderHub travis account](https://travis-ci.org/jupyterhub/binderhub/branches).
3. Wait for the build for your PR merge to pass (it will say "#NNN passed").
   If it does, then continue to step 4. If it doesn't, take a look at the error message, and debug as needed
   until they pass.
4. Run the `list_new_commits.py` script in the `scripts/` of the
   `mybinder.org-deploy` repository. It will output something like the following:

       ---------------------

       BinderHub: https://github.com/jupyterhub/binderhub/compare/<OLD-HASH>...<NEW-HASH>
       repo2docker: https://github.com/jupyter/repo2docker/compare/<OLD-HASH>...<NEW-HASH>
       JupyterHub: https://github.com/jupyterhub/zero-to-jupyterhub-k8s/compare/<OLD-HASH>...<NEW-HASH>

       ---------------------

   Since you are updating BinderHub, copy the text in `<NEW-HASH>` for the
   line that refers to BinderHub. This is the name of the new BinderHub image.
   We'll now update the config to refer to this image.

5. In your fork of the [mybinder.org-deploy](https://github.com/jupyterhub/mybinder.org-deploy)
   repository, open `mybinder/Chart.yaml`.
6. Toward the end of the file, you will see lines similar to:

      - name: binderhub
        version: 0.2.0-n454.h97fb8c3
        repository: https://jupyterhub.github.io/helm-chart

   Where `97fb8c3` following `.h`, a prefix for hash, is the same value printed
   in `<OLD-HASH>` above.

   Replace this hash with the text in `<NEW-HASH>` above. For example, in the
   above case, we'll replace it with the new hash.

      - name: binderhub
        version: 0.2.0-n457.hdc3df7f
        repository: https://jupyterhub.github.io/helm-chart

7. Merge this change to `mybinder/Chart.yaml` into the mybinder.org-deploy
   repository following the steps in the [Deploying a change](#deploying-a-change) section
   to deploy the change.


## Updating repo2docker

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the [repo2docker](https://github.com/jupyterhub/repo2docker) repo.

BinderHub uses a docker image with repo2docker in it. When a new commit is merged in
the repo2docker repository, a new version of this image is pushed. We then configure
BinderHub to use the newly built image (which is identified by a tag) by editing `values.yaml`.
The following lines describe how to point mybinder.org to the new repo2docker image

1. Merge changes to repo2docker.
2. Open the [branches page for repo2docker](https://travis-ci.org/jupyter/repo2docker/branches).
   And click on the number for the latest build on "Master".
3. Wait for the build for your PR merge to pass (it will say "#NNN passed").
   If it does, then continue to step 4. If it doesn't, take a look at the error message, and debug as needed
   until they pass.
4. Run the `list_new_commits.py` script in the `scripts/` of the
   `mybinder.org-deploy` repository. It will output something like the following:

       ---------------------

       BinderHub: https://github.com/jupyterhub/binderhub/compare/<OLD-HASH>...<NEW-HASH>
       repo2docker: https://github.com/jupyter/repo2docker/compare/<OLD-HASH>...<NEW-HASH>
       JupyterHub: https://github.com/jupyterhub/zero-to-jupyterhub-k8s/compare/<OLD-HASH>...<NEW-HASH>

       ---------------------

   Since you are updating repo2docker, copy the text in `<NEW-HASH>` for the
   line that refers to repo2docker. This is the name of the new repo2docker image.
   We'll now update the config to refer to this image.

5. In your fork of the mybinder.org-deploy repository, open
  `mybinder/values.yaml`.
6. Somewhere in the file you will see `repo2dockerImage`, it will look like
   this:

       BinderHub:
         build_image: jupyter/repo2docker:65d5411

   Where `65d5411` is the same value in `<OLD-HASH>` above.

7. Replace the *old* hash that is there with what you copied in step 4.
   For example, the edited file will look similar to:

       BinderHub:
         build_image: jupyter/repo2docker:<NEW-HASH>

8. Merge this change to `mybinder/values.yaml` into the mybinder.org-deploy
   repository following the steps in the [Deploying a change](#deploying-a-change) section
   to deploy the change.


## Deploying a change

### Deploying to *both* `staging` then `prod`

Deploying a change involves making a PR with your desired change and merging it to
master.

1. Make the changes as described above [on your fork of this repo](https://github.com/jupyterhub/mybinder.org-deploy).
2. Keep track of the **hashes** that were updated. You should have both the *old* hash that
   was replaced, and the *new* hash that replaced it.
3. If you haven't already, run the `list_new_commits.py` script in the `scripts/`
   folder. This will print out a URL that describes the changes made to both
   BinderHub and repo2docker.
4. Make a PR to the `master` branch with the changes you want.

    * Name the PR like so: `<TOOL-CHANGED>: <OLD-HASH>...<NEW-HASH>`
    * In the description of the PR, paste the full URL that you printed out
      `list_new_commits.py`. It should have the following form:

          https://github.com/jupyterhub/<REPO-NAME>/compare/<OLD-HASH>...<NEW-HASH>

5. Review, accept, and merge this PR. This will make GitHub Actions deploy the changes
   to [staging.mybinder.org](https://staging.mybinder.org), and run tests in the `tests/`
   directory against it. **In this case, you can merge your own PR**. Note that if the
   PR is a large change to the Kubernetes setup, this may take some time, and GitHub Actions may
   time-out in the process. If this happens and you _expect_ it to happen, you can restart
   the build a few times.
6. If the tests succeed, the change will be deployed to mybinder.org.
7. If the tests fail, the change will *not* be deployed to mybinder.org.
   You must then investigate why it failed. **If you can
   not figure out a cause in about 10 minutes, revert the change.**
   You can revert the change with [the GitHub UI](https://help.github.com/articles/reverting-a-pull-request/) and immediately
   merge the reversion PR that GitHub creates.
8. Troubleshoot and make changes to your fork. Repeat the process from Step 1.

### Deploying to *only* `staging`

```eval_rst
.. note::
    Currently, only pull requests from a branch on the `jupyterhub/mybinder.org-deploy` repo
    can be deployed to staging, not pull requests from forks.
```

Sometimes you want to test out a deployment live before you make a deployment
to `prod`.

This simplest way to achieve this is to apply the `test-staging` label to an open PR. This will trigger GitHub Actions to deploy the changes in the PR to the staging cluster **only**.

```eval_rst
.. note::
   If you need to re-deploy the changes in a PR to staging only, then the label will need to be removed and then re-added.
```

Another way to achieve this is by editing `staging`-only config files. To deploy
to staging only, follow these steps:

1. Make changes to [`config/staging.yaml`](https://github.com/jupyterhub/mybinder.org-deploy/blob/master/config/staging.yaml)
   on your fork. This file contains configuration for Helm that will **override**
   whatever is in `mybinder/values.yaml`.
2. Make a PR to the `master` branch, and review, accept, and merge this PR.
   **In this case, you can merge your own PR**.
   This will make GitHub Actions deploy the changes
   to [staging.mybinder.org](https://staging.mybinder.org), and run tests in the `tests/`
   directory against it. Because we've only edited `staging.yaml`, **it will not
   be deployed to `prod`**.
3. If the tests succeed, you can check out the new behavior at `staging.mybinder.org`.
4. If the tests fail, the deployer must investigate why it failed. **If they can
   not figure out a cause in about 10 minutes, revert the change.**
   The build should not remain broken for more than ten minutes.
5. Troubleshoot and make changes to your fork. Repeat the process from Step 1.
6. If you are satisfied with these changes, **revert** the change to `config/staging.yaml`,
   and **apply** those same changes to `mybinder/values.yaml`. Now follow the
   steps in the section above to deploy to **both** `staging` and `prod`.

The [what](./what.html) document has more details on common ways deployments can go
wrong, and how to debug them.


## Changing the mybinder.org infrastructure

Sometimes we need to make changes to the mybinder.org core infrastructure.
These are changes to the infrastructure that don't directly touch binderhub or
repo2docker, and often require more expertise. Examples for these include:

1. Upgrading nginx Ingress controller
2. Re-configuring our prometheus servers
3. Upgrading to a new JupyterHub release
4. Re-configuring autoscaling for the cluster
5. Doing a kubernetes master upgrade.

These changes require a different kind of review than deploying code. In this
case, ensure that you have a fellow member of the mybinder.org operations
team to assist in case something goes wrong.
