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
