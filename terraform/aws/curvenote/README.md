# AWS infrastructure on CurveNote

## Bootstrapping (first time only!)

The Terraform state file is stored in a remote S3 bucket which must be created before the first deployment.
This should only be run once!

TODO: enable Dynamo DB state locking

```
cd bootstrap
terraform init
terraform apply
cd ..
```
