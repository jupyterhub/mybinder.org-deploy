terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  required_version = ">= 1.4.6"

  # Bootstrapping
  # 1. comment this out for a new deployment
  # 2. run the deployment to create the S3 bucket
  # 3. uncomment this and migrate the tfstate to S3
  backend "s3" {
    bucket         = "binderhub-tfstate-7rjazazm1c7k"
    key            = "tfstate/dev/binderhub-dev"
    region         = "us-east-2"
    dynamodb_table = "dynamodb-state-locking"
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      "owner" : "binderhub"
    }
  }
}

# Needed so that Terraform can manage the EKS auth configmap
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.binderhub.token
}
