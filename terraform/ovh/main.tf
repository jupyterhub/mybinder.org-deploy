terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "2.10.0"
    }
    harbor = {
      source  = "goharbor/harbor"
      version = "3.11.2"
    }
  }
  # store state on s3, like other clusters
  backend "s3" {
    bucket = "mybinder-2i2c-bids-tf-state"
    key    = "${var.name}.tfstate"
    endpoints = {
      s3 = "https://s3.us-east-va.io.cloud.ovh.us"
    }
    region                      = lower(var.region)
    skip_requesting_account_id  = true
    skip_credentials_validation = true
    skip_region_validation      = true
  }
}

provider "ovh" {
  endpoint = var.endpoint
  # credentials loaded via source ./secrets/ovh-creds.sh
}
