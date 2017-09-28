# [mybinder.org-deploy][]

Deployment config files for [beta.mybinder.org](https://beta.mybinder.org).

*Note: If you wish to deploy your own Binder instance, please do not use these
files as they are specific to `mybinder.org`. Instead, you should refer
to the [`jupyterhub/binderhub`][] repo and the [BinderHub documentation][]*

## Deploying

The state of the production & staging mybinder.org clusters should match the
master of this git repository. Currently, deployments are still manual & require
users to run a script locally. We will soon automate this to be a GitHub based
automatic deployment set up for ease of use & resiliency.

### Pre-requisites

Before deploying, you need the following:

1. Be a member of the Google Cloud project that is being used for mybinder.org
2. Access to the [git-crypt](https://github.com/AGWA/git-crypt) symmetric
   encryption key file used to encrypt secrets in this repositories.
3. A recent version of [helm](https://helm.sh/) installed locally in `$PATH`.
4. Some knowledge of how to debug stuff when it goes wrong :)

### How to deploy

1. Make the changes to the config you wish to make.
2. Commit them to the git repository
3. Deploy to staging first:

   ./deploy.py deploy staging

4. Go to staging (currently at https://binder.binder-staging.omgwtf.in) and make sure
   everything works ok. Test the new functionality you just deployed and make sure
   it works fine.
5. Make sure the changes you wish to make are in the beta config files too.
6. Deploy to beta:

   ./deploy.py deploy beta

7. Make sure that everything works ok in beta!

This is still very manual, and there'll be lots of improvements coming soon.

## Repository structure

This repository contains config files & documentation related to the
[binderhub](https://github.com/jupyterhub/binderhub) deployment open to the
public at [beta.mybinder.org](https://beta.mybinder.org)

### `config`

This contains config YAML files that fully describe the current state of the
mybinder.org deployment

- `common.yaml` has public, non-secret settings that are common to both
  staging & production deployments.
- `staging.yaml` has config that is specific to the staging mybinder, which
  lives [here](https://binder.binder-staging.omgwtf.in/) (will move at some
  point to `staging.mybinder.org`)
- `beta.yaml` has config specific to the beta mybinder.

Note that we try to keep the contents of staging.yaml and beta.yaml super minimal -
they should be as close to each other as possible. We want staging to mirror beta
so we can test things before pushing them out.

### `config/secret`

This contains files that should be kept 'secret' to the rest of the world - secret
keys, cookie secrets, etc. However, keeping them in the git repo is the simplest &
easiest way to distribute them securely. We use [git-crypt](https://github.com/AGWA/git-crypt)
for this purpose.

- `staging.yaml` has secrets specific to the staging mybinder.
- `beta.yaml` has secrets specific to the beta mybinder.
- `common.yaml` has secrets specific to both staging & beta mybinders.

### `support` directory

This contains a set of 3rd party charts we use for supporting our own code
on the binder deployment. The charts we use and their versions are specified
in `requirements.yaml`, and the configuration of those charts is in
`values.yaml`.

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
