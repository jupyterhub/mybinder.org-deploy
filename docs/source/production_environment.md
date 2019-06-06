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

## Deployment nodes and pools

The staging cluster has one node pool, which makes things simple.
The production cluster has two, one for "core" pods (the hub, etc.)
and another dedicated to "user" pods (builds and user servers).
This strategy helps protect our key services from potential issues caused by users and helps us drain user nodes when we need to.

Since ~only user pods should be running on the user nodes,
cordoning that node should result in it being drained and reclaimed
after the max-pod-age lifetime limit
which often wouldn't happen without manual intervention.

It is still *not quite true* that only user pods are running on the user nodes at this point.
There can be some pods such as heapster and kube-dns that may run on user nodes,
and need to be manually removed from the pod after cordoning before the autoscaler will allow culling.

In the future, when we implement a pod packing strategy and node taints,
nodes could get reclaimed truly automatically without any intervention,
but we are not there yet.

Users and core pods are assigned to their pools via a `nodeSelector` in `config/prod.yaml`.
We use a custom label `mybinder.org/node-purpose = core | user`
to select which node a pod should run on.


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

### Exceptions on the OVH cluster

On the OVH cluster all the binder components use a specific certificate on `*.mybinder.ovh` domain.

Traffic for `ovh.mybinder.org` is redirected with a CNAME on `binder.mybinder.ovh`. That's why the OVH cluster should be able to serve 2 different certificates.

- The `*.mybinder.ovh` certificate is managed by ingresses in the ovh helm configuration.
- The `ovh.mybinder.org` certificate is managed by a specific ingress and `kube-lego` on the launch of `deploy.py` on the ovh stack.

## Secrets

Since we use this repo for deployment, it needs credentials for things like our
google cloud account, and secret tokens for our helm charts. Since this is a
public repo, we don't want these credentials to be readable in public! To solve
this, we use [git-crypt][] to store *encrypted* versions of files that should
be kept secret. These files are in the `secrets` folder. `git-crypt` uses a
shared secret to encrypt and decrypt files. For automated deployments, Travis
has access to the git-crypt secret in an encrypted environment variable. If you
don't need to edit the secret files, then you don't need the git-crypt secret,
or to see the contents of the secret files. When you clone, you will just have
the opaque, encrypted files. If you need access to view or edit the encrypted
files, you will need the git-crypt secret. See below for a procedure to share
the secret. Once you have unlocked the repo with `git-crypt`, you will be able
to view and edit the encrypted files as if they were any other file. `git-
crypt` handles the encryption and decryption transparently via git filters.


### Sharing secrets

Sharing secrets is tricky! There is a handy tool called [ssh-vault][] which
allows you to securely share information via a mechanism we all have available
here: ssh public keys on GitHub!

To securely share the git-crypt key, both parties should have git-crypt and
ssh-vault. On mac, these are both available from homebrew:

    brew install git-crypt ssh-vault

To encrypt the key with ssh-vault, pipe the key file through `ssh-vault
create`. Assuming you are in a mybinder.org-deploy directory that is already
setup with git-crypt:

```bash
[sender] $ cat .git/git-crypt/keys/default | ssh-vault -u receiver create
```

where `receiver` is the recipient's GitHub username, e.g. `willing` or
`choldgraf`.

The result should look something like this:

```
SSH-VAULT;AES256;30:40:9b:bd:16:26:f6:d2:1d:85:7a:dc:63:c9:e6:ae
LRCe3CrLL/isMhYVvA5gxZFCLCNyz64EepesTyKYklcMqUBZ1DML1rIXe4KBSudG
D9rbKP1PILGVaTHU2D2aSNJQUGNt3q+e3G8f5gpPJHvZeM9+mXKW4I3C8HfjU4sD
EKsm38ShYRAAtO5uTOToSd6j2vdakwEyO2YT7w2PTXiOL0VVeti7i9u+ENv1sxrg
oyAcN7tYA8Q/k3+zRy6ISJD8uEa/s9Igf99V0o7ocPpjON4oGsaLShuA8w0d3D+Y
kk0f1iBZ1k/0QoqPTL8JXjLh9Ba6o8TH6vi8rkZlmBrjDEg5cVlko/HadSnskQ/0
gW5CHn6XP0pIex59V9Tpiw==;dPQUIVgskPrYec3QqRqCrUkoRq1Ig5yOHihQJaS
EoTGNMwI=
```

The sender can deliver this encrypted copy to the receiver, via less secure
transport mechanism, such as a gitter private message, SMS, email, etc.

The receiver can now decrypt the message with ssh-vault and use it to unlock
the mybinder.org-deploy repo. Assuming the shared message has been saved to a
file `encrypted-key`:

```bash
[receiver] $ cat encrypted-key | ssh-vault view | git-crypt unlock -
# remove the encrypted temporary file
[receiver] $ rm encrypted-key
```

If your ssh key requries a passphrase then the above might not work. Below is a
method that works, but creates an intermediate file containing the human-readable
text. Make sure this file is secure and not discoverable by others!
If you have `ssh-vault` >= v0.12.4 you can run the following:

```
ssh-vault -o clear-git-crypt-key view encrypted-key
git-crypt unlock clear-git-crypt-key
rm clear-git-crypt-key
```

This solves the problem that `ssh-vault` prints the passphrase prompt to
standard out as well as the decrypted key. Make sure to delete `clear-git-crypt-key`,
which contains the clear text git-crypt key.

On a mac, you can use `pbcopy` and `pbpaste` to use the clipboard instead of
creating files:

```bash
[sender] $ cat .git/git-crypt/keys/default | ssh-vault -u receiver create | pbcopy
# the encrypted message is in sender's clipboard
# deliver it to the receiver, and once it is in their clipboard:
[receiver] $ pbpaste | ssh-vault view | git-crypt unlock -
```


### Who has the keys?

People who currently have the git-crypt secret include:

- @minrk
- @yuvipanda
- @betatim
- @choldgraf
- @mael-le-gal
- *add yourself here if you have it*

Contact one of them if you need access to the git-crypt key.


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
[git-crypt]: https://github.com/AGWA/git-crypt
[ssh-vault]: https://github.com/ssh-vault/ssh-vault
