# 2018-07-30 JupyterLab builds saturate BinderHub CPU

## Summary

Binder wasn't properly building pods and launches weren't working. It was
decided that:

1. The `jupyterlab-demo` repo updated itself, triggering a build
1. The update to `jupyterlab-demo` installed a newer version of JupyterLab
1. `repo2docker` needed a loooong time installing this (perhaps because of webpack size issues)
1. Since the repository gets a lot of traffic, each request to launch while
   the build is still happening eats up CPU in the Binder pod
1. The Binder pod was thus getting saturated and behaving strangely, causing
   the outage
1. Banning the `jupyterlab-demo` repository resolved the CPU saturation issue.

## Timeline

All times in PST (UTC-7)

### 2018-07-30 ca. 11:20

[Gitter Link](https://gitter.im/jupyterhub/binder?at=5b5f56df12f1be7137683cbc)

We notice that launches are not happening as expected. Cluster utilization is very low,
suggesting that pods aren't being created.

### 11:22

- Notice an SSL protocol error:

  ```
  tornado.curl_httpclient.CurlError: HTTP 599: Unknown SSL protocol error in connection to gcr.io:443
  ```

- Binder pod is deleted and launches return to normal.

### 12:19

- Launches aren't working again, taking a very long time to start up
- Deleted binder and hub pods
- This resolved the issue a second time.

This is the utilization behavior seen:

![](https://files.gitter.im/jupyterhub/binder/3cSB/thumb/image.png)

### 13:29

Behavior is once again going wrong. Launches taking forever to load. We note
a lot of networky-looking problems in the logs.

### 13:41

Deleted several evicted pods. Pods are often evicted because of low resources
available and `kubelet` evicts in order to free up resources for more important
services.

### 14:01

Confirm that networking seems to be find between production pods.

[Gitter link](https://gitter.im/jupyterhub/binder?at=5b5f7caecb4d5b036ca97bd9)

### 14:16

Note that the CPU utilization of the BinderHub pod is at 100%. If we restart
Binder pod, the new one gradually increases CPU utilization until it hits
100%, then problems begin.

This explains the short-term fixes of deleting the `binder` pod from before.

### 14:45

We realize that the `jupyterlab-demo` repository has been updated and has
a lot of traffic. This seems to be causing strange behavior because it is
still building.

[Gitter link](https://gitter.im/jupyterhub/binder?at=5b5f86b33e264c713850cb5c)

### 15:11

`jupyterlab-demo` repository is banned, and behavior subsequently returns to
normal.

Post-mortem suggests this is the problem:

1. The `jupyterlab-demo` repo updated itself, triggering a build
1. The update to `jupyterlab-demo` installed a newer version of JupyterLab
1. `repo2docker` needed a loooong time installing this (perhaps because of webpack size issues)
1. Since the repository gets a lot of traffic, each request to launch while
   the build is still happening eats up CPU in the Binder pod
1. The Binder pod was thus getting saturated and behaving strangely, causing
   the outage
1. Banning the `jupyterlab-demo` repository resolved the CPU saturation issue.

## Lessons learned

### What went well

- the binder team did a great job of distributed debugging and got this fixed
  relatively quickly once the error was spotted!

### What went wrong

- It took a while before we realized launch behavior was going wonky. We really
  could use a notifier for the team :-/

## Action items

These are only sample subheadings. Every action item should have a GitHub issue
(even a small skeleton of one) attached to it, so these do not get forgotten.

### Process improvements

1. set up notifications of downtime ([issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/611))

### Technical improvements

1. Find a way to gracefully handle repositories that take a long time to build (https://github.com/jupyterhub/binderhub/issues/624)
1. Find a way to avoid overloading the Binder CPU when a repository is building
   and also getting a lot of traffic at the same time. (https://github.com/jupyterhub/binderhub/issues/624)
