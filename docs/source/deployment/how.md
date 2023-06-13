# How to deploy a change to mybinder.org?

This document explains **how** to deploy a change to mybinder.org.
For information on what exactly a deployment does, see [what](what).

When a new change has landed in either [BinderHub](https://github.com/jupyterhub/binderhub)
or [repo2docker](https://github.com/jupyterhub/repo2docker), they need to be explicitly
deployed to mybinder.org for users to benefit from them. This is the most common kind of
change deployed to mybinder.org.

Upgrades to BinderHub and repo2docker are automatically managed by the [Watch Dependencies GitHub](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/watch-dependencies.yaml) workflow.

Follow the instructions below if you need to manually update BinderHub or Repo2docker.

## Deployment policy

Deployments to mybinder.org should be:

1. **Safe**. We will have good, user friendly tooling + lots of safeguards,
   so people can deploy without fear of accidentally breaking the site.

2. **Straightforward**. We want a lot of people to be involved in maintaining mybinder.org,
   so we must make sure deployments are also easy to do. Most deployments should
   not require specific sysadmin knowledge.

3. **Timely**. We deploy changes to repo2docker and BinderHub within a few days of
   them being merged into main.

These are all **aspirational** - we strive for hitting the above points,
but recognize that work and life may get in the way of doing this perfectly.

## Updating BinderHub

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the BinderHub repo.

BinderHub, the Helm chart, is a dependency for the local `mybinder` Helm chart.
The version of the BinderHub Helm chart is declared in `mybinder/Chart.yaml`.
Upgrading the version of BinderHub that is used in mybinder.org corresponds to
updating the BinderHub Helm chart version, which we step through below.

1.  Merge changes to BinderHub.
2.  Wait for the [Publish helm chart and docker images workflow on the main branch](https://github.com/jupyterhub/binderhub/actions/workflows/publish.yml?query=branch%3Amain) to complete successfully.
3.  Lookup the latest BinderHub chart dev version on https://hub.jupyter.org/helm-chart/#development-releases-binderhub
4.  In your fork of the [mybinder.org-deploy](https://github.com/jupyterhub/mybinder.org-deploy) repository, open `mybinder/Chart.yaml` and change `version` in the `binderhub` section of `dependencies` to the latest BinderHub chart dev version.
5.  Open a pull request to merge this change into the main branch of the
    mybinder.org-deploy repository, following the steps in [Deploying a change](deploying-a-change).

## Updating repo2docker

This section explains how to upgrade the mybinder.org deployment after
merging a PR in the [repo2docker](https://github.com/jupyterhub/repo2docker) repo.

BinderHub uses a docker image with repo2docker in it. When a new commit is merged in
the repo2docker repository, a new version of this image is pushed. We then configure
BinderHub to use the newly built image (which is identified by a tag) by editing `values.yaml`.

1.  Merge changes to repo2docker.
2.  Wait for the [Publish helm chart and docker images workflow on the main branch](https://github.com/jupyterhub/repo2docker/actions/workflows/release.yml?query=branch%3Amain) to complete successfully.
3.  Lookup the latest Repo2docker tag on https://quay.io/repository/jupyterhub/repo2docker?tab=tags
4.  In your fork of the mybinder.org-deploy repository, open `mybinder/values.yaml` and change the tag in `binderhub.config.KubernetesBuildExecutor.build_image` to the latest tag.
5.  Open a pull request to merge this change into the main branch of the
    mybinder.org-deploy repository, following the steps in [Deploying a change](deploying-a-change).

(deploying-a-change)=

## Deploying a change

### Deploying to _both_ `staging` then `prod`

Deploying a change involves making a PR with your desired change and merging it to
main.

1.  Make the changes as described above [on your fork of this repo](https://github.com/jupyterhub/mybinder.org-deploy).
2.  Keep track of the **hashes** that were updated. You should have both the _old_ hash that
    was replaced, and the _new_ hash that replaced it.
3.  If you haven't already, run the `list_new_commits.py` script in the `scripts/`
    folder. This will print out a URL that describes the changes made to both
    BinderHub and repo2docker.
4.  Make a PR to the `main` branch with the changes you want.

    - Name the PR like so: `<TOOL-CHANGED>: <OLD-HASH>...<NEW-HASH>`
    - In the description of the PR, paste the full URL that you printed out
      `list_new_commits.py`. It should have the following form:

          https://github.com/jupyterhub/<REPO-NAME>/compare/<OLD-HASH>...<NEW-HASH>

5.  Review, accept, and merge this PR. This will make GitHub Actions deploy the changes
    to [staging.mybinder.org](https://staging.mybinder.org), and run tests in the `tests/`
    directory against it. **In this case, you can merge your own PR**. Note that if the
    PR is a large change to the Kubernetes setup, this may take some time, and GitHub Actions may
    time-out in the process. If this happens and you _expect_ it to happen, you can restart
    the build a few times.
6.  If the tests succeed, the change will be deployed to mybinder.org.
7.  If the tests fail, the change will _not_ be deployed to mybinder.org.
    You must then investigate why it failed. **If you can
    not figure out a cause in about 10 minutes, revert the change.**
    You can revert the change with [the GitHub UI](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/reverting-a-pull-request) and immediately
    merge the reversion PR that GitHub creates.
8.  Troubleshoot and make changes to your fork. Repeat the process from Step 1.

### Deploying to _only_ `staging`

Sometimes you want to test out a deployment live before you make a deployment to `prod`.
There are a few ways we can achieve this.

#### Testing Pull Requests from **branches** of `mybinder.org-deploy`

This simplest way to deploy a PR to staging only is to apply the `test-staging` label to an open PR. This will trigger GitHub Actions to deploy the changes in the PR to the staging cluster **only**.

```{note}
If you need to re-deploy the changes in a PR to staging only, then the label will need to be removed and then re-added.
```

#### Testing Pull Requests from **forks** of `mybinder.org-deploy`

If the PR has been made from a fork of the repo, the labelling approach discussed in the previous section will fail due to a lack of access to secrets.
In this scenario, a user with `OWNER`, `COLLABORATOR` or `MEMBER` association with the `mybinder.org-deploy` repo can leave a `/test-this-pr` comment on the PR to trigger a deploy to staging.

#### Editing staging config directly

The final option to deploy to staging only is by editing `staging`-only config files. To deploy
to staging only, follow these steps:

1. Make changes to [`config/staging.yaml`](https://github.com/jupyterhub/mybinder.org-deploy/blob/HEAD/config/staging.yaml)
   on your fork. This file contains configuration for Helm that will **override**
   whatever is in `mybinder/values.yaml`.
2. Make a PR to the `main` branch, and review, accept, and merge this PR.
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

The [what](what) document has more details on common ways deployments can go
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
