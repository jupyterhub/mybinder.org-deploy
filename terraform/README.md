# Terraform deployment info

Common configuration is in terraform/modules/mybinder

most deployed things are in mybinder/resource.tf
variables (mostly things that should differ in staging/prod) in mybinder/variables.tf

per-deployment config in $deployment/main.tf

Variables declared in mybinder/variables.tf can be overridden in $deployment/main.tf

First you must login to `gcloud` to gain application credentials:

```bash
gcloud auth application-default login
```

Then, to deploy e.g. staging:

```bash
cd staging
terraform apply
```

which will create a plan and prompt for confirmation.

Review the proposed changes and if they look right, type 'yes' to apply the changes.

## Getting secrets out

Terraform will create the service accounts needed for the deployment.
The private keys for these will need to be exported to `secrets/config/$deployment.yaml`.
**This part is not yet automated**.

To get a service-account key for deployment:

```bash
cd terraform/staging

terraform output -json private_keys | jq -r '.deployer' > ../../secrets/gke-auth-key-staging2.json
```

and to get private keys to put in secrets/config/${deployment}.yaml:

```bash
terraform output -json private_keys | jq '.["events-archiver"]' | pbcopy
```

with key names: "events-archiver", "matomo", and "binderhub-builder" and paste them into the appropriate fields in `secrets/config/$deployment.yaml`.


### Notes

- requesting previously-allocated static ip via loadBalancerIP did not work.
  Had to manually mark LB IP as static via cloud console.

- sql admin API needed to be manually enabled [here](https://console.developers.google.com/apis/library/sqladmin.googleapis.com)
- matomo sql data was manually imported/exported via sql dashboard and gsutil in cloud console
- events archive history was manually migrated via `gsutil -m rsync` in cloud console
