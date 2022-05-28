# HTTPS ingress with nginx + kube-lego

Kubernetes [Ingress Objects](https://kubernetes.io/docs/concepts/services-networking/ingress/)
are used to manage HTTP(S) access from the internet to inside the Kubernetes cluster.
Among other things, it lets us do the following:

1. Provide a HTTPS end point so users can connect to us securely
2. Direct traffic to various Services based on hostnames or URL paths
3. Allow using one public IP address for multiple domain names

We use the [nginx-ingress](https://github.com/kubernetes/ingress-nginx) provider to handle
our Ingress needs.

## Nginx Ingress

We run on Google Cloud's Kubernetes Engine. Even though GKE comes pre-installed with
the [Google Cloud Load Balancer Ingress provider](https://github.com/kubernetes/ingress-gce),
we decided to use nginx instead for the following reasons:

1. GCLB has a 30s default timeout on all HTTP connections. This is counted
   not just when connection is idle, but from connection start time. This
   is particularly bad for websockets, since those connections usually last for
   a lot longer than 30s! There is no easy way to configure this timeout from
   inside Kubernetes.
2. GCLB does not guarantee you can use the same IP for multiple domains. We
   want the various subdomains of `mybinder.org` to point to the same IP
   so we can easily add / remove new services without waiting for DNS propagation
   delay.

### Installation

nginx-ingress is installed using the [nginx-ingress helm chart](https://github.com/kubernetes/charts/tree/master/stable/nginx-ingress).
This installs the following components:

1. `nginx-ingress-controller` - keeps the HTTPS rules in sync with `Ingress`
   objects and serves the HTTPS requests. This also exports
   [metrics](metrics) that are captured in prometheus.
2. `nginx-ingress-default-backend` - simply returns a 404 error & is used
   by `nginx-ingress-controller` to serve any requests that don't match
   any rules.

The specific ways these have been configured can be seen in the `mybinder/values.yaml`
file in this repo, under `nginx-ingress`.

### Configuration with Ingress objects

`Ingress` objects are used to tell the ingress controllers which requests
should be routed to which `Service` objects. Usually, the rules either
check for a hostname (like `mybinder.org` or `prometheus.mybinder.org`) and/or
a URL prefix (like `/metrics` or `/docs`). You can see all the ingress objects
present with `kubectl --namespace=prod get ingress`.

The following ingress objects currently exist:

* `jupyterhub` - Directs traffic to `hub.mybinder.org`.
  The zero-to-jupyterhub guide has more [documentation](https://zero-to-jupyterhub.readthedocs.io/en/latest/advanced.html#ingress).
* `binderhub` - Directs traffic to `mybinder.org`. You can find more details
   about this in the [binderhub helm chart](https://github.com/jupyterhub/binderhub/tree/master/helm-chart).
* `redirector` - Directs traffic to the HTTP redirector we run for `mybinder.org`.
   This helps do redirects such as `docs.mybinder.org` or `beta.mybinder.org`.
   The list of redirects is configured in `mybinder/values.yaml`. The code
   for this is in `mybinder/templates/redirector` in this repo.
* `static` - Directs traffic into `static.mybinder.org`. We serve the `mybinder.org`
   badges from a different domain for [privacy reasons](https://github.com/jupyterhub/binderhub/issues/379).
   This ingress lets us direct traffic only from `static.mybinder.org/badge.svg` to the
   binder pod.
* `prometheus-server` - Directs traffic to `prometheus.mybinder.org`. Configured under
  `prometheus` in both `mybinder/values.yaml` and `config/prod.yaml`.
* `grafana` - Directs traffic to `grafana.mybinder.org`. Configured under `grafana` in
   both `mybinder/values.yaml` and `config/prod.yaml`.
* `kube-lego-nginx` - Used by kube-lego for doing automatic
   HTTPS certificate renewals.

## HTTPS certificates with kube-lego

We use [Let's Encrypt](https://letsencrypt.org/) for all our HTTPS certificates.
[Kube Lego](https://github.com/jetstack/kube-lego) is used to automatically
provision and maintain HTTPS certificates for us.

```{note}
Kube-lego is deprecated, and we should move to
`cert-manager <https://github.com/jetstack/cert-manager/>`_ soon.
```

### Installation

kube-lego is installed using the [kube-lego](https://github.com/kubernetes/charts/tree/master/stable/kube-lego).

### Configuration

`kube-lego` requires Ingress objects to have specific `annotations` and
`tls` values, as [documented here](https://github.com/jetstack/kube-lego#how-kube-lego-works).
We specify this for all our ingress objects, mostly by customizing various helm charts
in `mybinder/values.yaml`.

### Let's Encrypt account

Let's Encrypt uses [accounts](https://community.letsencrypt.org/t/what-are-accounts-do-i-need-to-backup-them/21318)
to keep track of HTTPS certificates & expiry dates.
Currently, the account is registered to `yuvipanda@gmail.com`, mostly as a historical
accident. Changing it requires some amount of care to make sure we do not suffer
intermittent HTTPS failure, and should be done whenever we switch to cert-manager.
