# Deployment policy for mybinder.org

Deployments to mybinder.org should be:

1. **Safe**. We will have good, user friendly tooling + lots of safeguards, so people can deploy without fear of accidentally breaking the site.
2. **Easy**. We want a lot of people to be involved in maintaining mybinder.org, so we must make sure deployments are also easy to do. Most deployments should not require specific sysadmin knowledge.

These two should be our guiding principles.

## Kinds of deployments

There are primarily two kinds of deployments, and they should have different policies.

### Deploying code

When a change is merged into the binderhub or repo2docker repos, this new code needs to be deployed.


#### Proposal for how these are deployed

1. When a PR is merged in the repo2docker or binderhub repos, a PR is made automatically against the mybinder.org-deploy repo
2. No separate approvals are needed for these automatic PRs to mybinder.org-deploy- approval + merging of the PR in the repo2docker or binderhub repo is good enough.
3. The person doing the merging in the repo2docker or binderhub repo is also responsible for merging the PR to mybinder.org-deploy & making sure the deployment succeeds. This requires that they make sure they have the time to go through with the merge + deploy in mybinder.org-deploy before doing the merge in the repo2docker / binderhub repository. This is to prevent undeployed changes from piling up, and possibly blocking other people from deploying.
4. If a deployment fails and needs to be rolled back, it should either be also immediately fixed in the binderhub / repo2docker repos, or should be rolled back there too. The general principle is that we should be as close as possible to having master of those two repos deployed at all times.

This all needs a healthy dose of automation to make happen.

### Making infrastructure changes

These are changes to the infrastructure that don't directly touch binderhub or repo2docker. Examples for these include:

1. Upgrading nginx Ingress controller
2. Re-configuring our prometheus servers
3. Upgrading to a new JupyterHub release
4. Re-configuring autoscaling for the cluster
5. Doing a kubernetes master upgrade.

These changes require a different kind of review than deploying code.


#### Proposed process

???
