# Deploying mybinder.org

Deploying a change follows a two-phase process. First, you'll deploy to
the `staging` branch of the repository. Second, if all looks well, you'll
deploy to the `prod` (production) branch of the repository.

## Two-phase deployment process

1. Make the changes on your fork.
2. Make a PR to the `staging` branch with the changes you want.
3. Review, accept, and merge this PR. This will make Travis deploy the changes
   to [staging.mybinder.org][].
4. Go to [staging.mybinder.org][] to look at the changes.
5. Verify that [staging.mybinder.org][] works as intended. Please take your
   time to check that the change is working as expected.

**If the changes look correct:**

6. Make a new PR, merging [staging][] into the [prod][] branch.
7. Get this PR merged, and wait for Travis to make a deployment to [prod][].
8. Verify that [mybinder.org][] works as intended. Please take your
   time to check that the change is working as expected.
9. CELEBRATE! :tada:

**If the changes don't look correct, or there is an error:**

6. **Immediately revert the PR that was made to the [staging][] branch.**
7. Verify that [staging.mybinder.org][] is working as it was before the PR
   and revert.
8. Troubleshoot and make changes to your fork. Repeat the process from Step 1.

## Upgrading dependencies and making configuration changes

Upgrading dependencies used by [mybinder.org][] requires making changes
to the `config` files of repositories that are used to build the
[mybinder.org][] service.

The following sections cover how to do upgrade dependencies for [BinderHub][]
and [repo2docker][]. In each case, you'll need to deploy these changes by
following the steps above in [Two-phase deployment process][].

### Making changes to BinderHub

This section explains how to upgrade the [mybinder.org][] deployment after
making a change in the [BinderHub][] repo.

BinderHub is deployed via a helm chart that is tied to a particular commit on the
BinderHub repository. BinderHub is a "requirement" for this mybinder.org deployment,
which is why it is specified in requirements.yaml. Upgrading the version of BinderHub
that is used in mybinder.org corresponds to updating the BinderHub helm chart version,
which we step through below.

1. Merge changes to [BinderHub][].
2. Open the [Travis build for BinderHub](https://travis-ci.org/jupyterhub/binderhub),
   navigate to the page corresponding to the master branch.
3. If the build succeeds, grab the hash that is displayed at the end of the
   travis output. It looks something like:

       create mode 100644 binderhub-0.1.0-fbf6e5a.tgz

   The hash is the string at the very end, between `-` and `.tgz`. In this
   example, it is `fbf6e5a`.

   <img src="docs/static/travis-screenshot.png" width="500" />

4. In your fork of the [mybinder.org-deploy][] repository, open
   `mybinder/requirements.yaml`.
5. Toward the end of the file, you will see lines similar to:

      - name: binderhub
        version: 0.1.0-9692255
        repository: https://jupyterhub.github.io/helm-chart

   Replace the existing hash that comes just after the `-` under 'version' with new hash
   from step 3. In this example, replace `9692255`  with the hash `fbf6e5a`that you've
   copied in step 3. The edited lines will be:

      - name: binderhub
        version: 0.1.0-fbf6e5a
        repository: https://jupyterhub.github.io/helm-chart

6. Merge this change to `config/common.yaml` into the [mybinder.org-deploy][]
   repository following the steps in the [Deploying a change][] section above
   to deploy the change to [staging][], and then [prod][].

### Making changes to repo2docker

This section explains how to upgrade the [mybinder.org][] deployment after
making a change in the [repo2docker][] repo.

BinderHub uses a docker image with repo2docker in it. When a new commit is merged in
the repo2docker repository, a new version of this image is pushed. We then configure
BinderHub to use the newly built image (which is identified by a tag) by editing `values.yaml`.
The following lines describe how to point mybinder.org to the new repo2docker image

1. Merge changes to [repo2docker][].
2. Open the [Travis build for repo2docker](https://travis-ci.org/jupyter/repo2docker),
   find the text:

       Pushed new repo2docker image: <YOUR-IMAGE-NAME>

   Copy the text in `<YOUR-IMAGE-NAME>`. **Note**: You may need to unfold the
   code in the `Deploying application` line in order to see this text.
3. In your fork of the [mybinder.org-deploy][] repository, open
   `mybinder/values.yaml`.
4. Somewhere in the file you will see `repo2dockerImage`, replace the
   text that is there with what you copied in step 2. For example, the
   edited file will look similar to:

       repo2dockerImage: jupyter/repo2docker:65d5411

5. Merge this change to `mybinder/values.yaml` into the [mybinder.org-deploy][]
   repository following the steps in the [Deploying a change][] section above
   to deploy the change to [staging][], and then [prod][].


[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
[staging]: https://staging.mybinder.org
[BinderHub]: https://github.com/jupyterhub/binderhub
[binderhub]: https://github.com/jupyterhub/binderhub
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[repo2docker]: https://github.com/jupyter/repo2docker
[Two-phase deployment process]: #two-phase-deployment-process
