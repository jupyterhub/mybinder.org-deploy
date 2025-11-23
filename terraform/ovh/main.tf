terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "2.8.0"
    }
    harbor = {
      source  = "goharbor/harbor"
      version = "3.11.2"
    }
  }
  # store state on gcs, like other clusters
  backend "s3" {
    bucket = "mybinder-2i2c-tf-state"
    key    = "terraform.tfstate"
    region = "us-east-va"
    # Terraform 1.6.0
    # https://github.com/hashicorp/terraform/issues/33983#issuecomment-1801632383
    endpoints = {
      s3 = "https://s3.us-east-va.io.cloud.ovh.us"
    }
    skip_requesting_account_id  = true
    skip_credentials_validation = true
    skip_region_validation      = true
  }
}

provider "ovh" {
  endpoint = var.endpoint
  # credentials loaded via source ./secrets/ovh-creds.sh
}
