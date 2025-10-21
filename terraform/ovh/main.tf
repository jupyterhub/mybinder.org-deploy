terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "2.8.0"
    }
    harbor = {
      source = "goharbor/harbor"
      version = "3.11.2"
    }
  }
  # store state on gcs, like other clusters
  backend "s3" {
    bucket                      = "mybinder-2i2c-tf-state"
    key                         = "terraform.tfstate"
    region                      = "us-east-va"
    endpoint                    = "https://s3.us-east-va.io.cloud.ovh.us"
    skip_credentials_validation = true
    skip_region_validation      = true
  }
}

provider "ovh" {
  endpoint = var.endpoint
  # credentials loaded via source ./secrets/ovh-creds.sh
}
