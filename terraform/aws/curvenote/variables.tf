variable "region" {
  type        = string
  default     = "us-east-2"
  description = "AWS region"
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name"
  default     = "binderhub"
}

variable "k8s_version" {
  type        = string
  description = "Kubernetes cluster version"
  default     = "1.26"
}

variable "k8s_api_cidrs" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "CIDRs that have access to the K8s API"
}

variable "worker_group_1_number_azs" {
  type = number
  # Use just one so we don't have to deal with node/volume affinity-
  # can't use EBS volumes across AZs
  default     = 1
  description = "Number of AZs to use for worker-group-1"
}


# The following configuration is needed if you are using a limited IAM role for deployment

variable "enable_irsa" {
  type        = bool
  default     = false
  description = <<-EOT
    Disable if OIDC needs to be setup manually due to limited permissions.
    If you have full admin access, you can set this to true.
    EOT
}

variable "oidc_created" {
  type        = bool
  default     = true
  description = <<-EOT
    If enable_irsa is false and the OIDC provider has been manually created using
    the openid_connect_providers.tf.example file, set this to true.
    EOT
}

variable "permissions_boundary_name" {
  type        = string
  description = <<-EOT
    The name of the permissions boundary to attach to all IAM roles.
    Specify if you are using a limited IAM role for deployment.
    EOT
  default     = "system/binderhub_policy"
}
