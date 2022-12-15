terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 4.42"
    }
  }
}

provider "aws" {
  region = local.region
}

locals {
  cluster_name = "pangeo-mybinder"
  region       = "us-west-2"
}

data "aws_availability_zones" "available" {}

# Setup a VPC and subnets
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.18"

  name = "${local.cluster_name}-vpc"

  cidr = "10.0.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 3)

  private_subnets = []
  public_subnets  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]

  enable_nat_gateway   = false
  single_nat_gateway   = false
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = 1
  }

  private_subnet_tags = {}
}

# Setup security groups for core and user node groups
resource "aws_security_group" "node_group_core" {
  name_prefix = "node_group_core"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [
      "10.0.0.0/8",
    ] 
  }
}

resource "aws_security_group" "node_group_user" {
  name_prefix = "node_group_user"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = [
      "192.168.0.0/16",
    ] 
  }
}

# Setup EKS cluster with control plane and two managed node groups
module "eks" {
  source       = "terraform-aws-modules/eks/aws"
  version      = "~> 18.31"
  cluster_name = local.cluster_name

  # k8s v1.24 allows us to scale managed node groups to zero
  # ref: https://github.com/aws/containers-roadmap/issues/724
  cluster_version = "1.24"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnets

  eks_managed_node_group_defaults = {
    # Disabling and using externally provided security groups
    create_security_group                 = false
    attach_cluster_primary_security_group = true
  }

  eks_managed_node_groups = {
    # core node group
    core = {
      name = "core"

      instance_types = ["t3.small"]

      min_size     = 0
      max_size     = 2
      desired_size = 1

      vpc_security_group_ids = [
        aws_security_group.node_group_core.id
      ]
    }

    # user node group
    user = {
      name = "user"

      instance_types = ["t3.small"]

      min_size     = 0
      max_size     = 100
      desired_size = 0

      vpc_security_group_ids = [
        aws_security_group.node_group_user.id
      ]
    }
  }
}
