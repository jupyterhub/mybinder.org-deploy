# Getting started with local development

This page contains a starting point for people who want to know more about the BinderHub deployment by playing around with a local development instance running on Kubernetes with [Docker Desktop](https://docs.docker.com/desktop/).

## Install Docker Desktop

Install Docker Desktop on [Mac](https://docs.docker.com/desktop/setup/install/mac-install/), [Windows](https://docs.docker.com/desktop/setup/install/windows-install/), or [Linux](https://docs.docker.com/desktop/setup/install/linux/). And [turn on Kubernetes](https://docs.docker.com/desktop/features/kubernetes/#install-and-turn-on-kubernetes).

## Set up `kubectl` to connect to Docker Desktop

You can connect `kubectl` with Docker Desktop.
To do so, run the following command:

```
kubectl config use-context docker-desktop
```

You can test this out by running:

```
kubectl get -A pods
```

and a list of all running pods should be printed.
