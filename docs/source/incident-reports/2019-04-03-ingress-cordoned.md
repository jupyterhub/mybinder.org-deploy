# 2019-04-03, 30min outage during node pool upgrade

## Summary

During a Kubernetes version upgrade all nodes running our ingress-controller
pods were cordoned. This went unnoticed and caused 40min of total outage.

## Timeline

All times in GMT+2

### 2019-04-03 12:50

Start of incident. The final two nodes in the old user node pool are cordoned.

### 13:28

Investigation starts after a user reported that mybinder.org was down.

### 13:29

The ingress controller pods were deleted and rescheduled on uncordoned
nodes. Service resumes. Incident ends.

## Lessons learnt

### What went well

List of things that went well. For example,

1. service was quickly restored once outage was reported

### What went wrong

Things that could have gone better. Ideally these should result in concrete
action items that have GitHub issues created for them and linked to under
Action items.

1. Outage went unnoticed for 40minutes

### Where we got lucky

These are good things that happened to us but not because we had planned for them.
For example,

1. A user reported the outage on gitter and someone was around to see it and
   react to it

## Action items

These are only sample subheadings. Every action item should have a GitHub issue
(even a small skeleton of one) attached to it, so these do not get forgotten.

### Technical improvements

1. Update SRE guide to include guidance for moving ingress controller pods
2. Setup our ingress deployment to be robust against nodes being cordoned
