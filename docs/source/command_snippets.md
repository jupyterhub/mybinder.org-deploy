# Command snippets used during operations

This is a collection of frequently and infrequently used command-line snippets
that are useful for operating and investigating what is happening on the
cluster. Think of it as a mybinder.org specific extension of the [kubernetes
cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/).

## The mybinder-tools Python repository

Note that there is a helper package for working with Kubernetes in Python,
you can find it in the [mybinder-tools repo](https://github.com/jupyterhub/mybinder-tools).

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

* `hub-` XXX
* `binder-` XXX
* `proxy-` XXX
* `proxy-patches-` XXX
* `redirector-` XXX
* `jupyter-` - Deleting a user pod will shut down their session. The user will
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

If necessary, you can then scale the cluster back down.


## Networking

### Manually confirm network between pods is working

To confirm that binderhub can talk to jupyterhub, to the internet in general, or
you want to confirm for yourself that there is no connectivity problem between
pods follow this recipe.

1. connect to the pod you want to use as "source", for example the jupyterhub
pod: `kubectl --namespace=prod exec -it hub-989cc9bd-bbkbk /bin/bash`
1. start `python3`, `import requests`
1. use `requests.get(host)` to check connectivity. Some interesting hostnames
to try talking to are:
    * http://binder/, the binderhub service
    * http://hub:8081/hub/api, the jupyterhub API
    * http://proxy-public/hub/api, the CHP route that redirects you to the
      jupyterhub API (content of the response should be equal)
    * http://google.com/, the internet
    * the CHP API needs a token so run: `headers={'Authorization': 'token ' + os.environ['CONFIGPROXY_AUTH_TOKEN']}`
      and then`requests.get('http://proxy-api:8001/api/routes', headers=headers)`

To find out hostnames to try look at the `metadata.name` field of a kubernetes
service in the helm chart. You should be able to connect to each of them using
the name as the hostname. Take care to use the right port, not all of them are
listening on 80.

## Acronyms that Chris likes to use in Gitter

It has been pointed out that Chris often employs the use of unusually
long acronyms. This is a short list of translations so that the world can
understand his unique and special mind.

* TYVM: Thank You Very Much
* SGTM: Sounds Good To Me
* LMKWYT: Let Me Know What You Think
* WDYT: What Do You Think
