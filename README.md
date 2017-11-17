# mybinder.org-deploy

- Staging: [![Staging Build Status](https://travis-ci.org/jupyterhub/mybinder.org-deploy.svg?branch=staging)](https://travis-ci.org/jupyterhub/mybinder.org-deploy)
- Production: [![Production Build Status](https://travis-ci.org/jupyterhub/mybinder.org-deploy.svg?branch=prod)](https://travis-ci.org/jupyterhub/mybinder.org-deploy/branches)


This repository contains configuration files and documentation related to the
[binderhub][] deployment open to the public at [mybinder.org][].

**Important: If you wish to deploy your own Binder instance, please do not
use these files as they are specific to [mybinder.org][].** Instead, you should
refer to the [`jupyterhub/binderhub`][] repo and the
[BinderHub documentation][].

## Basics

This repo contains two branches: `staging` and `prod`. The `staging` branch
corresponds to the config for [staging.mybinder.org][] and the `prod`
branch to [mybinder.org][]. In general (except when performing a
deployment), these branches should always be the same, and `prod` should not
drift away from `staging` too much.

## Pre-requisites

The following are tools and technologies that mybinder.org uses. You should have
a working familiarity with them in order to make changes to the mybinder.org deployment.

### Google Cloud Platform

MyBinder.org currently runs on Google Cloud. There are two Google Cloud projects
that we use:

1. `binder-staging` contains all resources for the staging deployment
2. `binder-prod` contains all resources for the production deployment

We'll hand out credentials to anyone who wants to play with the staging deployment,
so please just ask!

While you only need merge access in this repository to deploy changes, ideally
you should also have access to the two Google Cloud Projects so you can debug
things when deployments fail.

### Kubernetes Basics

We heavily use Kubernetes for the mybinder.org deployment, and it is important you
have a working knowledge of how to use Kubernetes. Detailed explanations are out
of the scope of this repository, but there is a good [list of tutorials](https://kubernetes.io/docs/tutorials/).
Specifically, going through the [interactive tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
to get comfortable using `kubectl` is required.

### Helm Basics

We use [helm](https://helm.sh) to manage our deployments, and it is imporant you
have a working knowledge of how to use helm. Detailed explanations are out of the
scope of this repository, but [docs.helm.sh](https://docs.helm.sh) is an excellent
source of information. At a minimum, you must at least understand:

* [What is a chart?](https://docs.helm.sh/developing_charts/#charts)
* [What are values files?](https://docs.helm.sh/chart_template_guide/#values-files)
* [How do chart dependencies work?](https://docs.helm.sh/developing_charts/#chart-dependencies)

This is a non-exhaustive list. Feel free to ask us questions on the gitter channel or
here if something specific does not make sense!


## Deploying a change

Deploying a change follows a two-step process. First, you'll deploy to
the `staging` branch of the repository. Second, if all looks well, you'll
deploy to the `prod` (production) branch of the repository.

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
   navigate to the page corresponding to the master branch.
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
   to deploy the change to [staging][], and then [prod][].

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
   to deploy the change to [staging][], and then [prod][].

## Repository structure

This repository contains a 'meta chart' (`mybinder`) that fully captures the
state of the deployment on mybinder.org. Since it is a full helm chart, you
can read the [official helm chart structure](https://github.com/kubernetes/helm/blob/master/docs/charts.md#the-chart-file-structure)
document to know more about its structure.


### Dependent charts

The core of the meta-chart pattern is to install a bunch of [dependent charts](https://github.com/kubernetes/helm/blob/master/docs/charts.md#chart-dependencies),
specified in `mybinder/requirements.yaml`. This contains both support
charts like nginx-ingress & kube-lego, but also the core application chart
`binderhub`. Everything is version pinned here.

### Configuration values

The following files fully capture the state of the deployment for staging:

1. `mybinder/values.yaml` - Common configuration values between prod &
   staging
2. `secret/config/staging.yaml` - Secret values specific to the staging
   deployment
3. `config/staging.yaml` - Non-secret values specific to the staging
   deployment

The following files fully capture the state of the production deployment:

1. `mybinder/values.yaml` - Common configuration values between prod &
   staging
2. `secret/config/prod.yaml` - Secret values specific to the production
   deployment
3. `config/prod.yaml` - Non-secret values specific to the production
   deployment

**Important**: For maintainability and consistency, we try to keep the contents
of `staging.yaml` and `prod.yaml` super minimal - they should be as close
to each other as possible. We want all common config in `values.yaml` so testing
on staging gives us confidence it will work on prod. We also never share the same
secrets between staging & prod for security boundary reasons.

### MyBinder.org specific extra software

We sometimes want to run additional software for the mybinder deployment that
does not already have a chart, or would be too cumbersome to use with a chart.
For those cases, we can create kubernetes objects directly from the `mybinder`
meta chart. You can see an example of this under `mybinder/templates/redirector`
that is used to set up a simple nginx based HTTP redirector.

### Related repositories

Related repositories used by the [mybinder.org][] service are:

1. [binderhub][]

   This contains the [binderhub][] code (UI & hub management) & helm chart.
   To change the UI / UX or hub management aspects of [mybinder.org][],
   go to [binderhub][].

2. [repo2docker][]

   This is used to do the actual building of git repositories into docker
   images, and can be used standalone too. If you want to change how a git
   repository is converted into a docker image to be run for the user,
   go to [repo2docker][].


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
