# cloning a registry

initially written to run from a local environment,
goal is to run on an existing cluster with the registry to migrate _from_, to minimize egress cost.

Assumes access to `binder-secret`, `binder-build-docker-config` in binder namespace.

Create an auth secret with:

```
skopeo login registry.2i2c.mybinder.org --authfile=./auth.json
```

and login with the credentials from `secrets/config/hetzner-2i2c.yaml`

and then create a secret with:

```
kubectl create secret generic migrate-registry-auth --from-file=./auth.json
```
