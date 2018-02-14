# mybinder.org-deploy

Deployment: [![Build Status](https://travis-ci.org/jupyterhub/mybinder.org-deploy.svg?branch=master)](https://travis-ci.org/jupyterhub/mybinder.org-deploy)

Deployment, configuration, and Site Reliability documentation files for the
public [mybinder.org][] service.

#### Deploying a Binder Service other than mybinder.org

These files are specific to [mybinder.org][].
If you wish to deploy your own Binder instance, please **do not use** these files.
Instead, you should review the [BinderHub documentation][] and the
[`jupyterhub/binderhub`][] repo to set up your deployment.

## Site Reliability Guide [![Documentation Status](http://readthedocs.org/projects/mybinder-sre/badge/?version=latest)](http://mybinder-sre.readthedocs.io/en/latest/?badge=latest)

[Site Reliability Guide for mybinder.org][] includes:
- our [deployment policy](http://mybinder-sre.readthedocs.io/en/latest/deployment_policy.html)
- [production environment](http://mybinder-sre.readthedocs.io/en/latest/production_environment.html) and [configuration](http://mybinder-sre.readthedocs.io/en/latest/production_environment.html#configuration-values) information
- [incident reports](http://mybinder-sre.readthedocs.io/en/latest/incident-reports/incident_reports_toc.html) and a [new incident template](https://github.com/jupyterhub/mybinder.org-deploy/blob/master/docs/source/incident-reports/template-incident-report.md)

## Key Links

|             | Staging | Production |
| ----------- | ------- | ---------- |
| Site     |[staging.mybinder.org](https://staging.mybinder.org) | [mybinder.org](https://mybinder.org) |
| TravisCI Deployment | [![Build Status](https://travis-ci.org/jupyterhub/mybinder.org-deploy.svg?branch=master)](https://travis-ci.org/jupyterhub/mybinder.org-deploy)
| Deployment checklist | staging | prod |
| Deployment docs | [staging](#deploy-to-staging) | [prod](#deploy-to-production) |
| Monitoring | staging | [prod](https://grafana.mybinder.org/dashboard/db/kubernetes-cluster-monitoring-binder-prod?refresh=10s&orgId=1) |

| Helm chart  | dev | stable |
|-------------|-----|--------|
| JupyterHub  | [ dev](https://jupyterhub.github.io/helm-chart/#development-releases-jupyterhub) | [stable](https://jupyterhub.github.io/helm-chart/#stable-releases) |
| BinderHub | [dev](https://jupyterhub.github.io/helm-chart/#development-releases-binderhub)| - |

## Deploying a change

Deploying a change involves making a PR
with your desired change and merging it to
master.

1. Make the [changes](#upgrading-dependencies-for-the-mybinderorg-deployment) on your fork.
2. Make a PR to the `master` branch with the changes you want.
3. Review, accept, and merge this PR. This will make Travis deploy the changes
   to [staging.mybinder.org][], run tests in the `tests/` directory against it.
4. If the tests succeed, the change will be deployed to [mybinder.org][].
5. If the tests fail, the change will *not* be deployed to [mybinder.org][].
   The deployer would then need to investigate why it failed, and if they can
   not figure out a cause in about 10 minutes, revert the change.
   Ideally, the build should not remain broken for more than ten minutes.
8. Troubleshoot and make changes to your fork. Repeat the process from Step 1.

## Upgrading dependencies for the mybinder.org deployment

Upgrading dependencies used by [mybinder.org][] requires making changes
to the `config` files of repositories that are used to build the
[mybinder.org][] service. The following sections cover how to do upgrade
dependencies for [BinderHub][] and [repo2docker][]. In each case, you'll need
to deploy these changes by following the steps above in [Deploying a change][].

### BinderHub

This section explains how to upgrade the [mybinder.org][] deployment after
making a change in the [BinderHub][] repo.

BinderHub is deployed via a helm chart that is tied to a particular commit on the
BinderHub repository. BinderHub is a "requirement" for this mybinder.org deployment,
which is why it is specified in requirements.yaml. Upgrading the version of BinderHub
that is used in mybinder.org corresponds to updating the BinderHub helm chart version,
which we step through below.

1. Merge changes to [BinderHub][].
2. Open the [Travis build for BinderHub](https://travis-ci.org/jupyterhub/binderhub),
   navigate to the page corresponding to the master branch, `TEST=helm` job.
3. If the build succeeds, grab the hash that is displayed at the end of the
   travis output. It looks something like:

       Successfully packaged chart and saved it to: gh-pages/binderhub-0.1.0-f87ac35.tgz

   The hash is the string at the very end, between `-` and `.tgz`. In this
   example, it is `f87ac35`.

   <img src="docs/static/travis-screenshot.png" width="500" />

4. In your fork of the [mybinder.org-deploy][] repository, open
   `mybinder/requirements.yaml`.
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

6. Merge this change to `mybinder/requirements.yaml` into the [mybinder.org-deploy][]
   repository following the steps in the [Deploying a change][] section above
   to deploy the change.

### repo2docker

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
   to deploy the change.

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[prod]: https://mybinder.org
[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
[staging]: https://staging.mybinder.org
[BinderHub]: https://github.com/jupyterhub/binderhub
[binderhub]: https://github.com/jupyterhub/binderhub
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[repo2docker]: http://github.com/jupyter/repo2docker
[Deploying a change]: #deploying-a-change
[Site Reliability Guide for mybinder.org]: http://mybinder-sre.readthedocs.io
