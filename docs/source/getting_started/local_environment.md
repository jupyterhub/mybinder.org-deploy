# Getting started with local development

This page contains a starting point for people who want to know more about the BinderHub deployment by playing around with a local development instance.

## Local Kubernetes

You will need a local Kubernetes cluster. A few options are

- [K3s](https://k3s.io/)
  - [Kubernetes with Rancher Desktop](https://www.rancher.com/products/rancher-desktop)
- [minikube](https://minikube.sigs.k8s.io/docs/)
- [k3d](https://k3d.io/stable/)
- [kind](https://kind.sigs.k8s.io/)
  - [Kubernetes with Docker Desktop](https://docs.docker.com/desktop/features/kubernetes/)

### Install Docker Desktop

Install Docker Desktop on [Mac](https://docs.docker.com/desktop/setup/install/mac-install/), [Windows](https://docs.docker.com/desktop/setup/install/windows-install/), or [Linux](https://docs.docker.com/desktop/setup/install/linux/). And [turn on Kubernetes](https://docs.docker.com/desktop/features/kubernetes/#install-and-turn-on-kubernetes).

## Set up `kubectl` to connect to Kubernetes

Once you have `kubectl` installed, you can connect it with your local Kubernetes.
To do so, run the following command:

```bash
kubectl config use-context k8s-context-name
```

If using Docker Desktop, `k8s-context-name` is `docker-desktop`.

You can test this out by running:

```bash
kubectl get -A pods
```

and a list of all running pods should be printed.

## Deploy mybinder.org to Kubernetes

Run the following command:

```bash
source cert-manager.env
```

```bash
for d in ./mybinder*/; do
    helm dependency update "$d"
done
```

```bash
chartpress --skip-build
```

`deploy.py` requires your IP address (represented by `xxx.xxx.xxx.xxx` in the next command).

```bash
python deploy.py localhost --local-ip xxx.xxx.xxx.xxx
```

## Access your mybinder.org

Open http://localhost with your favourite web browser.
