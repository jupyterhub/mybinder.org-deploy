# 2020-07-09, Simultaneous launches (aka, SciPy gives Binder a lot of hugs at the same time)

## Summary

Several SciPy 2020 tutorials are using Binder as a part of their demonstrations. They've
requested quota increases before-hand, which we have granted. However, when two
tutorials both launched at the same time with >100 users each, Binder temporarily lost
service. This disruption self-healed once a new node was up, so major technical
improvements aren't needed. Though we may consider process/documentation improvements to
help avoid this in the future.

## Timeline

All times in UC/Pacific

[link to grafana during incident window](https://grafana.mybinder.org/d/3SpLQinmk/1-overview?orgId=1&from=1594299600000&to=1594305000000&var-cluster=default)

### 07:30am - First report

[We hear reports](https://gitter.im/jupyterhub/mybinder.org-deploy?at=5f072954a61b8675119e65dd)
that the xarray tutorial noted some broken and/or slow launches on Binder.

### 07:35 - Note pending pods

[We note there are many pending pods](https://gitter.im/jupyterhub/mybinder.org-deploy?at=5f072ac186ccb45b599592c9) during that time. We also noted that
the xarray Binder had undergone many builds before the tutorial, which may have
contributed to the time it took to pull Docker images on the nodes.

We also noted that the placeholder pods and active pods seemed to do
[some weird stuff](https://grafana.mybinder.org/d/nDQPwi7mk/node-activity?orgId=1&from=1594300376037&to=1594305103856&fullscreen&panelId=43):

![](https://i.imgur.com/0bTTTRd.png)

Same chart with annotations for scale-up events:

![](https://i.imgur.com/lGUajxp.png)

> Min notes that: this is placeholder pods doing exactly what they are supposed to
> (ref: [placeholder writeup](https://discourse.jupyter.org/t/planning-placeholders-with-jupyterhub-helm-chart-0-8-tested-on-mybinder-org/213)):
> 1. pending placeholders is what causes node scale-up before 'real' users need the new node
> 2. as the new node is ready to accept pods, placeholders start there and go back to running
> 3. if 100% of placeholders are pending for a period of time waiting for the new node
>    (as they are here), this indicates *user* pods are also waiting for the new node,
>    which is what placeholder pods are meant to reduce. We should expect a rise in
>    launch time when this happens. This indicates we do not have enough placeholder
>    pods.

### 07:35 - Node limit increased

We noted that we'd reached our node limit on GKE and
[increased it](https://gitter.im/jupyterhub/mybinder.org-deploy?at=5f072b0a8342f46274047e5b).

### 07:42 - Launches are back to normal

We noted that [launches returned to normal](https://gitter.im/jupyterhub/mybinder.org-deploy?at=5f072ce0c7d15f7d0f801ab0).

## Lessons learnt

### What went well

1. We quickly heard about the problem and responded
2. The deployment was relatively self-healing here (with one exception that we may
   have hit a node limit on GKE)

### What went wrong

1. A steeper than usual spike in traffic meant our placeholder pods didn't allocate new
   nodes early enough to be ready when users needed them, resulting in queuing of
   launches.
2. A very high spike in number of builds (~30) may have contributed to an unusual
   allocation of resources (maybe?)
3. As a result of the high load and new nodes spinning up, launches began to timeout
4. GKE prod reached its upper node limit in capacity, requiring a manual increase in
   node capacity. During this time, many pods were pending, waiting for a slot.
5. According to our metrics, launch success rate never dropped below 100%, but users
   experienced failures. This is perhaps because our timeout is 10 minutes (long!) and a
   first-try failure at 10 minutes followed by a success 5 minutes later is likely experienced as a failure by the user. The
   launch success rate chart shows 100% success rate *after retry* but high retry rate,
   indicating timeouts due to load:

   ![launch success rate chart](https://i.imgur.com/UiAgdwA.png)

6. Users reported experiencing connection errors, but these are not reflected in our
   metrics as failures


## Action items

### Process improvements

1. Something about how to notice whether we're hitting GKE node limits? *We
   can add a threshold to certain Grafana charts, indicating the current limit. Not sure
   how to keep it up-to-date.*
2. Consider dedicated nodes or cluster for large events we know are going to use Binder a lot
   (e.g. `scipy.mybinder.org`). [see issue here](https://github.com/jupyterhub/mybinder.org-deploy/issues/1526)
3. Include a "tips and recommendations" step to the official "quota increase" issues.
   Maybe a short list of 5 items that instructors should consider (like "don't make lots
   of changes just before the event") and we get them to verbally say "yes" to before
   they are approved. [issue here](https://github.com/jupyterhub/mybinder.org-deploy/issues/1525)

### Documentation improvements

1. Something about recommending to others not to make lots of builds of the repo just
   before an event (or to separate out content/env repos)
2. Something about spreading out Binder clicks for events so they don't all happen at once?

Add these to the documentation and then add a link to these docs to the github quota increase
issue.

### Code and Configuration changes

1. increase the number of placeholder pods on GKE while we expect larger than usual
   spikes from SciPy tutorials:
   [PR](https://github.com/jupyterhub/mybinder.org-deploy/pull/1492).
2. decrease launch timeout to 5 minutes. 10 minutes to launch is probably too long to
   start retrying. This chart (lots of lines!) shows brief periods of 'retried'
   launches, almost all of which are at 10 minutes, indicating that timeout is the
   majority cause:

   ![launch-time-chart](https://i.imgur.com/dO1FIfw.png)

   If we limit to only the 99th percential of successful launches, we see that launches *almost never* take longer than 5 minutes and then succeed:

   ![](https://i.imgur.com/rYh0Whv.png)
   
   If we decrease the launch timeout to 5 minutes, this will likely increase our failure rate, *according to metrics*, but should clear out the queue of what are likely already failed launches *according to users*. The result should be a better experience. [issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/1528).

3. We should investigate resource allocations to builds, and possible limit concurrent
   builds per repo to a very small number (killing old builds is probably a better user
   experience than blocking new ones), as the failure corresponds to a spike in builds
   but *not* a spike in launches. [issue for information gathering here](https://github.com/jupyterhub/mybinder.org-deploy/issues/1529).
4. Add a launches-requested metric that is recorded immediately upon request, because
   our current launch metrics are only recorded when the launch either succeeds or
   fails, resulting in an inaccurately smooth and delayed metrics report. For example:
   120 requests in 1 second that complete one at a time over a minute will look like a
   smooth 2 requests/second in the current metrics.
5. Implement a quota on prod so that pending pods beyond capacity fail informatively,
   rather than queuing, continuing to add to the load?
