# tc-init

Kubernetes init container for throttling bandwidth with tc.

Currently, only upload rate limits work (sending data out of the container).

Use with:

```yaml
spec:
  initContainers:
  - name: tc-init
    image: minrk/tc-init:0.0.1
    env:
    - name: UPLOAD_RATE
      value: 1mbit
    securityContext:
      capabilities:
        add:
        - NET_ADMIN
```
