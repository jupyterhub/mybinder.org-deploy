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
  version         = "19.15.2"
  cluster_name    = var.cluster_name
  cluster_version = var.k8s_version
  subnet_ids      = module.vpc.public_subnets

  cluster_endpoint_private_access      = true
  cluster_endpoint_public_access       = true
  cluster_endpoint_public_access_cidrs = var.k8s_api_cidrs

  vpc_id = module.vpc.vpc_id

  enable_irsa                   = var.enable_irsa
  iam_role_permissions_boundary = local.permissions_boundary_arn

  # Anyone in the AWS account with sufficient permissions can access the cluster
  aws_auth_accounts = [
    data.aws_caller_identity.current.account_id,
  ]

  eks_managed_node_group_defaults = {
    capacity_type                 = "SPOT"
    iam_role_permissions_boundary = local.permissions_boundary_arn
  }

  eks_managed_node_groups = {
    worker_group-1 = {
      name           = "${var.cluster_name}-wg1"
      instance_types = ["t3a.large"]
      ami_type       = "BOTTLEROCKET_x86_64"
      platform       = "bottlerocket"

      # additional_userdata = "echo foo bar"
      vpc_security_group_ids = [
        aws_security_group.all_worker_mgmt.id,
        aws_security_group.worker_group_all.id,
      ]
      min_size     = 1
      max_size     = 2
      desired_size = 1

      # Disk space can't be set with the default custom launch template
      # disk_size = 100
      block_device_mappings = [
        {
          # https://github.com/bottlerocket-os/bottlerocket/discussions/2011
          device_name = "/dev/xvdb"
          ebs = {
            volume_size = 100
            volume_type = "gp3"
          }
        }
      ]

      subnet_ids = slice(module.vpc.public_subnets, 0, var.worker_group_1_number_azs)
    },
    # Add more worker groups here
  }
}

data "aws_eks_cluster" "cluster" {
  name = split("/", module.eks.cluster_arn)[1]
}

data "aws_eks_cluster_auth" "cluster" {
  name = split("/", module.eks.cluster_arn)[1]
}
