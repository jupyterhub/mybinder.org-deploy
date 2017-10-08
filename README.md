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

Deploying a change follows a two-step process. First you'll deploy to
the `staging` branch of the repository, then if all looks well you'll deploy
to the production branch of the repository (called `beta`)

1. Make the change you want.
2. Make a PR to the `staging` branch with the changes you want!
3. Get this PR merged. This will make travis do a deployment
   to [staging](https://staging.mybinder.org)
4. Go to `staging.mybinder.org` to look at the changes.
5. Verify that staging works as intended. If there are *any* issues at all,
   however minor - stop, investigate, and do not proceed until you are
   completely convinced that it is ok!

**If the changes look correct.**
6. Make a new PR, merging staging into the beta branch.
7. Get this PR merged, and wait for travis to make a deployment
   to [beta](https://beta.mybinder.org)
8. CELEBRATE!

**If the changes don't look correct, or there is an error.**
6. **Immediately revert the PR that was made to `staging`.**
7. Make changes to your fork and repeat the process above until it looks
   correct.

## Upgrading dependencies on the public deployment
Upgrading dependencies that `mybinder.org` uses requires making specific changes
to the `config` files of the repository. The following sections cover how to do
this for various dependencies. In each case, you'll need to deploy these changes
by following the steps above in `Deploying a change`.

### BinderHub
1. After changes to `BinderHub` have been merged.
2. Open the travis build for `BinderHub`, navigate to the page corresponding to
   the master branch.
3. If the build succeeds, grab the hash that is displayed at the end of the
   travis output. It looks something like

   `create mode 100644 binderhub-0.1.0-9e509fa.tgz`

   The hash is the string at the very end, between `-` and `.tgz`. In this
   example, it is `9e509fa`.
4. In your fork of the `myinder.org-deploy` repository, open
   `config/common.yaml`.
5. Under `version`, update the hash that comes just after the `-` with the
   hash that you've copied in step 3.
6. Merge this change into the `mybinder.org-deploy` repository following the
   steps in the `Deploying a change` section above to deploy the change
   to `staging`, and then `beta`.

### repo2docker
1. After changes to `repo2docker` have been merged.
2. Open the travis build for `repo2docker`, find the text "Pushed new
   repo2docker image: <YOUR-IMAGE-NAME>". Copy the text in `<YOUR-IMAGE-NAME>`.
   **Note**: You may need to unfold the code in the `Deploying application` line
   in order to see this text.
3. In your fork of the `mybinder.org-deploy` repository,
   open `config/common.yaml`.
4. Under `repo2dockerImage`, replace the text that is there with what you copied
   in step 2.
6. Merge this change into the `mybinder.org-deploy` repository following the
   steps in the `Deploying a change` section above to deploy the change
   to `staging`, and then `beta`.

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
