terraform {
  backend "gcs" {
    bucket = "tf-state-binder-staging"
    prefix = "terraform/state"
  }
}

provider "google" {
  version = "~> 3.39"
  project = "binderhub-288415"
  region  = "us-central1"
  zone    = "us-central1-a"
}

locals {
  gke_version = "1.16.13-gke.401"
}

module "mybinder" {
  source = "../modules/mybinder"

  name               = "staging"
  gke_master_version = local.gke_version
}

# define node pools here, too hard to encode with variables
resource "google_container_node_pool" "pool" {
  name    = "pool-2020-09"
  cluster = module.mybinder.cluster_name

  autoscaling {
    min_node_count = 1
    max_node_count = 4
  }

  version = local.gke_version

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 500
    disk_type    = "pd-standard"
    # https://www.terraform.io/docs/providers/google/r/container_cluster.html#oauth_scopes-1
    oauth_scopes = [
      "storage-ro",
      "logging-write",
      "monitoring",
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

# output "public_ip" {
#   value       = module.mybinder.public_ip
#   description = "store in ingress-nginx.controller.service.loadBalancerIP"
# }

output "private_keys" {
  value       = module.mybinder.private_keys
  description = "GCP serice account keys"
  sensitive   = true
}
