# Some useful Grafana plots

Below are some links to various plots from grafana, an explanation of what they show and why they are useful to check.

> Many of the plots on grafana have a drop-down menu called "cluster" with three options referring to the different clusters mybinder.org operates on:
>
> - "prometheus" refers to the GKE cluster (US)
> - "OVH prometheus" refers to the OVH cluster (EU)
> - "default" is the sum across the clusters

- [Launch/Build Success Rate](https://grafana.mybinder.org/d/3SpLQinmk/1-overview?refresh=1m&orgId=1&var-cluster=default&panelId=16&fullscreen) - This chart is the main indicator that mybinder.org is healthy. If there is a problem, a dropping success rate indicates that it's impacting users. The caveat is that it's an indicator of _current_ status: if builds or launches are failing due to timeouts that it can take a long time to show up as the failure is only reported once it's completed failing. Including retries, this can take several minutes. The [Launch Success Rate](https://grafana.mybinder.org/d/fZWsQmnmz/pod-activity?refresh=1m&panelId=9&fullscreen&orgId=1&var-cluster=prometheus) graph shows similar statistics but also includes the number of launch attempts. This can tell us if no-one tried to launch a repo, or if a lot of people tried but failed. Ocassionally, large spikes in launch attempts happen which can be interesting to investigate.

- [Number of Pods per Node](https://grafana.mybinder.org/d/nDQPwi7mk/node-activity?orgId=1&var-cluster=prometheus&panelId=26&fullscreen&refresh=1m) - This graph shows which nodes are serving the mybinder.org users. This can indicate when auto-scaling may need a helping hand, for example, if one node has had a low load for a long time, it may need to be manually cordoned and drained because a pod is stuck on it.

- [Number of User Pods over time](https://grafana.mybinder.org/d/fZWsQmnmz/pod-activity?refresh=1m&panelId=3&fullscreen&orgId=1&var-cluster=default) - This graph shows how many user pods have been running on mybinder.org. If this seems to be larger than usual, it could be indicative of something interesting, such as posting a blog post or a link on HackerNews that generates a lot of traffic.

- [Popular repositories](https://grafana.mybinder.org/d/fZWsQmnmz/pod-activity?refresh=1m&panelId=1&fullscreen&orgId=1&var-cluster=prometheus) - This graph shows the most popular repos by number of launches in the last hour and, for example, we can see classes that use mybinder.org.
