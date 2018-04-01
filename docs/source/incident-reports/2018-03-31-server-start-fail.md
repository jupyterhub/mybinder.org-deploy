# 2018-03-31, Server launch failures

## Summary

After a few days of general sub-optimal stability and some strange networking errors, a node was deleted. This caused a more general outage that was only solved by totally recycling all nodes.

[link to Gitter incident start](https://gitter.im/jupyterhub/binder?at=5ac010032b9dfdbc3a421980)

## Timeline

All times in PST

### 2018-03-31 15:47

Problem is identified

* Launch success rate drops quickly
* Many pods stuck in "Terminating" and "ContainerCreating" state.
* Hub pod is showing many timeout errors.


### 16:11

* Mount errors on build pods:

```
Events:
  Type     Reason                 Age                From                                           Message
  ----     ------                 ----               ----                                           -------
  Normal   Scheduled              5m                 default-scheduler                              Successfully assigned build-devvyn-2daafc-2dfield-2ddata-6e8479-c1cecc to gke-prod-a-ssd-pool-32-134a959a-p2kz
  Normal   SuccessfulMountVolume  5m                 kubelet, gke-prod-a-ssd-pool-32-134a959a-p2kz  MountVolume.SetUp succeeded for volume "docker-socket"
  Warning  FailedMount            4m (x8 over 5m)    kubelet, gke-prod-a-ssd-pool-32-134a959a-p2kz  MountVolume.SetUp failed for volume "docker-push-secret" : mkdir /var/lib/kubelet/pods/e8d31d4e-3537-11e8-88bf-42010a800059: read-only file system
  Warning  FailedMount            4m (x8 over 5m)    kubelet, gke-prod-a-ssd-pool-32-134a959a-p2kz  MountVolume.SetUp failed for volume "default-token-ftskg" : mkdir /var/lib/kubelet/pods/e8d31d4e-3537-11e8-88bf-42010a800059: read-only file system
  Warning  FailedSync             55s (x24 over 5m)  kubelet, gke-prod-a-ssd-pool-32-134a959a-p2kz  Error syncing pod
```


### 17:21

* Decided to increase cluster size to 4, wait for new nodes to come up, then cordon the two older nodes


### 17:30

* New nodes are up, old nodes are drained
* Hub / binder pods show up on new nodes
* Launch success rate begins increasing
* Launch rate goes back to 100%

## Lessons learnt

### What went well

1. The problem was eventually resolved

### What went wrong

1. It was difficult to debug this problem as there was no obvious error message, and the person solving the problem wasn't sure how to debug.

## Action items

### Investigation

The outage seemed to come from the deletion of a node, but it seemed to be related to other pre-existing nodes as well. Perhaps this is a general thing that happens when nodes become too old?

### What went wrong

* There was a major outage that we were unable to debug, there were not clear errors in the logs
* There was only one person available to debug, which made it more difficult to know how to proceed withot any feedback

### Process improvements

1. Improve the alerting so that a majority of the team is notified when there's an outage. (currently blocking on [#365](https://github.com/jupyterhub/mybinder.org-deploy/issues/365))
2. Come up with team guidelines for how "stale" a node can become before we intentionally recycle it. ([#528](https://github.com/jupyterhub/mybinder.org-deploy/issues/528))

### Documentation improvements

1. Document how to "recycle" nodes properly ([#528](https://github.com/jupyterhub/mybinder.org-deploy/issues/528))
