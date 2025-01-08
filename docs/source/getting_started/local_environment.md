# Getting started with local development

This page contains a starting point for people who want to know more about the BinderHub deployment by playing around with a local development instance.

## Local Kubernetes

You will need a local Kubernetes cluster. A few options are

- [Kubernetes with Docker Desktop](https://docs.docker.com/desktop/features/kubernetes/) (recommended)
- [minikube](https://minikube.sigs.k8s.io/docs/)
- [k3d](https://k3d.io/stable/)
- [kind](https://kind.sigs.k8s.io/)

### Install Docker Desktop

Install Docker Desktop on [Mac](https://docs.docker.com/desktop/setup/install/mac-install/), [Windows](https://docs.docker.com/desktop/setup/install/windows-install/), or [Linux](https://docs.docker.com/desktop/setup/install/linux/). And [turn on Kubernetes](https://docs.docker.com/desktop/features/kubernetes/#install-and-turn-on-kubernetes).

## Set up `kubectl`

To do so, run the following command:

```
kubectl config use-context k8s-context-name
```

If using Docker Desktop, `k8s-context-name` is `docker-desktop`.

You can test this out by running:

```
kubectl get -A pods
```

and a list of all running pods should be printed.

## Deploy Harbor

Run the following command:

```
helm repo add harbor https://helm.goharbor.io
```

```
helm install harbor harbor/harbor
```

## Deploy mybinder.org

Run the following command:

```
source cert-manager.env
```

```
for d in ./mybinder*/; do
    helm dependency update "$d"
done
```

```
python deploy.py localhost
```