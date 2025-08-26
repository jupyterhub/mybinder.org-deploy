# Getting started with the `mybinder.org` dev team

This page contains a starting point for people who would like to help
maintain the BinderHub deployment at <https://mybinder.org>.

## Make sure you have access on the Google Cloud project

Go to <https://console.cloud.google.com> and see if you have `binderhub` listed
in your projects. If not, message one of the Binder devs on [Jupyter instance of Zulip](https://jupyter.zulipchat.com/)
to get access.

## Install `kubectl`

To install `kubectl`, check out [Kubernetes Documentation / Tasks / Install Tools](https://kubernetes.io/docs/tasks/tools/#kubectl).

## Install Google Cloud CLI

To install `gcloud`, check out [Cloud SDK / Documentation / Guides / Install the Google Cloud CLI](https://cloud.google.com/sdk/docs/install-sdk).

Also, the installation of some [additional Google Cloud CLI components](https://cloud.google.com/sdk/docs/components#additional_components) are **required**:

- `gke-gcloud-auth-plugin`

## Configure Google Cloud CLI

When you run `gcloud init` for the first time, it'll ask you to authenticate
and to choose a project / default region. You should authenticate with
the email that's been given privileges to work on <https://mybinder.org>, choose
the project `binderhub`, and use the region `us-central1`.

:::{note}
You can also authenticate to Google Cloud using a service account.

```bash
gcloud \
    auth \
    activate-service-account \
    --key-file=secrets/key.json
```
:::

## Set up `kubectl` to connect to `mybinder.org`

Once you have `kubectl` installed, you can connect it with <https://mybinder.org>.
To do so, run the following command:

```bash
gcloud \
    container \
    clusters \
    get-credentials \
    prod \
    --zone us-central1 \
    --project binderhub-288415
```

Your `kubectl` will now be able to run commands with <https://mybinder.org>.

You can test this out by running:

```
kubectl --namespace=prod get pod
```

and a list of all running Binder pods should be printed.

### Connect to the staging deployment

Now that you're connected to `prod` it's time to connect to `staging`. To do so,
pull the staging credentials on to your local machine:

```
gcloud \
    container \
    clusters \
    get-credentials \
    staging \
    --zone us-central1-a \
    --project binderhub-288415
```

You can now switch between the `prod` and `staging` deployments by changing your
`kubectl` context.

## Look at the project Grafana

Another useful resource is the [mybinder.org Grafana dashboard](https://grafana.mybinder.org/?orgId=1).
This has information about the current state of the binder deployment. Take a
look at all of these plots and familiarize yourself with them. They're quite
useful in spotting and debugging problems in the future.

## Start helping out!

There are many ways that you can help debug/maintain/improve the `mybinder.org`
deployment. The best way to get started is to keep an eye on the [Jupyter instance of Zulip](https://jupyter.zulipchat.com/)
as well as the Grafana dashboard. If you see something interesting, don't hesitate
to ask questions or make suggestions!
