# AWS infrastructure on CurveNote

This deployment is run in an [AWS account owned by Curvenote](https://github.com/jupyterhub/mybinder.org-deploy/issues/2629), with restricted user accounts provided to the mybinder team.

## AWS account prerequisites

IAM roles, and users, and some other base infrastructure is defined in a separate private repository under the control of the AWS account administrator.
Contact the mybinder team and @stevejpurves to obtain access.

## Bootstrapping (new deployment only)

The Terraform state file is stored in a remote S3 bucket which must be created before the first deployment, along with a DynamoDB lock.
This should only be run once!

```
cd bootstrap
terraform init
terraform apply
cd ..
```

If you want to use this to create multiple deployments you **must** modify

`terraform { backend "s3" { ... } }`

in [`provider.tf`](provider.tf) to use a different key and/or bucket.
Failure to do this will result in the original deployment becoming unmanageable- it will not be possible to modify or even delete it with Terraform!

## Deploying

Ensure you have a recent version of Terraform.
The minimum required version is specified by `terraform { required_version } }` in [`provider.tf`](provider.tf).

The full deployment requires an OIDC Provider that must be created by a privileged administrator.

Deploy the Kubernetes cluster without the OIDC Provider by setting the following [variables](variables.tf):

```
enable_irsa = false
```

```
terraform init
terraform apply
```

Copy [`openid_connect_providers.tf.example`](./openid_connect_providers.tf.example) and edit the `resource "aws_iam_openid_connect_provider" "binderhub_eks_oidc_provider" { thumbprint_list, url }` fields, using the values from [`outputs.tf`](./outputs.tf).

Ask the AWS account administrator to create the OIDC Provider, and retrieve the OIDC binderhub provider ARN.

Set

```
oidc_created = true
```

and deploy again

```
terraform apply
```

## Obtaining a kubeconfig file

```
aws eks update-kubeconfig --name binderhub --kubeconfig /path/to/kubeconfig
kubectl --kubeconfig=/path/to/kubeconfig get nodes
```
