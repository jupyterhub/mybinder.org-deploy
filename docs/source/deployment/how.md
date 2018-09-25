# How to deploy a change to mybinder.org?

This document explains **how** to deploy a change to mybinder.org.
For information on what exactly a deployment does, see [what](what.html).

When a new change has landed in either [BinderHub](https://github.com/jupyterhub/binderhub)
or [repo2docker](https://github.com/jupyter/repo2docker), they need to be explicitly
deployed to mybinder.org for users to benefit from them. This is the most common kind of
change deployed to mybinder.org.

The first two sections of this page cover how to upgrade either `repo2docker` or
`BinderHub`.

## Updating BinderHub

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the BinderHub repo.

BinderHub is deployed via a helm chart that is tied to a particular commit on the
BinderHub repository. BinderHub is a "requirement" for this mybinder.org deployment,
which is why it is specified in `mybinder/requirements.yaml`. Upgrading the version of BinderHub
that is used in mybinder.org corresponds to updating the BinderHub helm chart version,
which we step through below.

1. Merge changes to BinderHub.
2. Open the [branches page for the BinderHub travis account](https://travis-ci.org/jupyterhub/binderhub/branches).
3. Click on the number for the latest build on "Master". It will say "#NNN passed".
4. You'll see a list of builds that have been run on this branch. Click on the `TEST=helm` job.
5. If the build succeeds (is green), a new helm chart for BinderHub will automatically
   be published and listed on GitHub. Go to the [BinderHub Helm Chart](https://jupyterhub.github.io/helm-chart/#development-releases-binderhub)
   page and grab the hash for the latest published version (at the top).

       binderhub-<version-number>-<hash-name>

   You want to copy `<hash-name>`. It will look something like
   example, it is `f87ac35`.

6. In your fork of the [mybinder.org-deploy](https://github.com/jupyterhub/mybinder.org-deploy)
   repository, open `mybinder/requirements.yaml`.
7. Toward the end of the file, you will see lines similar to:

      - name: binderhub
        version: 0.1.0-9692255
        repository: https://jupyterhub.github.io/helm-chart

   COPY the *old* hash value (above, it is `9692255`) and keep it for later.
   Replace the existing hash that comes just after the `-` under 'version' with new hash
   from step 3. In this example, replace `9692255`  with the hash `f87ac35`that you've
   copied in step 3. The edited lines will be:

      - name: binderhub
        version: 0.1.0-fbf6e5a
        repository: https://jupyterhub.github.io/helm-chart

8. Merge this change to `mybinder/requirements.yaml` into the mybinder.org-deploy
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
3. Click on the number for the latest build on "Master". It will say "#NNN passed".
4. You'll see a list of builds that have been run on this branch. Click on the
   build underneath the **Deploy** section.
5. You'll see the logs for this build. Scroll down and find the text:

       Pushed new repo2docker image: <YOUR-IMAGE-NAME>

   Copy the text in `<YOUR-IMAGE-NAME>`. **Note**: You may need to unfold the
   code in the `Deploying application` line in order to see this text.
6. In your fork of the mybinder.org-deploy repository, open
   `mybinder/values.yaml`.
7. Somewhere in the file you will see `repo2dockerImage`, it will look like
   this:
   
       repo2dockerImage: jupyter/repo2docker:65d5411
   
   COPY the *old* hash value (above, it is `65d5411`) and keep it for later.
8. Replace the *old* hash that is there with what you copied in step 2.
   For example, the edited file will look similar to:

       repo2dockerImage: jupyter/repo2docker:<YOUR-NEW-HASH>

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
3. Make a PR to the `master` branch with the changes you want.
4. In the description of the PR, include a link to the *diff* between the old and new hashes
   for the repository we're updating. It should have the following form:
   
       https://github.com/jupyterhub/<REPO-NAME>/compare/<OLD-HASH>...<NEW-HASH>
       
   For example, this is what the link for a recent update to BinderHub looks like:
   
       https://github.com/jupyterhub/binderhub/compare/3c21fde...af0d09e
       
5. Review, accept, and merge this PR. This will make Travis deploy the changes
   to [staging.mybinder.org](https://staging.mybinder.org), and run tests in the `tests/`
   directory against it. **In this case, you can merge your own PR**. Note that if the
   PR is a large change to the Kubernetes setup, this may take some time, and Travis may
   time-out in the process. If this happens and you _expect_ it to happen, you can restart
   travis a few times.
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
   Currently you cannot deploy changes to `mybinder/requirements.yaml` only to staging.
```
Sometimes you want to test out a deployment live before you make a deployment
to `prod`. This is possible by editing `staging`-only config files. To deploy
to staging only, follow these steps:

1. Make changes to [`config/staging.yaml`](https://github.com/jupyterhub/mybinder.org-deploy/blob/master/config/staging.yaml)
   on your fork. This file contains configuration for Helm that will **override**
   whatever is in `mybinder/values.yaml`.
2. Make a PR to the `master` branch, and review, accept, and merge this PR.
   **In this case, you can merge your own PR**.
   This will make Travis deploy the changes
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
