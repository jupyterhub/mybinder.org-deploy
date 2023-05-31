# Initial setup of S3 bucket to store tfstate file
variable "bucket-name" {
  type = string
  # python -c 'import random; import string; print("".join(random.choices(string.ascii_lowercase + string.digits,k=12)))'
  default     = "binderhub-tfstate-7rjazazm1c7k"
  description = "Bucket name for Terraform state file"
}

variable "region" {
  type        = string
  default     = "us-east-2"
  description = "AWS region"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.region
  default_tags {
    tags = {
      "owner" : "binderhub"
    }
  }
}

resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket-name
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "public-block" {
  bucket                  = aws_s3_bucket.bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# resource "aws_dynamodb_table" "tfstate-lock" {
#   hash_key = "LockID"
#   name     = "dynamodb-state-locking"
#   attribute {
#     name = "LockID"
#     type = "S"
#   }
#   billing_mode = "PAY_PER_REQUEST"
# }
