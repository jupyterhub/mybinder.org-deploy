# [mybinder.org-deploy][]

Deployment config files for [beta.mybinder.org](https://beta.mybinder.org).

*Note: If you wish to deploy your own Binder instance, you should refer
to the [`jupyterhub/binderhub`][] repo and the [BinderHub documentation][]*

## Contents

This repo contains config files used in the deployment workflow
for `beta.mybinder.org`.

### `binder` directory

- `common.yaml` configuration settings that are used in all deployment files
- `staging.yaml` config used for staging the `beta.mybinder.org` deployment
  for testing
- `beta.yaml` config used for the beta deployment
- `prod.yaml` config used in a production deployment

### `support` directory

- `Chart.yaml` identifies name, API version, and version of the chart
- `requirements.yaml` identifies third party dependencies, such as
  prometheus, grafana, and others, and their specific versions
- `values.yaml` config values for third party tools

### repo root directory

- `common.yaml` (TODO: How does this differ from the common.yaml in the binder directory)

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
