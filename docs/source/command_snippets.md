# Command snippets used during operations

This is a collection of frequently and infrequently used command-line snippets
that are useful for operating and investigating what is happening on the
cluster. Think of it as a mybinder.org specific extension of the [kubernetes
cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/).

## List all pods that match a given name or age

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

## Delete all pods that match a given name or age

If you wish to **delete** the pods that match the query above, you supply the `--delete`
kwarg like so:

```
python scripts/delete-pods.py --pod-name <your-query> --older-than <your-query> --delete
```

## Remove a node from the cluster

First cordon off the node with `kubectl cordon <nodename>`.
Wait for there to be no `jupyter-*` pods on the node. You can check this with
`kubectl get pods --namespace=prod -o wide | grep "<nodename>$" | grep "^jupyter-"`.
Then drain the node `kubectl drain <nodename>`. The kubectl drain command will
most likely give you an error about certain pods running on the node that
prevent it from draining the node. It is Ok (and expected) to use the suggested
flags to force the draining: `kubectl drain <nodename> --ignore-daemonsets --force --delete-local-data`. The autoscaler should now remove the  node for you.
This can take 10-15minutes.

## Find out how many user pods are running on various nodes

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

## Manually confirm network between pods is working

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

## Manually increase cluster size

Sometimes we know ahead of time that mybinder.org will receive a lot of traffic.
As preparation we might choose to increase the size of the cluster before the
event.

To pre-emptively bump the cluster size beyond current occupancy, it's two steps:

* increase autoscaler minimum size (http://console.cloud.google.com/), this
  will lead to a brief period where the kubernetes API is not available.
* resize cluster to new minimum size explicitly with `gcloud container clusters resize prod-a --size 3`
  replacing 3 with your target size.

Manually resizing a cluster with autoscaling on doesn't always work because the autoscaler
can automatically reduce the cluster size after asking for more nodes that
aren't needed. Increasing the minimum size works if you are resizing from
outside the autoscaler's bounds (e.g. 2) to the new minimum cluster size (3), so the
autoscaler doesn't have any idle nodes available for deletion. Similarly if
the new minimum is higher than the current size and there is no need to increase
the size of the cluster the autoscaler will not scale up the cluster even though
it is below the minimum size.

## Acronyms that Chris likes to use in Gitter

It has been pointed out that Chris often employs the use of unusually
long acronyms. This is a short list of translations so that the world can
understand his unique and special mind.

* TYVM: Thank You Very Much
* SGTM: Sounds Good To Me
* LMKWYT: Let Me Know What You Think
* WDYT: What Do You Think
