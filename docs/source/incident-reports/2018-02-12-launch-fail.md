# 2018-02-12, Hub Launch Fail

## Summary

Binder was successfully building user pods, but was then failing to direct
users to the built pods. It was fixed by deleting the `binder` and `hub` pods.

## Timeline

All times in PST

### 2018-02-12 14:03

We realized that there's a high usage on the mybinder deployment. Tried
building a repository and it would get to the "launching" step then never
proceed further. Eventually it'd return a "your image took too long to launch" error.

### 2018-02-12 14:06

From the [grafana board](https://grafana.mybinder.org), we realized that in the
"Launch Times Summary" plot we showed *all* pods as failing to launch.

### 14:08

We delete the `binder` and `hub` pods in the `prod` deployment.

### 14:09

Two people confirm that their pods now build and launch fine, Grafana also
shows successful "Launch Times Summary" data.

## Lessons learnt

### What went well

* Once we noted the problem, it was quickly resolved.

### What went wrong

* The outage was present for nearly an hour before we noticed it. This is partially
  because the site itself was returning no errors, only taking forever to launch.

### Where we got lucky

* The solution was just "delete `binder` and `hub`" and the problem resolved
  itself.

## Action items


### Process improvements

1. Improve the team operations around debugging the cluster more generally. We
   should make sure that on average there are N>1 people around with the skills
   and time to debug the deployment.

### Documentation improvements

1. Improve the language around site reliability expectations for mybinder.org,
   so that these kinds of outages don't feel like we're letting users down. ([link to issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/359))

### Technical improvements

1. We should set up some kind of monitoring for the mybinder.org deployment.
   We have plans to do this long-term ([link](https://github.com/jupyterhub/mybinder.org-deploy/issues/19)),
   but we should have something quick-and-dirty that gets us part of the way there
   quickly. ([link to issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/358))
