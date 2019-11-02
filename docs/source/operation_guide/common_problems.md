# Common problems and their solutions

This is a page to list a few of the common problems that we run into during
operation of `mybinder.org`, and some common solutions that solve these
problems. In general, **manual intervention** is something that we should
avoid requiring, but sometimes it is necessary. This page serves as a helpful
guide for people maintaining `mybinder.org`, and an informal list of things
we should design new technology to fix.

## The Docker-in-Docker socket

When using Docker-in-Docker, there is a chance that `dind` hasn't started when a
build is requested. If this happens, the volume mount to load
`/var/run/dind/docker.sock` into the build container may occur before `dind`
has created the socket. If this happens, the volume mount will create a
directory at the mount point (which we don't want to happen). If this happens,
Docker-in-Docker will be inaccessible until `/var/run/dind` is manually deleted
and the `dind` pod is restarted.

### How to spot the problem

Build pods will not be working, and the `dind` pods are stuck in `CrashLoopBackoff`.

### How to resolve the problem

1. Find out which node contains the crashing `dind` pod (aka, the node that has
   *folder* in `/var/run/dind/docker.sock` rather than the socket file).
   You can do so by running:

       kubectl --namespace=<ns> get pod -o wide

2. Once you find the node of interest, SSH into it with:

       gcloud compute ssh <nodename>

3. Manually delete the `docker.sock` folder from the node.

       sudo rm -rf /var/run/dind/docker.sock/

4. Delete the `dind` pod (k8s will automatically create a new one)

       kubectl --namespace=<ns> delete pod <dind-pod-name>

## Networking Errors

Sometimes there are networking errors between pods, or between one pod and
all other pods. This section covers how to debug and correct for networking
on the Kubernetes deployment.

### Manually confirm network between pods is working

To confirm that binderhub can talk to jupyterhub, to the internet in general, or
you want to confirm for yourself that there is no connectivity problem between
pods follow this recipe.

1. connect to the pod you want to use as "source", for example the jupyterhub
pod: `kubectl --namespace=prod exec -it hub-989cc9bd-bbkbk /bin/bash`
1. start `python3`, `import requests`
1. use `requests.get(host)` to check connectivity. Some interesting hostnames
   to try talking to are:
    * http://binder/, the binderhub service
    * http://hub:8081/hub/api, the jupyterhub API
    * http://proxy-public/hub/api, the CHP route that redirects you to the
      jupyterhub API (content of the response should be equal)
    * http://google.com/, the internet
    * the CHP API needs a token so run: `headers={'Authorization': 'token ' + os.environ['CONFIGPROXY_AUTH_TOKEN']}`
      and then`requests.get('http://proxy-api:8001/api/routes', headers=headers)`
    * Other hostnames within the Kubernetes deployment. To find out hostnames
      to try look at the `metadata.name` field of a kubernetes
      service in the helm chart. You should be able to connect to each of them using
      the name as the hostname. Take care to use the right port, not all of them are
      listening on 80.

Here's a code snippet to try all of the above in quick succession:

```python
import requests
import os
urls = ["binder/", "hub:8081/hub/api", "proxy-public/hub/api", "google.com/"]
for url in urls:
    resp = requests.get("http://" + url)
    print('{}: {}'.format(url, resp))
```

### Spikes in traffic

Spikes in traffic can cause congestion, slowness, or surface bugs in the
deployment. Here are some ways to detect spikes.

#### Spikes to `mybinder.org`

Spikes to `mybinder.org` are most-easily detected by going to the project's
Google Analytics page. Look at the "real-time" page and see if there is a big
shift from typical patterns of behavior.

#### Spikes to the `/build` API

Sometimes there are spikes to the BinderHub build API, which we cannot capture
with Google Analytics. Spikes to the build API usually come from a single
repository, and can be found with the following command.

To list the API requests to `/build`:

```python
kubectl --namespace=prod logs -l component=controller | grep '/build'
```

and to list the number of API requests to `/build` that contain a particular
word:

```python
kubectl --namespace=prod logs -l component=controller | grep '/build' | grep <word-name> | wc -l
```
