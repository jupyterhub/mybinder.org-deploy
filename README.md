# tc-init

Kubernetes init container for throttling bandwidth with tc.

Currently, only egress bandwidth limits work (sending data out of the container).

## First things first: don't use this

...if you don't have to!

Kubernetes has [annotations](https://github.com/kubernetes/kubernetes/blob/v1.8.4/pkg/util/bandwidth/utils.go#L38)
that *should* enable you to accomplish bandwidth limits without any help:

```yaml
spec:
  annotations:
  - kubernetes.io/egress-bandwidth: 1M
  - kubernetes.io/ingress-bandwidth: 10M
```

Unfortunately, I've found that many network implementations do not respect these annotations (as of kubernetes 1.8, anyway),
so test if these more official annotations work before adopting tc-init.

## Using tc-init

Add tc-init to your containers as an initContainer.
It will run `tc` and limit the egress bandwidth to EGRESS_BANDWIDTH.
The value is passed to [tc](http://lartc.org/manpages/tc.txt),
e.g `10mbit` for ten megabits per second,
or `5mbps` for five mega*bytes* per second.

For example:

```yaml
spec:
  initContainers:
  - name: tc-init
    image: minrk/tc-init:0.0.2
    env:
    - name: EGRESS_BANDWIDTH
      value: 1mbit
    securityContext:
      capabilities:
        add:
        - NET_ADMIN
```
