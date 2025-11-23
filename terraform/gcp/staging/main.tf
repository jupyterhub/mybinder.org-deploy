terraform {
  backend "gcs" {
    bucket = "tf-state-binder-staging"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = "binderhub-288415"
  region  = "us-central1"
  zone    = "us-central1-a"
}

locals {
  gke_version = "1.24.10-gke.2300"
}

module "mybinder" {
  source                = "../modules/mybinder"
  name                  = "staging"
  gke_master_version    = local.gke_version
  use_artifact_registry = true
  federation_members    = []
}

# define node pools here, too hard to encode with variables
resource "google_container_node_pool" "pool" {
  name    = "pool-2023-04-spot"
  cluster = module.mybinder.cluster_name

  autoscaling {
    min_node_count = 1
    max_node_count = 3
  }

  version = local.gke_version

  node_config {
    # e2-medium is 2cpu, 8GB shared-core
    # only 1 CPU allocatable, though, and k8s itself needs most of that
    # e2-standard-2 is 2x as expensive
    # but 2 e2-standard-2 is $100/month
    machine_type = "e2-standard-2"
    # spot = true increases disruption,
    # but saves ~70%
    spot = true
    disk_size_gb = 100
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
  # do not recreate pools that have been auto-upgraded

  lifecycle {
    ignore_changes = [
      version
    ]
  }
}

# output "public_ip" {
#   value       = module.mybinder.public_ip
#   description = "store in ingress-nginx.controller.service.loadBalancerIP"
# }

output "private_keys" {
  value       = module.mybinder.private_keys
  description = "GCP service account keys"
  sensitive   = true
}

output "events_archiver_keys" {
  value     = module.mybinder.events_archiver_keys
  sensitive = true
}
