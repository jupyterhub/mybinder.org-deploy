# scripts for managing mybinder.org

## delete-old-images.py

This script talks to the docker registry API and tries to delete old images.
The script has the following conditions to check:

- images that don't match the build prefix (e.g. changing the BinderHub.image_prefix in configuration)
- limiting the number of builds stored for a given repo (`--max-builds`)
- deleting all images older than a certain date (`--delete-before`)

Use:

```bash
python3 scripts/delete-old-images.py prod --dry-run
```

This script is not run automatically.

## prune_harbor.py

Harbor registries have far more powerful garbage collection and image retention policies than the basic docker registry implementation,
or Google Container Registry.
The only missing piece is removing _repositories_ that have no artifacts in them,
which seems to affect the performance of those policies and other aspects of harbor.

This script only deletes repositories with no images in them.

Right now, this script is run for our harbor-using federation members
(currently OVH),
via the [prune-harbor workflow](../.github/workflows/prune-harbor.yaml).
Credentials are found in `secrets/{name}-harbor.yaml`.

Use:

```bash
python3 scripts/prune_harbor.py ovh2
```
