# 2018-07-08, too many pods

## Summary

Pod shutdown stopped functioning,
resulting in constant growth of pods,
eventually filling the cluster and new launches failing.
Total service disruption for Binder lasted for approximately five hours on a Saturday evening.

## Timeline

All times in CEST (UTC+2)

### 2018-07-08 ca. 18:30

Launch success drops to zero.

### 22:48

Suspicious behavior reported on gitter.

### 23:25

Investigation launched.
Cluster is full, scaled up to 8 nodes.
Almost 1k user pods are found (737 running, 240 waiting to be scheduled).
Pods older than 4 hours are deleted,
and some of the most-used images (such as ipython-in-depth)
are culled more aggressively.

After culling ~600 pods and restarting the Hub pod, launches are back to normal.

Some of the nodes allocated due to the flood of pods are cordoned to be reclaimed by the autoscaler.

Launches return to stable and European-timezone team retires for the night.

### 2018-07-09 08:00

Manual max-age culling frees up some of the remaining nodes.
Cluster is able to scale back to 3 nodes.

### 10:00

Investigating hub logs shows indications that the pod reflector has stopped receiving events ca 18:30 CEST, such as:

```
2018-07-07 18:32:27.000 CEST
TimeoutError: pod/jupyter-ipython-2dipython-2din-2ddepth-... did not disappear in 300 seconds!
2018-07-07 18:34:04.000 CEST
TimeoutError: pod/jupyter-bokeh-2dbokeh-2dnotebooks-... did not start in 300 seconds!
```

Shortly thereafter, pod deletion is skipped for pods that launch but are not in the pod reflector, presumably for the same reason they are skipped in the above:

```
2018-07-07 18:38:35.000 CEST
[W 2018-07-07 16:38:35.506 JupyterHub spawner:1476] No pod jupyter-ipython-2dipython-2din-2ddepth-... to delete. Assuming already deleted.
```

These pods _have_ started, but aren't registered in the pod reflector,
so in aborting the launch, the pod is not deleted.
This is the direct cause of the runaway pod growth,
though the root cause is that the pod reflector has stopped updating.

## Lessons learned

### What went well

- mybinder.org-deploy/scripts/delete-pods.py script was useful for bulk deleting older pods to get things back under control.
- once noticed, cluster returned to healthy within a few minutes.

List of things that went well. For example,

1. We were alerted to the outage by automated bots before it affected users
2. The staging cluster helped us catch this before it went to prod

### What went wrong

- pod reflector in kubespawner stopped receiving events,
  leading to total launch failure until the Hub was restarted.
- A compounding bug caused pods that the reflector failed to notice starting
  skipped deletion because they were assumed not to have been created in the first place.
- outage lasted a long time (five hours) before we noticed. We still don't have downtime notifications setup.
- cluster scale-down still involves several manual steps of cordoning and draining nodes.

## Action items

These are only sample subheadings. Every action item should have a GitHub issue
(even a small skeleton of one) attached to it, so these do not get forgotten.

### Process improvements

1. set up notifications of downtime ([issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/611))
2. automate scale-down ([issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/646))

### Documentation improvements

1. make sure downtime recovery steps are documented.
   They worked well this time,
   but not all team members may know the steps.
   ([issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/655))

### Technical improvements

1. Fix failure to delete pods when pod reflector fails
   ([pull request](https://github.com/jupyterhub/kubespawner/pull/208))
2. Make kubespawner more robust to pod-reflector failure
   ([issue](https://github.com/jupyterhub/kubespawner/issues/209))
3. Refactor event reflector to be a single reflector instead of one-per-pod.
   The new event reflectors were one major new feature in KubeSpawner,
   and may have been relevant to the failure (not clear yet)
   ([issue](https://github.com/jupyterhub/kubespawner/issues/210)).
4. try to auto-detect likely unhealthy Hub state and restart the Hub without manual intervention ([issue](https://github.com/jupyterhub/jupyterhub/issues/2028))
