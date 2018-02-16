# How to deploy a change to mybinder.org?

This document explains **how** to deploy a change to mybinder.org.
For information on what exactly a deployment does, see [what](what.html).

## Proposing a change

When a new change has landed in either [BinderHub](https://github.com/jupyterhub/binderhub)
or [repo2docker](https://github.com/jupyter/repo2docker), they need to be explicitly
deployed to mybinder.org for users to benefit from them. This is the most common kind of
change deployed to mybinder.org.

### BinderHub updates

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the BinderHub repo.

BinderHub is deployed via a helm chart that is tied to a particular commit on the
BinderHub repository. BinderHub is a "requirement" for this mybinder.org deployment,
which is why it is specified in `mybinder/requirements.yaml`. Upgrading the version of BinderHub
that is used in mybinder.org corresponds to updating the BinderHub helm chart version,
which we step through below.

1. Merge changes to BinderHub.
2. Open the [Travis build for BinderHub](https://travis-ci.org/jupyterhub/binderhub),
   navigate to the page corresponding to the master branch, `TEST=helm` job.
3. If the build succeeds, grab the hash that is displayed at the end of the
   travis output. It looks something like:

       Successfully packaged chart and saved it to: gh-pages/binderhub-0.1.0-f87ac35.tgz

   The hash is the string at the very end, between `-` and `.tgz`. In this
   example, it is `f87ac35`.

   ```eval_rst
   .. image:: travis-screenshot.png
   ```

4. In your fork of the [mybinder.org-deploy][https://github.com/jupyterhub/mybinder.org-deploy]
   repository, open `mybinder/requirements.yaml`.
5. Toward the end of the file, you will see lines similar to:

      - name: binderhub
        version: 0.1.0-9692255
        repository: https://jupyterhub.github.io/helm-chart

   Replace the existing hash that comes just after the `-` under 'version' with new hash
   from step 3. In this example, replace `9692255`  with the hash `f87ac35`that you've
   copied in step 3. The edited lines will be:

      - name: binderhub
        version: 0.1.0-fbf6e5a
        repository: https://jupyterhub.github.io/helm-chart

6. Merge this change to `mybinder/requirements.yaml` into the mybinder.org-deploy
   repository following the steps in the [Deploying a change][#deploying-a-change] section
   to deploy the change.

### repo2docker updates

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the [repo2docker](https://github.com/jupyterhub/repo2docker) repo.

BinderHub uses a docker image with repo2docker in it. When a new commit is merged in
the repo2docker repository, a new version of this image is pushed. We then configure
BinderHub to use the newly built image (which is identified by a tag) by editing `values.yaml`.
The following lines describe how to point mybinder.org to the new repo2docker image

1. Merge changes to repo2docker.
2. Open the [Travis build for repo2docker](https://travis-ci.org/jupyter/repo2docker),
   and find the build for the job marked as 'deploy'. In the logs for that, find the text:

       Pushed new repo2docker image: <YOUR-IMAGE-NAME>

   Copy the text in `<YOUR-IMAGE-NAME>`. **Note**: You may need to unfold the
   code in the `Deploying application` line in order to see this text.
3. In your fork of the mybinder.org-deploy repository, open
   `mybinder/values.yaml`.
4. Somewhere in the file you will see `repo2dockerImage`, replace the
   text that is there with what you copied in step 2. For example, the
   edited file will look similar to:

       repo2dockerImage: jupyter/repo2docker:65d5411

5. Merge this change to `mybinder/values.yaml` into the mybinder.org-deploy
   repository following the steps in the [Deploying a change][#deploying-a-change] section
   to deploy the change.

## Deploying a change

### Deploying to *both* `staging` then `prod`

Deploying a change involves making a PR with your desired change and merging it to
master.

1. Make the [changes](#upgrading-dependencies-for-the-mybinderorg-deployment) on your fork.
2. Make a PR to the `master` branch with the changes you want.
3. Review, accept, and merge this PR. This will make Travis deploy the changes
   to [staging.mybinder.org](https://staging.mybinder.org), and run tests in the `tests/`
   directory against it.
4. If the tests succeed, the change will be deployed to mybinder.org.
5. If the tests fail, the change will *not* be deployed to mybinder.org.
   The deployer must then investigate why it failed. **If they can
   not figure out a cause in about 10 minutes, revert the change.**
   The build should not remain broken for more than ten minutes.
6. Troubleshoot and make changes to your fork. Repeat the process from Step 1.

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

The [what](what.html) document has more details on common ways deployments can go
wrong, and how to debug them.
