# Pre-requisite technologies

The following are tools and technologies that mybinder.org uses. You should have
a working familiarity with them in order to make changes to the mybinder.org deployment.

This is a non-exhaustive list. Feel free to ask us questions on the gitter channel or
here if something specific could be clearer!

## Google Cloud Platform

MyBinder.org currently runs on Google Cloud. There are two Google Cloud projects
that we use:

1. `binder-staging` contains all resources for the staging deployment
2. `binder-prod` contains all resources for the production deployment

We'll hand out credentials to anyone who wants to play with the staging deployment,
so please just ask!

While you only need merge access in this repository to deploy changes, ideally
you should also have access to the two Google Cloud Projects so you can debug
things when deployments fail.

## Kubernetes

We heavily use [Kubernetes](https://kubernetes.io/) for the mybinder.org deployment, and it is important you
have a working knowledge of how to use Kubernetes. Detailed explanations are out
of the scope of this repository, but there is a good [list of tutorials](https://kubernetes.io/docs/tutorials/).
Specifically, going through the [interactive tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
to get comfortable using `kubectl` is required.

## Helm

We use [helm](https://helm.sh) to manage our deployments, and it is important you
have a working knowledge of how to use helm. Detailed explanations are out of the
scope of this repository, but [docs.helm.sh](https://docs.helm.sh) is an excellent
source of information. At a minimum, you must at least understand:

- [What is a chart?](https://helm.sh/docs/chart_template_guide/getting_started/#charts)
- [What are values files?](https://helm.sh/docs/chart_template_guide/values_files/)
- [How do chart dependencies work?](https://helm.sh/docs/chart_template_guide/subcharts_and_globals/)

## GitHub Actions

We use [GitHub Actions](https://docs.github.com/en/actions) for doing all our deployments. Our
[`.github/workflows/cd.yml`](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/cd.yml) file
contains the entire configuration for our **continuous** deployment.

Because mybinder.org dependes on JupyterHub, BinderHub and repo2docker, we also use [GitHub Actions to watch those dependencies](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/watch-dependencies.yaml) once every day and, if needed, create a pull request. mybinder.org operators can manually trigger a dependency check by clicking the "[Run workflow](https://github.com/jupyterhub/mybinder.org-deploy/actions/workflows/watch-dependencies.yaml)" button.

[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
