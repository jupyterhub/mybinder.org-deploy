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

# load harbor credentials from harbor chart config
# (avoids redundancy)
locals {
  config        = yamldecode(file("${path.module}/../../config/${var.name}.yaml"))
  secret_config = yamldecode(file("${path.module}/../../secrets/config/${var.name}.yaml"))
}

provider "harbor" {
  url      = "https://${local.config.harbor.expose.ingress.hosts.core}"
  username = "admin"
  password = local.secret_config.harbor.harborAdminPassword
}
