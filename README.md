# [mybinder.org-deploy][]

Deployment procedure and configuration files for
[beta.mybinder.org](https://beta.mybinder.org).

*Note: If you wish to deploy your own Binder instance, please do not use these
files as they are specific to `mybinder.org`. Instead, you should refer
to the [`jupyterhub/binderhub`][] repo and the [BinderHub documentation][].*

## Deploying

The state of the *production* and *staging* clusters for `mybinder.org` should
match the `master` branch of this git repository.

Currently, users deploy the site manually using required deployment scripts,
such as `deploy.py`. We will soon automate the deployment process for ease of
use, consistency, monitoring, and resiliency.

## Deployment Process

### Prerequisites

Before deploying, you need the following:

1. Be a team member of the Google Cloud project that is being used for
   `mybinder.org`.

2. Access to the [git-crypt](https://github.com/AGWA/git-crypt) symmetric
   encryption key file used to encrypt secrets in this repository.

3. A recent version of [helm](https://helm.sh/) installed locally in `$PATH`.

4. Some knowledge of how to debug stuff when it goes wrong :)

### How to deploy

1. Make changes to the config.

2. Commit the changes to the git repository. We recommend following the
   PR process, when able to do so.

3. Deploy to `staging` first:

   ```bash
   ./deploy.py deploy staging
   ```

4. Go to `staging` (currently at https://binder.binder-staging.omgwtf.in)
   and make sure everything works ok. Test the new functionality you just
   deployed and make sure it works as expected.

5. Make sure the changes you made in Step 2 are found in the `beta` config
   files too.

6. Deploy to `beta` after verifying Step 4 and 5:

   ```bash
   ./deploy.py deploy beta
   ```

7. Make sure that everything works ok in `beta`!

As this process is still very manual, please use these steps as a
**deployment checklist**. There'll be lots of improvements to automate deployment
coming soon.

## Repository structure

This repository contains configuration files and documentation related to the
[binderhub](https://github.com/jupyterhub/binderhub) deployment open to the
public at [beta.mybinder.org](https://beta.mybinder.org).

### `config` directory

This contains config YAML files that fully describe the current state of the
mybinder.org deployment:

- `common.yaml`: public, non-secret settings that are common to both
  `staging` and `production` deployments.
- `staging.yaml`: config that is specific to the `staging` mybinder, which
  lives [here](https://binder.binder-staging.omgwtf.in/) (will move at some
  point to `staging.mybinder.org`)
- `beta.yaml`: config specific to the `beta` mybinder.

**Important**: For maintainability and consistency, we try to keep the contents
of `staging.yaml` and `beta.yaml` super minimal - they should be as close
to each other as possible. We want `staging` to mirror `beta` so we can test
things before pushing them out.

### `config/secret` subdirectory

This contains files that should be kept *'secret'* from the rest of the world
i.e. secret keys, cookie secrets, etc. Though secret, keeping them in the git
repo is the simplest and easiest way to distribute them securely to
**deployment team** members. We use [git-crypt](https://github.com/AGWA/git-crypt)
for this purpose.

- `staging.yaml` has secrets specific to the `staging` mybinder.
- `beta.yaml` has secrets specific to the `beta` mybinder.
- `common.yaml` has secrets specific to both `staging` and `beta` mybinders.

### `support` directory

This contains a set of third party charts which we use for supporting our own
code on the `mybinder` deployment. The charts we use and their versions are
specified in `requirements.yaml`, and the configuration of those charts is in
`values.yaml`.

[mybinder.org-deploy]: https://github.com/jupyterhub/mybinder.org-deploy
[BinderHub documentation]: https://binderhub.readthedocs.io/en/latest/
[`jupyterhub/binderhub`]: https://github.com/jupyterhub/binderhub
