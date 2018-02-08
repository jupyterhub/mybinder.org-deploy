# Command snippets used during operations

This is a collection of frequently and infrequently used command-line snippets
that are useful for operating and investigating what is happening on the
cluster. Think of it as a mybinder.org specific extension of the [kubernetes
cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/).


## List all pods older than X

To get a list of all pods older than four hours:
```
kubectl get pod --namespace=prod | grep '^jupyter-' | grep '\(\([12][0-9]\|[4-9]\)h\|d\)$'
```

or all those that have existed for more than 24hours:
```
kubectl get pod --namespace=prod | grep '^jupyter-' | grep 'd$' | awk '{print $1}')
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

## Delete all pods that match a given name

Sometimes you want to delete all the pods for a given repository. The easiest
way to do this is to name-match the part of the pod name that corresponds to
the repo (since there will be a bunch of random characters as well).

Here's a python script that will match pods with a given name and delete them
(you need to uncomment the line to actually do the deleting). The script can
be run by changing your directory to the root of this repository, then running

```
python scripts/delete_pods_matching_name.py <your-query> --delete
```

## Delete all user pods older than a given number of hours

We use the Kubernetes cluster autoscaler, which
removes nodes from the kubernetes cluster when they have
been 'empty' for more than 10 minutes However, we
have issues where some pods get 'stuck' and never actually
die, sometimes forever. This causes nodes to not be
killed automatically.

You can use the 'old-user-pods.py' script to lis/kill these pods. You can run it with:

```bash
./scripts/old-user-pods.py <number-of-hours> --delete
```

If you do not pass --delete, it will simply print all the matching pods.
You will need the `kubernetes` python library installed to use this script!