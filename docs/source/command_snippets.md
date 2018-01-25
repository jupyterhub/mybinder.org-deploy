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
