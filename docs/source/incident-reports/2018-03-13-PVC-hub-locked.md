# 2018-03-13, PVC for hub is locked

## Questions for follow up

-

## Summary

After a few hours we noticed that JupyterHub wasn't
spawning any new users. Upon investigation it seemed that
some nodes had gone bad. The JupyterHub pod was on one such node,
but wasn't being deleted properly. Since it wasn't culled, it couldn't "release" the PVC
that contained the hub db, which meant that new hub pods
could not access the db, resulting in the outage.

[link to Gitter incident start](https://gitter.im/jupyterhub/binder?at=5aa76f7de4ff28713a26bf63)

## Timeline

All times in CET

### 2018-03-13 07:28

Problem is identified

- mybinder launch success rate has been at zero for several hours now [https://grafana.mybinder.org/dashboard/db/main-dashboard?refresh=1m&orgId=1&panelId=17&fullscreen&from=1520900905664&to=1520922505664](https://grafana.mybinder.org/dashboard/db/main-dashboard?refresh=1m&orgId=1&panelId=17&fullscreen&from=1520900905664&to=1520922505664)
- lots of pods are in state "Unknown" and "NodeLost"
- pods in weird states are on at least these nodes `10.128.0.7` `10.128.0.5`

### 07:33

Attempts to cordon bad nodes to see if this helps things.

- `kubectl cordon gke-prod-a-ssd-pool-32-134a959a-n2sk` and `kubectl cordon gke-prod-a-ssd-pool-32-134a959a-6`hmq
- the hub pod (`hub-65d9f46698-dj4jb`) was in state `Unknown` and a second hub pod (`hub-65d9f46698-dmlcv`) in `ContainerCreating` since 5h -> deleted both to see if this reschedules them on a healthy node

### 07:39

- bhub pod can't talk to the jhub pod, but it can connect to google.com and github.com
- starting a new jhub pod is failing because the PVC is still claimed by another old pod, presumably that old pod is dead/lost in action and hence not releasing the claim

### 07:59

- manually deleted all pods on node `-n2sk`, will this help the node to release the PVC?
  - (it does not)
- manually reset `gke-prod-a-ssd-pool-32-134a959a-n2sk` in the hope that this will force the release of the PVC. This is done in the GCP web user-interface

### 08:05

- `hub-65d9f46698-454cf` is now pulling its docker image, scheduled on `gke-prod-a-ssd-pool-32-134a959a-1j33`
- pod successfully scheduled and launched. running again, and the `binder-examples/r` repo successfully launches
- persistent plot of launch success rate dropping to zero https://grafana.mybinder.org/render/dashboard-solo/db/main-dashboard?refresh=1m&orgId=1&from=1520881680522&to=1520924880522&panelId=17&width=1000&height=500&tz=UTC%2B01%3A00

### 08:11

General cleanup because many pods are not identified by k8s. Deleting all pods in "Unknown" state.

### 08:17

- deleting pods in Unknown state does not seem to do anything. Pods remain listed.
- we assume the reason the pod is marked as "Unknown" is because k8s can't find out anything about it, which explains why it can't delete it. We will have to investigate what to do about those pods. Restarting the node seems to remove them but that feels pretty heavy handed

### 13:32

We realize that many other services are down, because they're running on pods that were attached to failed nodes.

The pods are in stated `Unknown` or `NodeLost`

### 13:34

Discovered that we can force-delete pods
in this state with:

`kubectl --namespace=prod delete pod <pod-name> --grace-period=0 --force`

Ran this code snippet to do so for all pods:

```python
from subprocess import check_output

out = check_output('kubectl get pod -o wide --namespace=prod'.split())
lines = out.decode().split('\n')
lines = [ii.split() for ii in lines]

df = pd.DataFrame(lines[1:], columns=lines[0])
lost_df = df.query('STATUS in ["Unknown", "NodeLost"]')

for nm in lost_df['NAME'].values:
    cmd = 'kubectl --namespace=prod delete pod {} --grace-period=0 --force'.format(nm)
    print('Deleting pod {}'.format(nm))
    check_output(cmd.split())

```

This deleted all pods that were in `Unknown` or
`NodeLost` state. Services run on these pods then recovered.

### 2018-03-21 06:30

We discover that another node has entered "NodeLost" state. Grafana and Prometheus are both down as they are on this node. Many pods are in state "Unknown" or "NodeLost".

### 2018-03-21 06:31

Run:

- `kubectl cordon gke-prod-a-ssd-pool-32-134a959a-bmsw`
- `deleting all pods on the lost node, w/ state "NodeLost" or "Unknown"`

The grafana/prometheus pods that were _trying_ to start before still didn't (they had been in that state for many hours) so we deleted those pods to see if new ones worked.

This resolved the issue, however it deleted the prometheus data collected up to that point.

## Lessons learnt

### What went well

1. Once the issue was identified, the steps taken to resolve this problem were logged well and quickly escalated in their heavy-handedness as necessary. There was minimal hub downtime once the issue was identified.

### What went wrong

1. It took quite some time before we noticed this error. This is strange because we did not get a stackdriver email about this. The stackdriver emails seem to get marked as spam and the notification about this arrives hours later.

## Action items

### Investigation

Why did this outage start in the first place? Was there a rouge pod? GCE outage? This kind of major outage should not "just happen". Read Stackdriver logs, check Google cloud incidents, other ideas.

### Process improvements

1. Make sure we have a non-stackdriver alerting service so we can catch these issues earlier (currently blocking on [#365](https://github.com/jupyterhub/mybinder.org-deploy/issues/365))

### Documentation improvements

1. Document how to check if a PVC hasn't been released so we can quickly identify this problem in the future.
2. Document how to manually restart a node if commands in general aren't working.
3. Document how to delete pods that have entered an "Unknown" state so k8s doesn't totally miss them. ([#512](https://github.com/jupyterhub/mybinder.org-deploy/pull/512))

### Technical improvements

1. Store the prometheus data somewhere more stable than its server pod. Otherwise whenever this pod restarts, we lose all the data.
