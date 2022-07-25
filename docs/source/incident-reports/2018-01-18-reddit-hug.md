# 2018-01-18, reddit hugs mybinder

## Summary

A repo is posted to [reddit /r/python](https://www.reddit.com/r/Python/comments/7r6e6w/visualize_your_mostplayed_artists_tracks_and/), it starts getting popular. Traffic starts
building from around 6pm. Peaks at about 6am with 600 running pods.

## Timeline

All times in PST

### 2018-01-18 4:19

First noticed something was up after receiving an email about high level of users on Grafana from someone and a question on the Gitter channel.

### 4:27

Found the repository that was being [spawned](https://github.com/N2ITN/GoogleMusicFavs/), checked content (was this a bot/spam repo?). About 300 pods from this repo running (`kubectl get pods --namespace=prod | grep googlemusic | wc -l`)

### 4:33

Find out this repo is part of a r/python post. Decide this is a legit use of mybinder, things seem to be working. Keep monitoring, no action.

### 4:45

Notice we are using 12 of the maximum 15 nodes that the autoscaler is allowed to scale up to. Unclear what metric the autoscaler uses to decide to scale up. Decide to increase limit if we get close to 15.

### 5:59

Now at 14 nodes, decide to increase limit to 20 nodes via web interface. Noticed that grafana reports one less active node than cloud console. Grafana does not count cordoned nodes!

### 6:15

Note that number of running pods according to grafana has started to level off.

### 6:25

Decide there must be a problem as Google analytics traffic suggests people are still trying to start new binders. Arriving at about 10 users per 15minutes ("real time active users" on GA). This doesn't fit with level or falling number of running pods.

### 6:39

User reports unrelated repository does not launch ("waiting for server to launch") as well as start of build not working (can not resolve github.com). Both problems are confirmed.

### 6:52

After investigating and looking for broken/restarting pods, health of nodes that something weird is broken. Remember that last time things looked fine but things were broken we increased the number of ingress replicas. Decided to increase to ten from five. Notice that some replicas are in CrashLoopBackoff. Decide not to further investigate because increasing the number to seven replicas seems good enough. Also does not seem to mitigate the original build/launch problem.

### 7:23

Connect to node -2fhq with `gcloud compute --project "binder-prod" ssh --zone "us-central1-a" "gke-prod-a-ssd-pool-972e4826-2fhq"` to test network connectivity. Fetching `github.com` and `google.com` with `wget` works. Conclude that there is no network problem.

### 7:27

Noticed that deploying to production "failed". This seem to be flaky deploys as the cluster had been changed to have more ingress replicas. Travis log ends/hangs on "deleting outdated charts". Multiple restarts of build do not seem to fix the problem.

### 7:49

Decided to build a never before built repo with a unique name to make debugging easier. See that it gets built, pod is started but then exits 40s after startup because it is not contacted. JupyterHub pod log shows corresponding "pod never showed up" message. Unclear why there seems to be networking issues.

### 8:04

Tim signs off, Carol online.

### 8:20 - 8:24

Yuvi and Carol discuss situation. Suggest scrolling back through gitter history to catch up with state of play.

### 8:24

Using 14 nodes, conclude that "we are full". Check content of the deploys made during the last few hours.

### 8:29

By hand remove all pods spawned by jupyterhub that are 6-9hours old with `kubectl --namespace=prod get pod -l heritage=jupyterhub | grep -P '[6-9]h$' | awk '{ print $1; }' | xargs -L1 kubectl --namespace=prod delete pod`

### 8:33

Note that jupyterhub logs are full of errors. Reading logs leads to conclusion that user pods are being spawned but contacting them within the 30s timeout fails.

### 8:39

Checking network connectivity between jupyterhub pod and a random pod. "ssh" into the hub pod with `kubectl --namespace=prod exec -it hub-7649b9bf8-d769g /bin/bash` and attempt to access a random user pod found with `kubectl --namespace=prod get pod -o wide`. Test network connectivity with:

```python
>>> requests.get('http://10.12.6.136:8888/')
<Response [404]>
```

404 error means we managed to talk to the jupyter notebook server on that IP.

### 8:47

Decide to delete the jupyterhub pod: `kubectl --namespace=prod delete pod hub-7649b9bf8-d769g`
watching logs of new hub pod with `kubectl --namespace=prod logs hub-7649b9bf8-hkvnl -f`

### 8:53

Noted that restarting the hub also woke up the culling process. Culler springs to action cleaning out a lot of stale pods.

### 8:57

Some builds succeed and proceed to notebook interface. Others still get stuck with "waiting for server ...".

### 9:00

Tim back. Catching up some details on cluster size that got missed in the scrollback.

### 9:01

`gke-prod-a-ssd-pool-972e4826-2fhq` is identified as a node that has networking issues. The pod `fluentd-gcp-v2.0.9-68p79` is in `CrashLoopBackOff`. This pod is also on -2fhq. The pod was found by looking at all pods in all namespaces, not just the prod namespace.

### 9:05

Decide to cordon off node: `kubectl cordon gke-prod-a-ssd-pool-972e4826-2fhq`. Noted that the ingress pods that have been failing are also on this node.

### 9:14

After testing several repositories by hand and with `py.test tests/test_launch.py --hub-url=https://hub.mybinder.org --binder-url=https://mybinder.org` feeling is things are back to working order. Brief discussion if incident is over or not.

## Action items

### Process

- Gather commands used in incident response and add to SRE guide.
- Discuss how to know when to call an incident as resolved.

### Training

- Investigate k8 training
- Consider ways to have a system similar to staging (though not critical path) for training and experimentation

### Testing

- Consider creating a script or cheatsheet for running tests to launch binders
- Run the py.tests constantly and actively alert us when they fail (active monitoring)
