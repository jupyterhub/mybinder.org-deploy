# Getting started with the `mybinder.org` dev team

This page contains a starting point for people who would like to help
maintain the BinderHub deployment at `mybinder.org`.

## Make sure you have access on the Google Cloud project

Go to `console.cloud.google.com` and see if you have `binder-prod` listed
in your projects. If not, message one of the Binder devs on the [Gitter Channel](https://gitter.im/jupyterhub/binder)
to get access.

## Install `kubectl` and the `gcloud` SDK

The most important tool for keeping an eye on the Kubernetes deployment is
`kubectl` and the `gcloud` SDK. These will let you run queries on the
`mybinder.org` deployment from your command line. To set this up, check
out the [Zero to JupyterHub Google SDK section](https://zero-to-jupyterhub.readthedocs.io/en/latest/create-k8s-cluster.html#setting-up-kubernetes-on-google-cloud).
(everything before the part where you create a google cloud cluster).

When you run `gcloud init` for the first time, it'll ask you to authenticate
and to choose a project / default region. You should authenticate with
the email that's been given privileges to work on `mybinder.org`, choose
the project `binder-prod`, and use the region `us-central1-a`.

We recommend enabling [`kubectl` autocompletion](https://kubernetes.io/docs/tasks/tools/install-kubectl/#enabling-shell-autocompletion)
as well.

## Set up `kubectl` to connect to `mybinder.org`

Once you have `kubectl` installed, you can connect it with `mybinder.org`.
To do so, run the following command:

```
gcloud container clusters get-credentials prod-a --zone us-central1-a --project binder-prod
```

This will open a log-in page in your browser. If you've got access, you'll
be able to log in and your `kubectl` will now be able to run commands
with `mybinder.org`.

You can test this out by running:

```
kubectl --namespace=prod get pod
```

and a list of all running Binder pods should be printed.

## Look at the project Grafana

Another useful resource is the [mybinder.org Grafana dashboard](https://grafana.mybinder.org/?orgId=1).
This has information about the current state of the binder deployment. Take a
look at all of these plots and familiarize yourself with them. They're quite
useful in spotting and debugging problems in the future.

## Start helping out!

There are many ways that you can help debug/maintain/improve the `mybinder.org`
deployment. The best way to get started is to keep an eye on the [Gitter Channel](https://gitter.im/jupyterhub/binder)
as well as the Grafana dashboard. If you see something interesting, don't hesitate
to ask questions or make suggestions!
