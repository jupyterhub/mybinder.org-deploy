# 2018-04-18, Culler flood

A deploy of updates to the Hub included an upgraded implementation of the idle-culler script and an update to kubespawner.
The culler script had a bug which resulted in flooding the Hub with requests to stop servers that aren't running.
Additionally, a resource leak was introduced in the update to kubespawner,
which caused JupyterHub to become unresponsive after launching a certain
number of servers.
As a result, Binder service was degraded with periodic outages of 10-30 minutes.

## Timeline

All times in CEST

### 2018-04-18 12:35

Upgrade of jupyterhub, binderhub charts is deployed. Tests pass and builds and launches are working.

### ~13:30-13:45

Launch success drops to zero.

### 14:29

Binder outage is reported on Gitter by @jakamkon, investigation is started.

JupyterHub is determined to be inaccessible. Suspecting network issues, the proxy pod is restarted.
This does not resolve the issue, so the nginx-ingress pods are restarted.
This also does not resolve the issue.
Upon discovering that the proxy-patches endpoint is responsive (by manually visiting https://hub.mybinder.org/user/doesntexist).
This endpoint working means that the proxy and ingress are both working,
and it is only the Hub itself that is not responsive.
The hub pod is restarted, and launches quickly return back to 100% success rate.

### 14:49

After returning the deployment to working order, the logs of the Hub pod around the start of the outage (~13:30) are investigated.
The logs show a large and increasing volume of 400 errors in the culler,
indicating that the recent changes in the culler may be responsible.
This suggests that an outage will recur in a similar amount of time after restarting the Hub.

Coincidence: a [pull request](https://github.com/jupyterhub/jupyterhub/pull/1807) had just been merged, fixing bugs in the culler.
It is suspected that these are exactly the bugs responsible for the outage.

The process to deploy a change to mybinder.org begins:

### 14:43

[apply changes to jupyterhub chart](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/pull/655)

### 14:55

[pull updated jupyterhub into binderhub chart](https://github.com/jupyterhub/binderhub/pull/526)

### 15:36

[deploy to mybinder.org](https://github.com/jupyterhub/mybinder.org-deploy/pull/562)

The final deploy has to be resubmitted multiple times before it succeeds.
This is in part because the culler bug resulted in a failure to delete users,
so users were constantly accumulating.
The large number of users meant the updated Hub took a long time to deploy.
When the new culler arrived it began to cull the old users,
of which there were many.
The sustained deletions also put a lot of load on the Hub,
but a one-time cost because the deletions succeeded this time.

Hub behavior is believed to have returned to normal.

### 17:03

Believing the issue to be resolved, work resumes,
merging new pull requests into binderhub.

### 17:23

Observing culler behavior is fixed, but memory and CPU growth continues.
Reviewing further changes that were part of the revised deploy,
a new feature of kubespawner is suspected as the source of the leak.
The process begins to deploy reverting this change.
Since this is a zero-to-jupyterhub change, it will again take an hour to propagate to mybinder.org

### 19:47

Latest deploy is attempted to mybinder.org.
Deploying to master fails due to a bug in the newly introduced image culler.
Updates are reverted to the last-known-working configuration.

### 19. April, 11:00

Fix for image-culler bug that prevented the previous deploy is [applied](https://github.com/jupyterhub/binderhub/pull/530)
and [deployed](https://github.com/jupyterhub/mybinder.org-deploy/pull/567).

### 11:07

This deploy is successful except on production,
due to another bug in the image cleaner.

This time, the image cleaner is disabled by
[setting the inode threshold to 0](https://github.com/jupyterhub/mybinder.org-deploy/pull/568) without reverting other changes.

### 11:27

Deploy is successful, but took close to half an hour.
Memory leak is not fixed.

### 11:47

To avoid reverting more large deploys,
only the hub image is [reverted to the last known good version](https://github.com/jupyterhub/mybinder.org-deploy/pull/569).

After reverting the hub image update, everything is okay again.

### 11:58

On investigation of logs, it appears that the Hub was not fully upgraded to its target version.
The cause for this is still unknown,
but could be the result of manual interactions with the cluster during the upgrade.

The pinning of the hub image is [reverted](https://github.com/jupyterhub/mybinder.org-deploy/pull/570)
and everything is now up-to-date.
It is observed that the memory leak does not recur,
confirming that the kubespawner update is the root cause.

## Lessons learned

- It takes about an hour to deploy a change to zero-to-jupyterhub all the way to
  mybinder.org. This is because we must wait for the tests in all repositories to
  run twice: once to verify the pull request, then again after merge before
  publishing the chart. Since these tests each take ~10 minutes, that's 40
  minutes of waiting, not counting the human time of observing one success and
  submitting the next pull request.
- Culler behavior is not covered by tests.
  This is difficult, since the culler accumulates tasks over time,
  but some basic test coverage should be possible.
- Image cleaner is not covered by tests.
- Deploying many changes at once makes it more challenging to identify the causes of regressions.
- Since so many of these deployment processes take a very long time,
  even if a fix is known, reverting a bad version and waiting for the new one
  may often be preferable to keeping the degraded state while the fix propagates.
  The downside of doing this is that large (many services changed) deploys
  can take a long time as rolling updates are performed.
  Reverting a large deploy can result in significant downtime
  during the revert.
- Three separate bugs were introduced and resolved in this process:
  1. flood bug in updated culler
  2. memory leak bug in updated kubespawner
  3. failure-to-start bug in new image-cleaner
     More granular continuous deployments would have allowed us to find and catch
     each of these issues one at a time.
     On the other hand, deploying at dedicated, less frequent times
     would allow the team to be prepared to handle and respond to the update process,
     rather than reacting to issues as they are deployed throughout the week.

## Action items

- Revisit automatic pull requests to encourage keeping
  mybinder.org up-to-date with smaller, more-frequent changes
  ([Issue](https://github.com/jupyterhub/binderhub/pull/222))
- Add alarms for sustained high CPU and memory usage from JupyterHub and BinderHub pods. Related to [this issue](https://github.com/jupyterhub/mybinder.org-deploy/pull/527)
- Figure out tests for the culler (this may be part of splitting out the culler into its own package)
  ([Issue](https://github.com/jupyterhub/jupyterhub/issues/1791))
- Fix bugs in image-culler preventing it from running
  ([PR](https://github.com/jupyterhub/binderhub/pull/534))
- Allow disabling image culler in helm chart
- Investigate and fix memory leak in kubespawner
  ([Issue](https://github.com/jupyterhub/kubespawner/issues/165))
- Describe process for deploying jupyterhub image bumps to mybinder.org as short-term fixes during an incident?
