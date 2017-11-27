# A place to put the collective wisdom of the Binder project.

* When you are in an outage, focus only on fixing the outage - do not try to do anything else.
* Prefer minor annoyances happening infrequently but at regular intervals, rather than major annoyances happening rarely but at unpredictable intervals.


# Cull all pods older than four hours

```
kubectl get pod | grep '^jupyter-' | grep '\(\([12][0-9]\|[4-9]\)h\|d\)$'
```
or to get all those that hav eexisted for more than 24hours
```
kubectl delete pod $(kubectl get pod | grep '^jupyter-' | grep 'd$' | awk '{print $1}')
```
