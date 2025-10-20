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
  endpoint = "ovh-us"
  # credentials loaded via source ./secrets/ovh-creds.sh
}

locals {
  # FIXME: Turn this into variables when we have more than 1
  service_name = "5e4c805d3c614a1085d7b7bc1fee46d6" # id of the project `mybinder-2i2c`
  # Locate near our hetzner nodes, just in case we want to do data transfer in the future
  region = "US-EAST-VA"
}

