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

We heavily use [Kubernetes](https://k8s.io) for the mybinder.org deployment, and it is important you
have a working knowledge of how to use Kubernetes. Detailed explanations are out
of the scope of this repository, but there is a good [list of tutorials](https://kubernetes.io/docs/tutorials/).
Specifically, going through the [interactive tutorial](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
to get comfortable using `kubectl` is required.

## Helm

We use [helm](https://helm.sh) to manage our deployments, and it is important you
have a working knowledge of how to use helm. Detailed explanations are out of the
scope of this repository, but [docs.helm.sh](https://docs.helm.sh) is an excellent
source of information. At a minimum, you must at least understand:

* [What is a chart?](https://docs.helm.sh/developing_charts/#charts)
* [What are values files?](https://docs.helm.sh/chart_template_guide/#values-files)
* [How do chart dependencies work?](https://docs.helm.sh/developing_charts/#chart-dependencies)

## Travis

We use [Travis CI](http://travis-ci.org/) for doing all our deployments. Our
`.travis.yml` file contains the entire configuration for our deployment. Travis CI
has documentation on the [various components of the `.travis.yml` file](https://docs.travis-ci.com/user/customizing-the-build/).

[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
