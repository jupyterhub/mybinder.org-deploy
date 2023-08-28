terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.5"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.21"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  required_version = ">= 1.4.6"
}
