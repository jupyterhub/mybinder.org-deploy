
# 2018-01-04, Failed deploy to staging

## Summary

Merging a PR into BinderHub and deploying that change to `mybinder.org` staging in a second PR resulted in a Travis error. It also led to user uncertainty about the steps to resolve the error. User misunderstanding of the correct commit SHA to use for the binderhub helm-chart was one part of the problem. Flakiness of Travis deployment due to insufficient waiting for helm-chart deployments contributed to the problem. Though time consuming to determine the cause of the Travis error, there was no loss of production service due to current workflow and the staging-prod workflow served its main purpose well.

## Timeline

All times in PST

### 2018-01-04 07:33

Reviewed and merged BinderHub PR [#395](https://github.com/jupyterhub/binderhub/pull/395). Min's PR commit 441f5ea. Merge commit 4e3bafb.

### 08:03

PR [#254](https://github.com/jupyterhub/mybinder.org-deploy/pull/254) failed to deploy to staging.

[Travis CI](https://travis-ci.org/jupyterhub/mybinder.org-deploy/builds/325095814) errored and displayed that the deploy to staging failed.

PR #254 was generated using the first set of instructions in the `README`, [Deploying a Change](https://github.com/jupyterhub/mybinder.org-deploy#deploying-a-change). *Note: User error was made here by assuming the SHA used in the BinderHub helm-chart (binderhub-0.1.0-441f5ea) was the same as the PR in the BinderHub merge commit (4e3bafb). The assumption was that Travis would deploy the binderhub change to the helm-chart repo using the merge commit hash. The Documentation in the `README `'s [BinderHub](https://github.com/jupyterhub/mybinder.org-deploy#binderhub) section has this correct, but the user didn't think to scroll down as they had done the deployment process before but not on a regular basis.*

Investigation begins.

### 08:17 

Following the process in the `README`, I reverted the original PR since Travis showed an error. PR [#255](https://github.com/jupyterhub/mybinder.org-deploy/pull/255) reverted #254.

### 08:25

Message posted on Gitter to understand why Travis had errored since it seemed to be a very simple change bumping the BinderHub version.

### 08:27

Response posted on Gitter that Travis often fails to deploy. A restart of the Travis job usually resolves the error.

### 08:34

Message posted on Gitter to understand why the merge SHA (4e3bafb) was not found in a binderhub helm-chart.

From the Gitter response, user learned that there is a delay in the helm-chart showing up. User realizes that I also made an incorrect assumption about the hash to use in the PR for binderhub helm-chart. The correct SHA to use would be the last commit where the relevant files changed (441f5ea) which is not the same as the most recent commit (4e3bafb).


### 08:59

Submitted a new PR [#256](https://github.com/jupyterhub/mybinder.org-deploy/pull/256) to staging with the correct hash. Travis deploys successfully to staging. Visual review of `staging.mybinder.org` site looks fine.

### 11:31

Deployed to Prod with PR [#257](https://github.com/jupyterhub/mybinder.org-deploy/pull/257). Travis deploys successfully.

Tested repo, `willingc/ThinkDSP`, using the prod service to see if the notebook would launch. All seemed working on the sample notebook launch. Also checked Grafana dashboard to see if there was any disruption in activity.

Everything is fine and prod is working.


## Action items

### Process

- Minimize tribal knowledge in the deployment process (i.e. all may not know that restarting a failed Travis build may clear the error.).
- Simplify steps into a checklist especially ones that require human lookup of information or copy/paste.

### mybinder.org-deploy

- Minimize copy-paste errors by user
- Add a "deployment to staging" checklist and a "deployment to prod" checklist to the documentation (possibly as files distinct from the `README`.)
- Add a better way to self diagnose whether the Travis failure is legitimate or spurious.
- Look into generating a commit for bumping without human entry of data (review by a human is fine)

### helm-chart

- Document in the helm chart repo as well as mybinder.org-deploy that the deployment of the helm-chart may be delayed. Users should wait approximately 'x' minutes before opening a PR on staging.
