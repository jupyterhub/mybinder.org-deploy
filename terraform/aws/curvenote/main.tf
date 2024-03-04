terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.5"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.21"
    }
  }

  required_version = ">= 1.4.6"

  # Bootstrapping: Create the bucket and DynamoDB table using the ./bootstrap directory
  backend "s3" {
    bucket         = "binderhub-tfstate-7rjazazm1c7k"
    key            = "tfstate/dev/binderhub-dev"
    region         = "us-east-2"
    dynamodb_table = "dynamodb-state-locking"
  }
}

provider "aws" {
  region = "us-east-2"
  default_tags {
    tags = {
      "owner" : "binderhub"
    }
  }
}

module "binder-eks" {
  source            = "../binder-eks"
  region            = "us-east-2"
  cluster_name      = "binderhub"
  k8s_version       = "1.26"
  k8s_api_cidrs     = ["0.0.0.0/0"]
  number_azs        = 1
  instance_type_wg1 = "r6a.4xlarge"
  use_bottlerocket  = false
  root_volume_size  = 200
  wg1_size          = 2
  wg1_max_size      = 2

  # The following configuration is needed if you are using a limited IAM role for deployment
  enable_irsa  = false
  oidc_created = true

  github_oidc_role_suffix   = "github-oidc-mybinderorgdeploy"
  permissions_boundary_name = "system/binderhub_policy"
}

# Needed so that Terraform can manage the EKS auth configmap
provider "kubernetes" {
  host                   = module.binder-eks.cluster_endpoint
  cluster_ca_certificate = module.binder-eks.cluster_ca_certificate
  token                  = module.binder-eks.eks_token
}
