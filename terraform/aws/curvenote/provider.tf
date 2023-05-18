terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }

  required_version = ">= 1.4.6"

  # Bootstrapping
  # 1. comment this out for a new deployment
  # 2. run the deployment to create the S3 bucket
  # 3. uncomment this and migrate the tfstate to S3
  backend "s3" {
    bucket = "binderhub-tfstate-7rjazazm1c7k"
    key    = "tfstate/dev/binderhub-dev"
    region = "us-east-2"
    # dynamodb_table = "dynamodb-state-locking"
  }
}

provider "aws" {
  region = var.region
}

