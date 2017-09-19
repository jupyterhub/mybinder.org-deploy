# [mybinder.org-deploy][]

Deployment config files for [beta.mybinder.org](https://beta.mybinder.org).

*Note: If you wish to deploy your own Binder instance, you should refer
to the [`jupyterhub/binderhub`][] repo and the [BinderHub documentation][]*

## Contents

This repo contains config files used in the deployment workflow
for `beta.mybinder.org`.

### `binder` directory

- `common.yaml` configuration settings that are used in all deployment files
- `staging.yaml` config used for "staging" binder service, which currently
  lives [here](https://binder.binder-staging.omgwtf.in/) (will move at some
  point to `staging.mybinder.org`)
- `beta.yaml` config used for the beta deployment
- `prod.yaml` config used in a production deployment

### `support` directory

This contains a set of 3rd party charts we use for supporting our own code
on the binder deployment. The charts we use and their versions are specified
in `requirements.yaml`, and the configuration of those charts is in
`values.yaml`.

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
