
# 2018-01-17, Emergency Aardvark bump


## Summary

In the midst of a general Travis period of instability, we were slow to
realize that Ubuntu had pulled several of its packages for "Zesty" from the
repository we were using in the base image for repo2docker. This meant that
most Binders would fail to build because those packages were no longer available.
We had to [perform an emergency bump](https://github.com/jupyterhub/repo2docker/pull/197)
to the latest version of Ubuntu (artful).
In the future we should keep bumping when ubuntu makes a new release *until*
it makes a new LTS release, then we should pin repo2docker at that.

## Timeline

All times in PST

### 2018-01-15
General Travis failures happening due to Travis downtime (not related to
Binder deployment)

### 2018-01-16

JupyterHub travis failures
(https://github.com/jupyterhub/repo2docker/pull/197#issuecomment-358515334),
was dismissed as holdover from Travis failing on the 15th (since it was reported
as 'no route to host' rather than 404).

### 2018-01-17 17:14pm
* Other travis failures (berkeley's), points to issue being real
* Realization this will cause repo2docker + mybinder to fail

### 2018-01-17 17:30pm
Binder build logs showed lots of "IGN" errors, due to trying to pull from
zesty repositories. Then would fail.

**Problem**: Ubuntu removed repository packages for zesty, since it was not
a long-term release. The base Binder image was using zesty, so it would look
for packages that weren't there anymore.

### 18:57
Bump to artful, merged + deployed. Checked mybinder.org and problem was resolved.


### 19:00
Tweet + Email listserv announcing bump to Artful.


## Action items

### Process

* Note that Ubuntu non-LTS is on a ~9 month cycle, not the 1 year cycle we assumed.
  Keep bumping Ubuntu versions until we hit LTS, then stop [Issue](https://github.com/jupyterhub/repo2docker/issues/198)
* Subscribe to the ubuntu-announce mailing list [Issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/296)

### repo2docker
* Separate python version from distro version [Issue](https://github.com/jupyterhub/repo2docker/issues/185)
* Allow users to pin distros (with an apt.yaml) [PR](https://github.com/jupyterhub/repo2docker/pull/148)

### Misc
* Keep our own apt mirror [Issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/295)

### mybinder.org-deploy
* Continuous tests should be run against binder, to tell us when things fail [Issue](https://github.com/jupyterhub/mybinder.org-deploy/issues/19)
