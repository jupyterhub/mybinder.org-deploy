# 2018-02-20, JupyterLab Announcement swamps Binder

## Summary

The JupyterLab [announcement post](https://blog.jupyter.org/jupyterlab-is-ready-for-users-5a6f039b8906) drove a great deal of traffic to mybinder.org.
This caused several outages throughout the day from varying causes.


We prepared for this by temporarily increasing the mininum number of nodes.

After a deployment, most users were getting "Failed to create temporary user for gcr.io/binder-prod/" when attempting to launch their image. This was caused by a small bug that manifests only when large numbers of users are using Binder at the same time. The bug was identified and fixed, but due to logistical issues it caused mybinder to be unusable for about 1h50m, and unstable for ~1 day.

## Timeline

All times in CET (GMT+1)

### Feb 20 2018 14:17

JupyterLab announcement blog post goes live via medium, twitter. At this point, the per-repo limit is 300.

### 14:55

Autoscaling increases node count to 4 from 3 as intended. This results in a
slight increase in launch backlog while the new node is prepared (and the
jupyterlab image is pulled)

### 15:05

Autoscaling increases node count to 5. JupyterLab is very popular! Grafana
shows that JupyterLab is heading very quickly for the 300 limit. It is decided
to raise the per-repo limit to 500.

### 15:08

JupyterLab hits the rate limit of 300 and Grafana starts listing failed builds
due to the per-repo limit. The rate limit is behaving as intended.

[Action Item] launches that are rejected due to rate limiting are registered as a
'failed launch' in our launch success metric. This should instead be its own label.


### 15:10

[PR #428](https://github.com/jupyterhub/mybinder.org-deploy/pull/428) increases the per-repo limit to 500.

### 15:15

Deployment of PR #428 to production fails on Travis due to a timeout waiting for `helm upgrade` on prod. The `binder` pod never became available.

The travis deployment is restarted.

### 15:20

Travis deployment fails again, this time hanging during grafana annotation.
It is discovered that the grafana pod is unhealthy:

```
$ kubectl describe pod grafana...
Events:
  Type     Reason          Age              From                                           Message
  ----     ------          ----             ----                                           -------
  Warning  Unhealthy       2m               kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Readiness probe failed: Get http://10.12.8.137:3000/login: dial tcp 10.12.8.137:3000: getsockopt: connection refused
  Warning  FailedSync      2m               kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Error syncing pod
  Warning  Failed          2m               kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Error: failed to start container "grafana": Error response from daemon: cannot join network of a non running container: 8babe89dbb28ea4c09f5490797b8bb2bd4e6298a8d79a04b8653febed86fec19
  Warning  Unhealthy       1m               kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Readiness probe failed: Get http://10.12.8.137:3000/login: net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
  Normal   SandboxChanged  1m               kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Pod sandbox changed, it will be killed and re-created.
  Normal   Pulling         1m (x4 over 4h)  kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  pulling image "grafana/grafana:4.6.3"
  Normal   Pulled          1m (x4 over 4h)  kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Successfully pulled image "grafana/grafana:4.6.3"
  Normal   Started         1m (x3 over 4h)  kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Started container
  Normal   Created         1m (x4 over 4h)  kubelet, gke-prod-a-ssd-pool-32-134a959a-vvsw  Created container
```

The grafana pod is deleted, as is the `binder` pod that failed to start.

### 15:32

Travis is retried once more, and succeeds this time.

Launch success begins to climb as JupyterLab pods rise from 300 to the new limit of 500.

Grafana pod dies and is restarted multiple times. This time by Kubernetes without intervention.

### 16:00

JupyterLab has hit the 500 user limit and is  ?????
After returning to working order, ????

### 16:05

Launch success rate is at 0%. Something is wrong beyond load.

### 16:18

Hub is restarted to attempt to clear out bad state via `kubectl delete pod`

The hub comes back and promptly culls many inactive pods. However, there appears to be a problem in the culler itself. Every cull request fails due to 400 requests asking for an already-stopping server to stop again, resulting in the culler exiting. **The culler shouldn't exit when there is an error**


### 16:29

restart both hub and proxy pods

Everything's still failing. Binder requests to the Hub are failing with a timeout:

```
[E 180220 15:32:35 launcher:93] Error creating user jupyterlab-jupyterlab-demo-gjvedw6o: HTTP 599: Timeout while connecting

[W 180220 15:32:35 web:1588] 500 GET /build/gh/jupyterlab/jupyterlab-demo/18a9793b58ba86660b5ab964e1aeaf7324d667c8 (10.12.8.27): Failed to create temporary user for gcr.io/binder-prod/r2d-fd74043jupyterlab-jupyterlab-demo:18a9793b58ba86660b5ab964e1aeaf7324d667c8
```


### 16:33

BinderHub is restarted, in case there is an issue in BinderHub itself.

After this restart, launches begin to succeed again. It appears that BinderHub was unable to talk to JupyterHub. It could be that the tornado connection pool was draining (this has happened before due to [a tornado bug](https://github.com/tornadoweb/tornado/pull/1582)).

It could also have been a kubernetes networking issue where pod-networking is no longer working.


### 16:40

Grafana pod restarted itself again. No indication as to why, but it could just be being reassigned to new nodes as the cluster resizes. 

In hindsight, it is most likely because it only requests 100Mi of RAM and nothing more.

### 16:55

Launches begin failing again with the same 599: Timeout errors

### 17:00-18:00

Since BinderHub is reaching a timeout after several requests to the hub have accumulated

### 18:03

- cull jupyterlab pods older than 2 hours (103 pods)
- install pycurl on binderhub, which has been known to fix some timeout issues on jupyterhub underload
- revert per-repo limit back to 300 pods


### 18:10

Travis deployment [fails tests on prod](https://travis-ci.org/jupyterhub/mybinder.org-deploy/builds/343924455):

```
def test_hub_up(hub_url):
        """
        JupyterHub url is up and returning sensible result (403)
        """
        resp = requests.get(hub_url)
        # 403 is expected since we are using nullauthenticator
        # FIXME: Have a dedicated health check endpoint for the hub
>       assert resp.status_code == 403
E       assert 504 == 403
E        +  where 504 = <Response [504]>.status_code
```

due to networking failure on a node, but we don't know that yet.

(Note: I suspect this is due to JupyterHub being too busy, not because of node failure)

### 18:22

pycurl PR is reverted due to suspicion that it caused Service Unavailable errors.
It turns out this is not the case, the Hub really was unavailable due to bad networking state on at least one node.


Hub logs show:

```
[E 2018-02-20 17:18:21.889 JupyterHub app:1623]
    Traceback (most recent call last):
      File "/usr/local/lib/python3.6/dist-packages/jupyterhub/app.py", line 1620, in launch_instance_async
        yield self.initialize(argv)
      File "/usr/lib/python3.6/types.py", line 184, in throw
        return self.__wrapped.throw(tp, *rest)
      File "/usr/local/lib/python3.6/dist-packages/jupyterhub/app.py", line 1382, in initialize
        yield self.init_spawners()
      File "/usr/local/lib/python3.6/dist-packages/jupyterhub/app.py", line 1210, in init_spawners
        self.users[orm_user.id] = user = User(orm_user, self.tornado_settings)
      File "/usr/local/lib/python3.6/dist-packages/jupyterhub/user.py", line 178, in __init__
        self.spawners[name] = self._new_spawner(name)
      File "/usr/local/lib/python3.6/dist-packages/jupyterhub/user.py", line 208, in _new_spawner
        spawner = spawner_class(**spawn_kwargs)
      File "/usr/local/lib/python3.6/dist-packages/kubespawner/spawner.py", line 83, in __init__
        self.api = client.CoreV1Api()
      File "/usr/local/lib/python3.6/dist-packages/kubernetes/client/apis/core_v1_api.py", line 35, in __init__
        api_client = ApiClient()
      File "/usr/local/lib/python3.6/dist-packages/kubernetes/client/api_client.py", line 67, in __init__
        self.pool = ThreadPool()
      File "/usr/lib/python3.6/multiprocessing/pool.py", line 789, in __init__
        Pool.__init__(self, processes, initializer, initargs)
      File "/usr/lib/python3.6/multiprocessing/pool.py", line 174, in __init__
        self._repopulate_pool()
      File "/usr/lib/python3.6/multiprocessing/pool.py", line 239, in _repopulate_pool
        w.start()
      File "/usr/lib/python3.6/multiprocessing/dummy/__init__.py", line 48, in start
        threading.Thread.start(self)
      File "/usr/lib/python3.6/threading.py", line 846, in start
        _start_new_thread(self._bootstrap, ())
    RuntimeError: can't start new thread
```

Node cordoned, as it is suspected to be the culprit. Hub pod is deleted to be reassigned to a new node

### 18:30

to help recover, user pods older than one hour are deleted

### 18:37

nothing is responding to requests anymore, including prometheus, grafana, hub, binder. ingress controller pods are deleted to try to help. It helps!

Previously cordoned node is drained, as it is suspected of causing widespread outage.

### 18:40

Launch success rate is back to 100% after ~1hr of total downtime and ~4 hours of diminished capacity.

### 19:00

JupyterLab pods once again reach 300 user limit. Things seem to behave as intended at this point.

### 19:33

The repo quota is bumped to 303 in order to see if we can handle deployments under heavy load.

### 19:35

Notice that the launch rate now begins falling strongly

### 19:40

Note that logs show many `Failed to create temporary user for` errors

### 19:42

Note that `binder-` logs also show `Error creating user jupyterlab-jupyterlab-demo-7qptz8ws: HTTP 599: Connection timed out`
Also note that Grafana launch percentile plot has stopped reporting

### 19:45

Delete the Binder pod: `kubectl delete pod --namespace=prod binder-66fcc59fb9-58btx`

### 19:52

Note that Grafana launch percentile plot is back, launch success rate is back up. `binder-` pod is stable.

### 2X:XX (not sure exact time)

Same `connection timed out` errors popping up as before - launch
success rate is down to zero again.

### 21:57

Realization that the `hub-` pod is being overwhelmed by HTTP
requests due to the high traffic, and is locking up. This is causing the behavior.

### 22:12

All pods are deleted

### 22:30

Pods launching again, we are keeping an eye on the `hub-` pod CPU usage, which was _really_ high during the spikes in traffic (~125%).

Doing this with `kubectl --namespace=prod exec -it hub-989cc9bd-5qdcb /bin/bash` and then running `top`

### 22:43

CPU usage on the hub seems to be stabilized.

### 22:44

Another realization: if user pods were deleted while they were
still running their session, then HTTP requests would be sent to
"default", which was the `hub`. This was overwhelming the hub
even more. We should make "default" go to a 404 page rather than
hub. [Response codes for the hub](https://grafana.mybinder.org/render/dashboard-solo/db/main-dashboard?refresh=30s&orgId=1&from=1519107353593&to=1519193753593&panelId=4&width=1000&height=500&tz=UTC%2B01%3A00), note the switch from mostly 2xx to 3xx.

### 22:52 (maybe earlier?)

We have the idea to delete the routing table for the `hub-` pod so that it reduces the HTTP requests. This is done with the following commands.

* First, enter the `hub-` pod and start a python session with:
  
  `kubectl --namespace=prod exec -it hub-989cc9bd-5qdcb /bin/bash`
  
  then
  
  `python`

* delete default HTTP route:
   
  `requests.delete('http://proxy-api:8001/api/routes//', headers={'Authorization': 'token ' + os.environ['CONFIGPROXY_AUTH_TOKEN']})`

* add route for /hub/api:

  `requests.post('http://proxy-api:8001/api/routes//hub/api', headers={'Authorization': 'token ' + os.environ['CONFIGPROXY_AUTH_TOKEN']}, json={'hub': True, 'target': 'http://10.15.251.161:8081', 'jupyterhub': True, 'last_activity': '2018-02-20T21:18:29.579Z'})`

We decide to *not* experiment on live users right now. 
Everything has been stable once the 100-users-per-repo
throttling had been re-established..

## Feb 21, 13:00

A more permanent fix for the proxy routes is applied to redirect all requests for stopped pods back to the Binder landing page ([PR #441](https://github.com/jupyterhub/mybinder.org-deploy/pull/441)) by adding a route on `/user/` in the configurable-http-proxy (CHP) routing table that is handled by an nginx instance redirecting all requests to the main deployment URL.

### 15:15

`/user/` route is updated to serve 404 on most URLs instead of redirecting to BinderHub, to avoid shifting request load to BinderHub.

### 16:20

many pods are failing to stop, causing an increase in failures. cordon nodes `-qz3m` and `-vvsm` as likely culprits due to lots of error logs attributed to these instances in VM logs.

note: need to find a better way to identify bad nodes

## Feb 22, 07:13

It is discovered that the hub's high CPU usage is due to a known bug in KubeSpawner with the Kubernetes Python client version 4.0 that was [fixed](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/pull/462) in the jupyterhub helm chart v0.6. With kubernetes-client 4.0 Each Spawner allocates four idle threads via a ThreadPool. After some time, the total thread count gets high enough (~7000) that CPU usage get very high, even when the threads are idle.

### 07:18

The jupyterhub chart version used by binderhub [is updated to v0.6](https://github.com/jupyterhub/binderhub/pull/463).
Once deployed, CPU usage of the Hub returns close to zero.
This high CPU usage in the Hub due to a flood of threads created by kubernetes-client is believed to be the root cause of most of our issues during this incident.

## Conclusions

The ultimate cause of this incident was a bug in a specific version JupyterHub+KubeSpawner+kubernetes-client that causes unreasonably high load for a moderate load. This bug had been fixed weeks ago in the jupyterhub chart, and was present. BinderHub was using a development version of the jupyterhub chart *prior* to the latest stable release.

1. deploying a capacity increase during heavy load may not be a recipe for success, but this is inconclusive.
1. handling of slow shutdown needs work in jupyterhub
1. there is a bug in jupyterhub causing it to attempt to delete routes from the proxy that are not there. The resulting 404 is already fixed in jupyterhub, but the bug causing the incorrect *attempt* is still undiagnosed.
1. grafana is regularly being restarted, which causes the page to be down. Since deployments now notify grafana of a deploy, this can prevent deploy success. It is a harmless failure in this case because if the grafana annotation fails, no deploy stages are attempted, so a Travis retry is quite safe.
1. culler has an issue where it exits if its request fails with 400
1. culler shouldn't be making requests that fail with 400

1. Deploying a change to `prod` under heavy load causes instability, in this case manifesting in
   new users not being created.
1. Unclear if this instability was fixed by deleting `binder-`, or if this was just waiting for a
   change to propagate.
   
1. JupyterHub was basically getting swamped because it was handling more HTTP requests by an order of magnitude or more. This was because of a few factors:
    1. The aforementioned big bump in usage
    2. The "default" route points to the hub, so when a user's pod would get delete and they'd continue doing stuff, all resulting requests went to the hub.
    3. We don't have a mechanism for throttling requests on the hub
    4. We only have a single hub that's handling all HTTP requests
    5. There were cascading effects going on where errors would generate more HTTP requests that would worsen the problem.
1. some issues may have been attributable to unhealthy nodes, but diagnosing unhealthy nodes is difficult.


## Action Items

### JupyterHub

- Release JupyterHub 0.9 (or backport for 0.8.2), which has some known fixes for some of these bugs (https://github.com/jupyterhub/jupyterhub/issues/1676)
- Improve handling of spawners that are slow to stop https://github.com/jupyterhub/jupyterhub/issues/1677
- Investigating allowing deletion of users whose servers are slow to stop or fail to stop altogether https://github.com/jupyterhub/jupyterhub/issues/1677
- implement API-only mode for use cases like Binder (https://github.com/jupyterhub/jupyterhub/issues/1675)


### Zero-to-JupyterHub

cull_idle_servers:

- identify reason why 400 responses cause script to exit (https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/522)
- avoid 400 responses by waiting for servers to stop before deleting users (https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/522)

### BinderHub

- ensure pycurl is used, which is known to perform better with large numbers of requests than tornado's default SimpleAsyncHTTPClient (https://github.com/jupyterhub/binderhub/pull/460)
- Investigate timeout issue, which may be due to lack of pycurl, too many concurrent requests, or purely the overloaded Hub (https://github.com/jupyterhub/binderhub/issues/464)
- separate rejection code/metadata for launch failures due to repo limit vs. "regular" launch failures. Note: on investigation, we already do this so launch failures should *not* include rejected launches.
- Figure out if there's a way to reduce the number of HTTP requests that are going to the JupyterHub (this became a problem w/ high load) (https://github.com/jupyterhub/binderhub/pull/461)
- Make it possible for Binder to launch multiple JupyterHubs and direct users through those hubs in a round-robin fashion (https://github.com/jupyterhub/binderhub/issues/465)

### Deployment

- Avoid sending requests for stopped pods to the Hub (which may overwhelm it if there's high load) (https://github.com/jupyterhub/mybinder.org-deploy/pull/444)
- Document ways to suspect and identify unhealthy nodes. At least some of the issues had to do with nodes that had become unhealthy, but diagnosing this was difficult. (https://github.com/jupyterhub/mybinder.org-deploy/issues/468)
- Come up with group guidelines for deploying changes under heavy loads. (https://github.com/jupyterhub/mybinder.org-deploy/issues/466)
- Investigate what are "expected" downtimes for a change to repo user limits, or other changes more broadly (https://github.com/jupyterhub/mybinder.org-deploy/issues/466)
- Find a way to limit HTTP requests to the JupyterHub in cases
  of high load.
- "we should also monitor and alert on jupyterhub process > 70% CPU" (monitoring done [in grafana](https://grafana.mybinder.org/dashboard/db/components-resource-metrics))
- Move Grafana and other support services to an external cluster, so they are not affected by load in the main cluster. Our tools for debugging should not be affected by the bugs we are trying to debug (https://github.com/jupyterhub/mybinder.org-deploy/issues/438)
- Document clear processes for requesting limit raises and how they should be granted https://github.com/jupyterhub/mybinder.org-deploy/issues/438
- Fix cadvisor + prometheus setup so we properly get CPU / Memory statistics from cadvisor https://github.com/jupyterhub/mybinder.org-deploy/pull/449
- Make all infrastructure pods be in the `Guaranteed` QoS so they do not get restarted when resources get scarce
