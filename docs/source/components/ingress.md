# HTTPS ingress with traefik

Kubernetes [Ingress Objects](https://kubernetes.io/docs/concepts/services-networking/ingress/)
are used to manage HTTP(S) access from the Internet to inside the Kubernetes cluster.
Among other things, it lets us do the following:

1. Provide an HTTPS endpoint so users can connect to us securely
2. Direct traffic to various Services based on hostnames or URL paths
3. Allow using one public IP address for multiple domain names

We use the [traefik ingress](https://github.com/traefik/traefik) provider to handle
our Ingress needs.

A typical ingress configuration in our repo looks like:

```yaml
# in mybinder/values.yaml
ingress:
  annotations:
    kubernetes.io/ingress.class: traefik
    kubernetes.io/tls-acme: "true"

# in config/name.yaml:
ingress:
  hosts:
    - subdomain.mybinder.org
  tls:
    - hosts:
        - subdomain.mybinder.org
      secretName: tls-subdomain
```

where the common configuration is that:

1. `traefik` should recognize and serve the traffic described by the Ingress (`ingress.class`)
2. `certmanager` should register certificates (`tls-acme`)

and the deployment-specific configuration (hosts) are in the deployment-specific configuration file.

## Cluster Entrypoint

The Cluster Entrypoint is a Service defined in our chart that routes traffic from the Internet to the actual Controller that directs traffic to each of our deployed services.
Cluster Entrypoint is intended to be the only publicly-facing (`type: LoadBalancer`) Service on each cluster.
This way, we can change the _implementation_ (ingress controller or gateway controller) without needing to worry about stable public IP addresses, etc.

## Traefik Ingress

We run on a changing variety of Kubernetes providers, including Google Cloud's Kubernetes Engine
and single-node K3S clusters.
Even though GKE, K3S, and other managed Kubernetes come pre-installed with an Ingress controller such as [Google Cloud Load Balancer Ingress provider](https://github.com/kubernetes/ingress-gce),
we decided deploy our own instance of traefik instead because using the same ingress controller across deployments simplifies management considerably,
and gives us access to configuration often not available for host-provided ingress controllers.

We migrated to traefik from the official Kubernetes `ingress-nginx` ingress controller because it
See more discussion [here](https://github.com/jupyterhub/mybinder.org-deploy/issues/3639) and in linked issues.

### Installation

traefik is installed using the [traefik helm chart](https://github.com/traefik/traefik-helm-chart).
This installs the following components:

1. `traefik` - keeps the HTTPS rules in sync with `Ingress`
   objects and serves the HTTPS requests. This also exports
   [metrics](metrics) that are captured in prometheus.

The specific ways these have been configured can be seen in the `mybinder/values.yaml`
file in this repo, under `traefik`.

### Configuration with Ingress objects

`Ingress` objects are used to tell the ingress controllers which requests
should be routed to which `Service` objects. Usually, the rules either
check for a hostname (like `mybinder.org` or `prometheus.mybinder.org`) and/or
a URL prefix (like `/metrics` or `/docs`). You can see all the ingress objects
present with `kubectl --namespace=prod get ingress`.

An ingress object is served with `traefik` if it has the annotation:

```
kubernetes.io/ingress.class: traefik
```

The following ingress objects currently exist (not all clusters provide all endpoints):

- `jupyterhub` - Directs traffic to `hub.mybinder.org`.
  The zero-to-jupyterhub guide has more [documentation](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/advanced.html#ingress).
- `binderhub` - Directs traffic to `mybinder.org`. You can find more details
  about this in the [binderhub helm chart](https://github.com/jupyterhub/binderhub/tree/HEAD/helm-chart).
- `federation-redirect` - The load-balancing proxy that serves `mybinder.org` and routes requests across the federation.
  Its source is in `images/federation-redirect`.
- `gcs-proxy` - A proxy for the blob storage on Google Cloud Storage to serve archive.analytics.mybinder.org.
- `redirector` - Directs traffic to the HTTP redirector we run for `mybinder.org`.
  This helps do redirects such as `docs.mybinder.org` or `beta.mybinder.org`.
  The list of redirects is configured in `mybinder/values.yaml`. The code
  for this is in `mybinder/templates/redirector` in this repo.
- `harbor` - serves the image registry Harbor, if a self-hosted registry is deployed on the cluster.
- `static` - Directs traffic into `static.mybinder.org`. We serve the `mybinder.org`
  badges from a different domain for [privacy reasons](https://github.com/jupyterhub/binderhub/issues/379).
  This ingress lets us direct traffic only from `static.mybinder.org/badge.svg` to the
  binder pod.
- `prometheus-server` - Directs traffic to `prometheus.mybinder.org`. Configured under
  `prometheus` in both `mybinder/values.yaml` and `config/prod.yaml`.
- `grafana` - Directs traffic to `grafana.mybinder.org`. Configured under `grafana` in
  both `mybinder/values.yaml` and `config/prod.yaml`.

## HTTPS certificates with cert-manager

We use [Let's Encrypt](https://letsencrypt.org/) for all our HTTPS certificates.
[Cert-Manager](https://cert-manager.io) is used to automatically provision and maintain HTTPS certificates for us.

### Installation

Cert-Manager is installed using the [cert-manager chart](https://github.com/cert-manager/cert-manager).

### Configuration

Cert-Manager requires Ingress objects to have specific `annotations` and
`tls` values, as [documented here](https://cert-manager.io/docs/usage/ingress/).
We specify this for all our ingress objects, mostly by customizing various helm charts
in `mybinder/values.yaml`.

### Let's Encrypt account

Let's Encrypt uses [accounts](https://community.letsencrypt.org/t/what-are-accounts-do-i-need-to-backup-them/21318)
to keep track of HTTPS certificates & expiry dates.
Currently, the account is registered to `binder-team@googlegroups.com`.
