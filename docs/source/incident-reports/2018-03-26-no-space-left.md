# 2018-03-26, "no space left on device"

## Summary

A node became unhealthy, correlated with a flood of "no space left on device"
messages in the logs. Kubernetes noticed the issue and appeared to recover itself in 20 minutes. Binder launches were failing during this time.

## Timeline

All times in CEST

### 2018-03-26 10:34

Launch success metric reaches 0%.

### 2018-03-26 10:55

Cluster self-heals and everything returns to normal, launch success back to 100%.

### 2018-03-26 15:00

Dip in log success metric noticed via grafana, investigation launched.
Found hundreds of "No space left on device" messages on node at the time of the event.

Cordoned node where the error occurred (gke-prod-a-ssd-pool-32-134a959a-wlmp),
despite the fact that it appears to have recovered.

Created log metric for "No space left on device" logs, exported to stackdriver.
Upon testing of stackdriver, observed that another node, gke-prod-a-ssd-pool-32-134a959a-ql6n,
has been reporting the same message hundreds of times.
Cordoned that node as well, for good measure.

Both of the cordoned nodes were aged 5-6 days and were the oldest nodes in the cluster.
I suspect that node age is related to this, and we will see it every week or so as something accumulates on the nodes.
The root cause is still unknown.


## Lessons learned

### What went well

- Cluster noticed the issue and self-healed. Recovery took ~20 minutes.
- Investigation was not under pressure as the cluster was in a functioning state at the time.
- Correlating VM logs in the google cloud console with grafana charts indicating an issue is
  very useful but somewhat difficult as there is a very large amount of information.

### What went wrong

- Binder was unavailable, but nobody was notified.
  Only proactive checking of Binder status on Grafana revealed the issue.


## Action items

- [x] Add log metric for "no space left on device" messages that seem correlated with problematic nodes
- [x] Add log metric for "Error creating user" message
- [x] Add metrics-based alert for "Error creating user" messages via stackdriver
- [ ] Enable SMTP for alerts from grafana metrics [GitHub Issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/365)
- [ ] Investigate root cause of "no space left on device" messages
- [ ] Systematically cordon and cull nodes older than 3-5 days?
