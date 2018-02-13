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

## mybinder.org specific extra software

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

## The Deployment Helm Meta Chart

BinderHub is deployed using a Kubernetes Helm Chart, which is a specification
for instructing Kubernetes how to deploy particular applications. Sometimes,
applications depend on others in order to function properly, similar to how
a package might depend on other packages (e.g., Pandas depends on Numpy).
These dependencies are specified with a Helm "Meta Chart".

For example, let's say that you'd like to begin using Prometheus in your
Kubernetes deployment. Since Prometheus has a helm chart for deploying it
on Kubernetes, we can add it as a dependency in a Helm Meta Chart. We'd
create a file called `requirements.yaml` and put the following in it:

```yaml
dependencies:
- name: prometheus
  version: 4.6.16
  repository: https://kubernetes-charts.storage.googleapis.com
```

This also allows us to pin a *version* of Prometheus, which improves
reliability of the site.

```note::
It is still possible to deploy each of these applications on their own *without*
a Meta Helm Chart, this is simply a way of clustering dependencies together
and simplifying the deployment structure.
```

Another benefit of Meta Charts is that you can use a single configuration
file (`config.yaml`) with multiple Helm Charts. For example, look at the
[BinderHub Helm Chart](https://github.com/jupyterhub/mybinder.org-deploy/blob/staging/mybinder/values.yaml). Note that there are multiple
top-level sections (e.g., for [jupyterhub](https://github.com/jupyterhub/mybinder.org-deploy/blob/5aa6dde60c9b5f3012686f9ba2b23b176c19b224/mybinder/values.yaml#L53) and for [prometheus](https://github.com/jupyterhub/mybinder.org-deploy/blob/5aa6dde60c9b5f3012686f9ba2b23b176c19b224/mybinder/values.yaml#L204)) and that each section
has a corresponding entry in the Helm Meta Chart. In this way, we can provide
configuration for each dependency of BinderHub without needing a separate
file for each, and we can deploy them all at the same time.

For more information, we recommend investigating the structure of the
[Binder Helm Meta Chart](https://github.com/jupyterhub/mybinder.org-deploy/blob/staging/mybinder/requirements.yaml). In addition, the Kubernetes
organization keeps a [curated list of Helm Charts](https://github.com/kubernetes/charts) that you can specify in
your Meta Chart in order to deploy different types of applications.

## HTTPS configuration for `mybinder.org`

Using HTTPS requires having a signed certificate. BinderHub uses [kube-lego](https://github.com/jetstack/kube-lego),
a tool that obtains and deploys a free *Let's Encrypt* certificate automatically.
This section describes how to use `kube-lego` to configure and deploy HTTPS support.

`kube-lego` provides 90 day SSL certificates for `mybinder.org` through
the [letsencrypt](https://letsencrypt.org/) service. As the 90
day cycle nears its end, `kube-lego` will automatically request a new
certificate and configure the kubernetes deployment to use it.

`kube-lego` is a kubernetes application, with its own Helm Chart that is
referenced in the [`mybinder.org` Meta Chart](https://github.com/jupyterhub/mybinder.org-deploy/blob/5aa6dde60c9b5f3012686f9ba2b23b176c19b224/mybinder/values.yaml#L152). This tells kubernetes which
account to use for letsencrypt certification.

Once we have a letsencrypt account set up, we need to attach the SSL
certificate to a particular `ingress` object. This is a Kubernetes object
that controls how traffic is routed *into* the deployment. This is also
done with the `mybinder.org` Helm Chart ([see here for example](https://github.com/jupyterhub/mybinder.org-deploy/blob/5aa6dde60c9b5f3012686f9ba2b23b176c19b224/mybinder/values.yaml#L13)).

Note that letsencrypt will send you an email if your SSL certificate is
about to expire. If you get such an email, it might mean that the automatic
`kube-lego` renewal process hasn't worked properly. To debug this, we
recommend running the standard Kubernetes debugging commands with the
`kube-lego` object used with your deployment. For example:

```
kubectl --namespace=<my-namespace> logs <kube-lego-object>
```

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[prod]: https://mybinder.org
[mybinder.org]: https://mybinder.org
[staging.mybinder.org]: https://staging.mybinder.org
[staging]: https://staging.mybinder.org
[BinderHub]: https://github.com/jupyterhub/binderhub
[binderhub]: https://github.com/jupyterhub/binderhub
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[repo2docker]: https://github.com/jupyter/repo2docker
