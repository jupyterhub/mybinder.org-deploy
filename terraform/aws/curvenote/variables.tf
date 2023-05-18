variable "region" {
  default     = "us-east-2"
  description = "AWS region"
}

variable "cluster_name" {
  description = "EKS cluster name"
  default     = "binder-dev"
}

variable "k8s_api_cidrs" {
  default     = ["myip"]
  description = "CIDRs that have access to the K8s API, default current IP of user"
}

variable "worker-group-1-number-azs" {
  # Use just one so we don't have to deal with node/volume affinity-
  # can't use EBS volumes across AZs
  default     = 1
  description = "Number of AZs to use for worker-group-1"
}
