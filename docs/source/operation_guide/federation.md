(mybinder-federation)=

# The `mybinder.org` Federation

The current status of the `mybinder.org` federation can be found
[here](https://mybinder.readthedocs.io/en/latest/about/status.html).

## Adding or removing a federation member

The following files contain references to the federation, and should be
updated when a federation member is added or removed:

1.  pages for <https://mybinder.readthedocs.io>:
    [status](https://github.com/jupyterhub/mybinder.org-user-guide/blob/HEAD/doc/about/status.rst)
    and [federation
    info](https://github.com/jupyterhub/mybinder.org-user-guide/blob/HEAD/doc/_data/support/federation.yml)

2.  [deployment to the
    cluster](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/cd.yml)

3.  [testing of the cluster
    configuration](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/.github/workflows/test-helm-template.yaml)

4.  membership in [federationRedirect.hosts config for
    prod](https://github.com/jupyterhub/mybinder.org-deploy/blob/7aa58e033efe1ed1cee1b5cb7e789c1296deb36a/config/prod.yaml#L220)

5.  add/remove data source for the cluster\'s prometheus at
    <https://grafana.mybinder.org>

6.  **if outside the default Google Cloud project, make sure launches are published to the events archive:**
    - If not deployed from this repo, publishing events to the
      archive is configured
      [here](https://github.com/jupyterhub/mybinder.org-deploy/blob/339ccb1de8107dc7854cac45f0a5b6e99937a91b/mybinder/values.yaml#L200-L219)
    - GKE clusters don\'t need further configuration, but outside
      GKE (or outside our GCP project, maybe?) need a service
      account. These accounts are configured [in
      terraform](https://github.com/jupyterhub/mybinder.org-deploy/blob/339ccb1de8107dc7854cac45f0a5b6e99937a91b/terraform/gcp/prod/main.tf#L17),
      and can be retrieved via [terraform output
      events_archiver_keys]{.title-ref}. For OVH, a secret is
      added to the chart
      [here](https://github.com/jupyterhub/mybinder.org-deploy/blob/main/mybinder/templates/events-archiver/secret.yaml)
      and mounted in the binder pod
      [here](https://github.com/jupyterhub/mybinder.org-deploy/blob/339ccb1de8107dc7854cac45f0a5b6e99937a91b/config/ovh2.yaml#L25-L34)
      (in our chart, the secret itself is added to
      [eventsArchiver.serviceAccountKey](https://github.com/jupyterhub/mybinder.org-deploy/blob/339ccb1de8107dc7854cac45f0a5b6e99937a91b/mybinder/values.yaml#L555-L557)
      helm config, in secrets/config/ovh2.yaml).

## Temporarily removing a federation member from rotation

There are a few reasons why you may wish to remove a Federation member
from rotation. For example, maintenance work, a problem with the
deployment, and so on.

There are 3 main files you may wish to edit in order to remove a cluster
from the Federation:

1.  _Required._ Set the `binderhub.config.BinderHub.pod_quota` key to
    `0` in the cluster\'s config file under the
    [config](https://github.com/jupyterhub/mybinder.org-deploy/tree/HEAD/config)
    directory
2.  _Recommended._ Set the `weight` key for the cluster to `0` in the
    [helm chart values
    file](https://github.com/jupyterhub/mybinder.org-deploy/blob/7aa58e033efe1ed1cee1b5cb7e789c1296deb36a/config/prod.yaml#L220)
    in order to remove it from the redirector\'s pool
3.  _Optional._ Comment out the cluster from the [continuous
    deployment](https://github.com/jupyterhub/mybinder.org-deploy/blob/4f42d791f92dcb3156e7c4ea92a236246bbf9135/.github/workflows/cd.yml#L168)
    file
