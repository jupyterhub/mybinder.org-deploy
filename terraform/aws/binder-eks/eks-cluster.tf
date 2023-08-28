# https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/19.15.2
# Full example:
# https://github.com/terraform-aws-modules/terraform-aws-eks/blame/v19.14.0/examples/complete/main.tf
# https://github.com/terraform-aws-modules/terraform-aws-eks/blob/v19.14.0/docs/compute_resources.md

data "aws_caller_identity" "current" {}

locals {
  permissions_boundary_arn = (
    var.permissions_boundary_name != null ?
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.permissions_boundary_name}" :
    null
  )
}

# This assumes the EKS service linked role is already created (or the current user has permissions to create it)
module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "19.15.3"
  cluster_name    = var.cluster_name
  cluster_version = var.k8s_version
  subnet_ids      = module.vpc.public_subnets

  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = var.k8s_api_cidrs

  vpc_id = module.vpc.vpc_id

  # Allow all allowed roles to access the KMS key
  kms_key_enable_default_policy = true
  # This duplicates the above, but the default is the current user/role so this will avoid
  # a deployment change when run by different users/roles
  kms_key_administrators = [
    "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root",
  ]

  enable_irsa                   = var.enable_irsa
  iam_role_permissions_boundary = local.permissions_boundary_arn

  eks_managed_node_group_defaults = {
    capacity_type                 = "SPOT"
    iam_role_permissions_boundary = local.permissions_boundary_arn
  }

  eks_managed_node_groups = {
    worker_group_1 = {
      name           = "${var.cluster_name}-wg1"
      instance_types = [var.instance_type_wg1]
      ami_type       = var.use_bottlerocket ? "BOTTLEROCKET_x86_64" : "AL2_x86_64"
      platform       = var.use_bottlerocket ? "bottlerocket" : "linux"

      # additional_userdata = "echo foo bar"
      vpc_security_group_ids = [
        aws_security_group.all_worker_mgmt.id,
        aws_security_group.worker_group_all.id,
      ]
      desired_size = var.wg1_size
      min_size     = 1
      max_size     = var.wg1_max_size

      # Disk space can't be set with the default custom launch template
      # disk_size = 100
      block_device_mappings = [
        {
          # https://github.com/bottlerocket-os/bottlerocket/discussions/2011
          device_name = var.use_bottlerocket ? "/dev/xvdb" : "/dev/xvda"
          ebs = {
            # Uses default alias/aws/ebs key
            encrypted   = true
            volume_size = var.root_volume_size
            volume_type = "gp3"
          }
        }
      ]

      subnet_ids = slice(module.vpc.public_subnets, 0, var.number_azs)
    },
    # Add more worker groups here
  }

  manage_aws_auth_configmap = true
  # Anyone in the AWS account with sufficient permissions can access the cluster
  aws_auth_accounts = [
    data.aws_caller_identity.current.account_id,
  ]
  aws_auth_roles = [
    {
      # GitHub OIDC role
      rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.cluster_name}-${var.github_oidc_role_suffix}"
      username = "binderhub-github-oidc"
      groups   = ["system:masters"]
    },
    {
      # GitHub OIDC terraform role
      rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.cluster_name}-${var.github_oidc_role_suffix}-terraform"
      username = "binderhub-github-oidc"
      groups   = ["system:masters"]
    },
    {
      # BinderHub admins role
      rolearn  = aws_iam_role.eks_access.arn
      username = "binderhub-admin"
      groups   = ["system:masters"]
    }
  ]
}

data "aws_eks_cluster_auth" "binderhub" {
  name = var.cluster_name
}
