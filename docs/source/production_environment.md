# Production environment

This section is an overview of the repositories, projects, and
systems used in a mybinder.org production deployment.

Reference: [Google SRE book section on Production Environment](https://landing.google.com/sre/book/chapters/production-environment.html)

## Repository structure

This repository contains a 'meta chart' (`mybinder`) that fully captures the
state of the deployment on mybinder.org. Since it is a full helm chart, you
can read the [official helm chart structure](https://docs.helm.sh/developing_charts/#the-chart-file-structure)
document to know more about its structure.


## Dependent charts

The core of the meta-chart pattern is to install a bunch of [dependent charts](https://docs.helm.sh/developing_charts/#chart-dependencies),
specified in `mybinder/requirements.yaml`. This contains both support
charts like nginx-ingress & kube-lego, but also the core application chart
`binderhub`. Everything is version pinned here.

## Configuration values

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

## MyBinder.org specific extra software

We sometimes want to run additional software for the mybinder deployment that
does not already have a chart, or would be too cumbersome to use with a chart.
For those cases, we can create kubernetes objects directly from the `mybinder`
meta chart. You can see an example of this under `mybinder/templates/redirector`
that is used to set up a simple nginx based HTTP redirector.

## Related repositories

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
[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
[staging]: https://staging.mybinder.org
[BinderHub]: https://github.com/jupyterhub/binderhub
[binderhub]: https://github.com/jupyterhub/binderhub
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[repo2docker]: https://github.com/jupyter/repo2docker
[Deploying a change]: #deploying-a-change
