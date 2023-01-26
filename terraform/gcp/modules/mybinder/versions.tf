terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.31"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.3.2"
    }
  }
  required_version = "~> 1.1"
}
