terraform {
  required_providers {
    harbor = {
      source  = "goharbor/harbor"
      version = "3.11.2"
    }
  }
  # store state on s3, like other clusters
  backend "s3" {
    bucket = "mybinder-hetzner-2i2c-tf-state"
    key    = "${var.name}.tfstate"
    endpoints = {
      s3 = var.state_s3_endpoint
    }
    region                      = "unused"
    skip_requesting_account_id  = true
    skip_credentials_validation = true
    skip_region_validation      = true
  }
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
