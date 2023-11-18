# BinderHub on AWS EKS

**_Important: Deploying this EKS cluster requires some manual steps after running Terraform_**

This module deploys an AWS EKS cluster with IRSA roles to support BinderHub ECR access.

The module has optional support for using a limited non-administrative AWS role with a permissions boundary to deploy the cluster.

For an example see [curvenote](../curvenote/README.md)

## Post-deployment steps

After running Terraform, you will need to perform the following steps:

### Install the AWS VPC CNI add-on

Using the AWS CLI:

1. Get the available vpc-cni versions: `aws eks describe-addon-versions --addon-name vpc-cni `
2. `aws eks create-addon --cluster-name binderhub --addon-name vpc-cni --addon-version v1.15.3-eksbuild.1 --resolve-conflicts OVERWRITE`
3. Wait for the status to change to `ACTIVE`: `aws eks describe-addon --cluster-name binderhub --addon-name vpc-cni`

You can also do this using the AWS EKS web console:

1. Go to the AWS EKS console and open the EKS cluster
2. Under `Add-ons` choose `Get more add-ons`
3. Select `Amazon VPC CNI`, click `Next`
4. Select latest version of the plugin, use the default IAM role `Inherit from node`, click `Next`
5. Client `Create`
6. Wait for the status to change to `Active`
