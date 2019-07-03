# Command snippets used during operations

This is a collection of frequently and infrequently used command-line snippets
that are useful for operating and investigating what is happening on the
cluster. Think of it as a mybinder.org specific extension of the [kubernetes
cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/).

## The mybinder-tools Python repository

Note that there is a helper package for working with Kubernetes in Python,
you can find it in the [mybinder-tools repo](https://github.com/jupyterhub/mybinder-tools).

## Cluster management

### Merging kubernetes credentials

Before completing any of the command snippets below, you need to merge the kubernetes credentials of the cluster you'd like to work with into your `~/.kube/config` file.
This is achieved by running:

```bash
gcloud container clusters get-credentials <CLUSTER-NAME> --zone=us-central1-a
```

### Upgrading kubernetes

Upgrading Kubernetes is done in two steps:

1. upgrade the kubernetes master version
2. upgrade the node version

First, we can upgrade the master version.
This is easiest via the Google Cloud Console which gives you a button to pick the latest version.
Upgrading master will result in some brief downtime of Binder during the upgrade.
It should take a couple of minutes.

To upgrade the master version with `gcloud`:

```bash
gcloud --project=binder-staging container clusters upgrade staging --master --zone=us-central1-a
gcloud --project=binder-prod container clusters upgrade prod-a --master --zone=us-central1-a
```

Now we can start the process of upgrading node versions, which takes more time.
Upgrading nodes really means replacing each node with a new one with the same name, using the new version.
If we use the above `container clusters upgrade` command to upgrade nodes,
it will take a very long time as Kubernetes drains nodes one by one to replace them.
To minimize downtime at the expense of some extra nodes for a while,
we create a whole new node pool with the new version and then cordon
and eventually delete the existing one.

**Note:** the process for changing node machine-type is the same
as the process for upgrading kubernetes node version,
since it is also creating a new node pool and draining and deleting the old one.

#### Upgrading staging

First, start the upgrade on staging by creating a new node pool.
Check the node type, number of nodes, and disk size.
The new pool should match the old one.

```bash
# old_pool is the name of the pool that we are replacing
old_pool=default-pool
# new_pool is the name our new pool will have. It must be different
new_pool=standard-4


gcloud --project=binder-staging container node-pools create $new_pool \
    --cluster=staging \
    --disk-size=500 \
    --machine-type=n1-standard-4 \
    --enable-autorepair \
    --num-nodes=2
    --zone=us-central1-a
```

> Note: To see a list of the node pools, run `gcloud container node-pools list --cluster staging --project=binder-staging`.

After the pool is created, cordon the previous nodes:

```bash
# for each node in the old pool:
kubectl cordon $node
```

> Note: You can run `kubectl get nodes -n <NAMESPACE>` to see a list of the current nodes.

Test that launches succeed on the new nodes by visiting
[https://staging.mybinder.org/v2/gh/binderhub-ci-repos/requirements/master](https://staging.mybinder.org/v2/gh/binderhub-ci-repos/requirements/master)

> Note: You might have to restart one of the ingress pods named `staging-nginx-ingress-controller-*` as they will both be on cordoned nodes and hence not receiving traffic. The symptom of this is that https://staging.mybinder.org does not load anymore.

Once this is verified to be successful, the old node pool can be drained:

```bash
kubectl drain --force --delete-local-data --ignore-daemonsets --grace-period=0 $node
```

and then the node pool deleted:

```bash
gcloud --project=binder-staging container node-pools delete $old_pool --cluster=staging --zone=us-central1-a
```

#### Upgrading prod

Upgrading production is mostly the same as upgrading staging.
It has a couple small differences in node configuration,
and we don't want to delete the old pool as soon as we have the new one
because there will be active users on it.

Production has two node pools:

1. a "core" pool, which runs the hub, binder, etc.
2. a "user" pool, where user pods run.

The process is mostly the same, but we do it in two steps (for two pools).

As with staging, first we create the new pool,
copying configuration from the old pool.
On production, we use `pd-ssd` disks, enable autoscaling,
and use the larger `n1-highmem-16` nodes for users.

The 'core' pool uses n1-highmem-4 nodes and has a smaller, 250GB SSD.

> Note: `gcloud beta` is currently required for the `--disk-type` argument.

First we'll create variables that point to our old and new node pools to make it clear when we're creating new things vs. deleting old things.

```bash
# old_pool is the name of the existing user pool, to be deleted
old_pool=user-1dot11dot7
# new_pool can be anything, as long as it isn't the same as old_pool
# something short but descriptive, e.g. hm16 for highmem-16 nodes
new_pool=hm16
```

> Note: You can see a list of the node pools by running:
```bash
gcloud container node-pools list --cluster prod-a --project=binder-prod --zone=us-central1-a
```
> To automatically assign the old pool name to a variable, run:
```bash
old_user_pool=$(gcloud container node-pools list --cluster prod-a --project=binder-prod --zone=us-central1-a --format json | jq -r '.[].name' | grep '^user')

old_core_pool=$(gcloud container node-pools list --cluster prod-a --project=binder-prod --zone=us-central1-a --format json | jq -r '.[].name' | grep '^core')
```

Then we can create the new user pool:

```bash
# create the new user pool
gcloud beta --project=binder-prod container node-pools create $new_pool \
    --cluster=prod-a \
    --zone=us-central1-a \
    --disk-type=pd-ssd \
    --disk-size=1000 \
    --machine-type=n1-highmem-8 \
    --num-nodes=2 \
    --local-ssd-count=1 \
    --enable-autoscaling \
    --enable-autorepair \
    --min-nodes=1 \
    --max-nodes=8 \
    --node-labels hub.jupyter.org/node-purpose=user,mybinder.org/pool-type=users
```

and/or create the new core pool:

```bash
# the name of the old 'core' pool
old_core_pool=core-pool
# the name of the new 'core' pool
new_core_pool=core-1-11

gcloud beta --project=binder-prod container node-pools create $new_core_pool \
    --cluster=prod-a \
    --zone=us-central1-a \
    --disk-type=pd-ssd \
    --disk-size=250 \
    --machine-type=n1-highmem-4 \
    --num-nodes=1 \
    --enable-autoscaling \
    --enable-autorepair \
    --min-nodes=1 \
    --max-nodes=4 \
    --node-labels hub.jupyter.org/node-purpose=core,mybinder.org/pool-type=core
```

Once the new pool is created, we can start cordoning the old pool.
To avoid new nodes being allocated in the old pool,
set the autoscaling upper limit to 1 on the old pool,
or disable autoscaling on the old pool.
This can only be done via the cloud console at this time.

<html>
<img src="images/node-pool-max-number.gif", alt="Set maximum number of nodes in a node pool" height="884" width="754">
</html>

Since prod has a lot of load which can overwhelm a new node,
we don't want to cordon the whole old pool immediately,
which would drive all of Binder's traffic to the new nodes.
Instead, we cordon the old nodes gradually, starting with ~half of the pool.
After the new nodes have had a chance to warm up
(check cluster utilization and user pods metrics in grafana, around 10 minutes should be fine),
we can cordon the rest of the old pool.

At each point, especially after the old pool is fully cordoned,
verify that launches work on the new nodes by visiting
[https://mybinder.org/v2/gh/binderhub-ci-repos/requirements/master](https://mybinder.org/v2/gh/binderhub-ci-repos/requirements/master)

```bash
# for each node in node pool
kubectl cordon $node
```

The `hub` pod will need to be manually migrated over to the new node pool.
This is achieved by deleting the pod and it should automatically restart on one of the new core nodes.

```bash
kubectl delete pod <HUB-POD-NAME> -n prod
```

> Note: You can find <HUB-POD-NAME> by running `kubectl get pods -n prod`.

Unlike staging, prod has active users, so we don't want to delete the cordoned node pool immediately.
Wait for user pods to drain from the old nodes (6 hours max), then drain them.
After draining the nodes, the old pool can be deleted.

```bash
kubectl drain --force --delete-local-data --ignore-daemonsets --grace-period=0 $node

gcloud --project=binder-prod container node-pools delete $old_pool --cluster=prod-a --zone=us-central1-a
```

## Pod management

### List all pods that match a given name or age

Sometimes you want to delete all the pods for a given repository. The easiest
way to do this is to name-match the part of the pod name that corresponds to
the repo (since there will be a bunch of random characters as well).

Here's a python script that will match pods with a given name or a given
age. You can use it with the following pattern:

```
python scripts/delete-pods.py --pod-name <your-query> --older-than <your-query>
```

* `--pod-name` is a string and will be matched to any pod that contains this string.
* `--older-than` is a float (in hours) and will match any pod that is older than this amount.

Note, they are both optional, but you need to supply *at least* one. Running
the above command by itself will list all pods that match the query.

### Delete all pods that match a given name or age

If you wish to **delete** the pods that match the query above, you supply the `--delete`
kwarg like so:

```
python scripts/delete-pods.py --pod-name <your-query> --older-than <your-query> --delete
```

### Forcibly delete a pod

Sometimes pods aren't easily deleted, e.g., if they are in a state `Unknown`
or `NodeLost` kubernetes may not be able to fluidly delete them. This is because
kubernetes waits for pods to gracefully delete, and if a pod cannot do this
(e.g., because it is totally unable to communicated with kubernetes), the
delete process won't happen. In this case, you can delete such pods with:

```
kubectl --namespace=prod delete pod <POD-NAME> --grace-period=0 --force
```

### Effects of deleting production pods

Below is a list of each production pod, and the expected outcome that comes with
deleting each one.

* `hub-` active user sessions will not be affected. New and pending launches will fail until the new Hub comes back.
* `binder-` the `mybinder.org` website will temporarily go down. Active user sessions will not be affected.
* `proxy-` all current users will lose connections (kernel connection lost) until the proxy returns and the Hub restores the routes. Server state is unaffected. Most browser sessions should recover by restoring connections. All pending launches will fail due to lost connections.
* `proxy-patches-` brief, minor degradation of error messages when browsers attempt to connect to a not-running server. This results in increased load on the Hub, handling requests from browsers whose idle servers have been culled.
* `redirector-` redirect sites (beta.mybinder.org) will 404 instead of sending to mybinder.org.
* `jupyter-` deleting a user pod will shut down their session. The user will
  encounter errors when they attempt to submit code to the kernel.

## Node management and information

### Manually increase cluster size

Sometimes we know ahead of time that mybinder.org will receive a lot of traffic.
As preparation we might choose to increase the size of the cluster before the
event.

To pre-emptively bump the cluster size beyond current occupancy, follow these steps:

* Increase autoscaler minimum size. (note this will lead to a brief period where
  the kubernetes API is not available.)
  * Go to http://console.cloud.google.com/
  * Click "Kubernetes engine" -> "edit" button
  * Under "Node Pools" find the "minimum size" field and update it.

* Use the `gcloud` command line tool to explicitly resize the cluster.
  * `gcloud container clusters resize prod-a --size <NEW-SIZE>`

Manually resizing a cluster with autoscaling on doesn't always work because the autoscaler
can automatically reduce the cluster size after asking for more nodes that
aren't needed. Increasing the minimum size works if you are resizing from
outside the autoscaler's bounds (e.g. 2) to the new minimum cluster size (3), so the
autoscaler doesn't have any idle nodes available for deletion. Similarly if
the new minimum is higher than the current size and there is no need to increase
the size of the cluster the autoscaler will not scale up the cluster even though
it is below the minimum size.

### Removing a node from the cluster

To remove a node from the cluster, we follow a two-step process. We first
**cordon** the node, which prevents new pods from being scheduled on it. We then
**drain** the node, which removes all remaining pods from the node.

* Step 1. Cordon the node

  ```bash
  kubectl cordon <NODE-NAME>
  ```

  "cordoning" explicitly tells kubernetes **not** to start new pods on this node.
  For more information on cordoning, see :ref:`term-cordoning`.
* Step 2. Wait a few hours for pods to naturally get deleted from the node.
  We'd rather not forcibly delete pods if possible. However if you *need* to
  delete all the pods on the node, you can skip to step 3.
* Step 3. Remove all pods from the node

  ```bash
  kubectl drain --force --delete-local-data --ignore-daemonsets --grace-period=0  <NODE-NAME>
  ```

  After running this, the node should now (forcibly) have 0 pods running on it.
* Step 4. Confirm the node has no pods on it after a few minutes. You can do this
  with:

  ```bash
  `kubectl get pods --namespace=prod -o wide | grep "<NODE-NAME>$" | grep "^jupyter-"`
  ```

  If there are any pods remaining, manually delete them with `kubectl delete pod`.

Once the node has no pods on it, the autoscaler will automatically remove it.

**A note on the need for scaling down with the autoscaler**.
The autoscaler has issues scaling nodes *down*, so scaling down needs to be
manually done. The problems are caused by:

1. The cluster autoscaler will never remove nodes that have user pods running.
2. We can not tell the Kubernetes Scheduler to 'pack' user pods efficiently -
   if there are two nodes, one with 60 user pods and another with 2, a new user
   pod can end up in either of those. Since all user pods need to be gone from
   a node before it can be scaled down, this leads to inefficient
   load distribution.

Because the autoscaler will only remove a node when it has no pods, this means
it is unlikely that nodes will be properly removed. Thus the necessity for
manually scaling down now and then.

### List how many user pods are running on all nodes

You can find the number of user pods on various nodes with the following command:

```bash
kubectl --namespace=prod get pod --no-headers -o wide -l component=singleuser-server | awk '{ print $7; }' | sort | uniq -c | sort -n
```

The `-o wide` lists extra information per pod, including the name of the node it is
running on. The `-l component=singleuser-server` makes it only show you user server
pods. The `--no-headers` asks kubectl to not print column titles as a header.
The `awk` command selects the 7th column in the output (which is the node name).
The sort / uniq / sort combination helps print the number of pods per each node in
sorted order.

### Recycling nodes

We have found that nodes older than > 4 days often begin to have problems.
The nature of these problems is often hard to debug, but they tend to be
fixed by "recycling" the nodes (AKA, creating a new node to take the place
of the older node). Here's the process for recycling nodes.

* **List the node ages.** The following command will list the current nodes
  and their ages.

  `kubectl get node`

* **Check if any nodes are > 4 days old.** These are the nodes that we can
  recycle.
* **Cordon the node you'd like to recycle.**

  `kubectl cordon <NODE-NAME>`

* **If you need a new node immediately.** E.g., if we think a currently-used
  node is causing problems and we need to move production pods to a new node.

  In this case, manually resize the cluster up so that a new node is added,
  then delete the relevant pods from the (cordoned) old node.

* **Wait a few hours.** This gives the pods time to naturally leave the node.
* **Drain the node.** Run the following command to remove all pods from the node.

  `kubectl drain --force --delete-local-data --ignore-daemonsets --grace-period=0  <NODE-NAME>`

* **If it isn't deleted after several hours, delete the node.** with

  `kubectl delete <NODE-NAME>`


## Networking

### Banning traffic

Sometimes there's bad traffic, either malicious or accidental,
and we want to block traffic, either incoming or outgoing,
between Binder and that source.

We can blacklist traffic in three ways:

1. ingress ip (bans requests to Binder coming from this ip or ip range)
2. egress ip (bans outgoing traffic *from* Binder to these ip addresses)
3. egress DNS (disables DNS resolution for specified domains)

All of these are *stored* in the `secrets/ban.py` file.
These are not upgraded

To update what should be banned, edit the `secrets/ban.py` file
and find the relevant list. If ip-based banning changed,
run the `scripts/firewall-rules` script to update the firewall:

```bash
./scripts/firewall-rules --project=binder-staging [gke_binder-staging_us-central1-a_staging]
./scripts/firewall-rules --project=binder-prod [gke_binder-prod_us-central1-a_prod-a]
```

If it is an update to the DNS block list, run the `secrets/ban.py` script:

```bash
./secrets/ban.py gke_binder-staging_us-central1-a_staging
./secrets/ban.py gke_binder-prod_us-central1-a_prod-a
```


## Acronyms that Chris likes to use in Gitter

It has been pointed out that Chris often employs the use of unusually
long acronyms. This is a short list of translations so that the world can
understand his unique and special mind.

* TYVM: Thank You Very Much
* SGTM: Sounds Good To Me
* LMKWYT: Let Me Know What You Think
* WDYT: What Do You Think
