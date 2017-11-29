# 2017-10-17, Cluster Full

## Summary

Users were reporting failed launches after building. This was caused by the cluster being full & hitting our autoscaling 'upper' limit. Due to the launch timeout being too small + a bug in KubeSpawner, pods kept getting started & then orphaned, leading to cluster being full. We increased the timeout and cleaned out the cluster, which has temporarily fixed the problem.

## Timeline

All times in PST

### 2017-10-17 07:42

Users report all launches are failing with a 'took too long to launch' error

### 08:47

Investigation starts, and the cluster is full - there are 94 pending pods and a full ten nodes.

### 09:14

All pending pods are deleted, but the cluster is still full and new launches are still failing. This is attributed to KubeSpawner not really cleaning up after itself - if a spawn fails, KubeSpawner should kill the pod, rather than let it stay in whatever state it was in. This leads to 'orphan' pods that won't be cleaned up, since JupyterHub has lost track of these pods.

This is made worse by the low timeout on launches in binderhub - except when the launch fails, we don't kill the server. This leads to servers that are launched after the timeout, so users never see it. This is still kept track of by JupyterHub, but users never use these pods.

### 09:19

A [PR](https://github.com/jupyterhub/binderhub/pull/188) is made to bump up the timeout, since that is what is making the problem unmanageable right now. This is delayed by a GitHub service degradation (PRs do not update for a while).

### 09:49

GitHub is usable again, and the PR gets merged.

### 10:18

A deployment to staging is attempted, but fails test because Cluster is still full. Deployment to staging is reverted.

### 11:02

Cluster is entirely cleaned out with a `kubectl --namespace=beta delete pod --all`. This is disruptive to current users, but is the easiest way to get cluster capacity again.

### 11:14

Launch timeout bump (to about 10mins) is deployed again [1](https://github.com/jupyterhub/mybinder.org-deploy/pull/89) [2](https://github.com/jupyterhub/mybinder.org-deploy/pull/90)

### 11:29

The [cluster autoscaler](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler) kicks in, resizing the cluster down to about 4 nodes.

Everything is fine and builds / launches are working again.

## Action items

### KubeSpawner

1. If a pod doesn't start in time, kubespawner should kill it. If it enters error state, kubespawner should kill it. In general, it should never 'orphan' pods. [Issue](https://github.com/jupyterhub/kubespawner/issues/95)

### BinderHub

1. Make the launch timeout more configurable, and specified in seconds [Issue](https://github.com/jupyterhub/binderhub/issues/244)
2. If launch fails, then BinderHub should actually call stop on the server & try to stop the server if it is running. [Issue](https://github.com/jupyterhub/binderhub/issues/245)

### Process

1. We need better alerting for when cluster is full, ideally before it is full! [Issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/125)
