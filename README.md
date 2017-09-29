# [mybinder.org-deploy][]

This repository contains configuration files and documentation related to the
[binderhub](https://github.com/jupyterhub/binderhub) deployment open to the
public at [beta.mybinder.org](https://beta.mybinder.org).

*Note: If you wish to deploy your own Binder instance, please do not use these
files as they are specific to `mybinder.org`. Instead, you should refer
to the [`jupyterhub/binderhub`][] repo and the [BinderHub documentation][].*

There are two branches here: staging & beta. These should always be the same -
beta should not drift away from staging too much. staging branch should
correspond to the config
for [staging.mybinder.org](https://staging.mybinder.org) & the beta branch
to [beta.mybinder.org](https://beta.mybinder.org).

## Deploying a change

Deploying a change is quite simple!

1. Make the change you want. 
2. Make a PR to the `staging` branch with the changes you want!
3. Get this PR merged. This will make travis do a deployment
   to [staging](https://staging.mybinder.org)
4. Verify that staging works as intended. If there are *any* issues at all,
   however minor - stop, investigate, and do not proceed until you are
   completely convinced that it is ok!
5. Make a new PR, merging staging into the beta branch.
6. Get this PR merged, and wait for travis to make a deployment
   to [beta](https://beta.mybinder.org)
7. CELEBRATE!

More detailed information to come soon!

## Repository structure

This repository contains purely config files. Related repositories with more
interesting contents are:

1. [binderhub](https://github.com/jupyterhub/binderhub)
   
   This contains the binderhub code (UI & hub management) & helm chart. This is
   where most of the action is. If you wanna change the UI / UX or hub
   management aspects of mybinder.org, go here!

2. [repo2docker](http://github.com/jupyter/repo2docker)

   This is used to do the actual building of git repositories into docker
   images, and can be used standalone too. If you want to change how a git
   repository is converted into a docker image to be run for the user, go here!

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
