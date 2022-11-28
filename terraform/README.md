# Terraform folder structure

We keep terraform files for repeatable deployment of similar infrastructure
within this folder. While terraform configuration can be _applied_ agnostically
to different cloud providers, each providers have different terraform interfaces
and modules to define the infrastructure; therefore, we cannot _write_
terraform configuration agnostically.

For each cloud provider we provide terraform config for, we have a sub-folder
within this folder:

- `gcp`: This folder contains terraform config that interacts with Google
  Cloud Platform
- `aws`: This folder contains terraform config that interacts with Amazon
  Web Services
