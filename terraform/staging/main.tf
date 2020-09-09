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

resource "google_container_cluster" "staging" {
  name = "staging"

  min_master_version = "1.16"

  # terraform recommends removing the default node pool
  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "pool" {
  name       = "pool-2020-09"
  cluster    = google_container_cluster.staging.name
  node_count = 2

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 500
    disk_type    = "pd-standard"

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}

resource "google_compute_global_address" "staging" {
  name        = "staging"
  description = "public ip for the staging cluster"
}

output "public_ip" {
  value = google_compute_global_address.staging.address
}
