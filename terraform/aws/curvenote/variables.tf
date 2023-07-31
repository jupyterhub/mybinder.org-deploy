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

variable "number_azs" {
  type = number
  # Use just one so we don't have to deal with node/volume affinity-
  # can't use EBS volumes across AZs
  default     = 1
  description = "Number of AZs to use"
}

variable "instance_type_wg1" {
  type        = string
  default     = "r6a.2xlarge"
  description = "Worker-group-1 EC2 instance type"
}

variable "use_bottlerocket" {
  type        = bool
  default     = false
  description = "Use Bottlerocket for worker nodes"
}

variable "root_volume_size" {
  type        = number
  default     = 100
  description = "Root volume size in GB"
}

variable "wg1_size" {
  type        = number
  default     = 2
  description = <<-EOT
    Worker-group-1 initial desired number of nodes.
    Note this has no effect after the cluster is provisioned:
    - https://github.com/terraform-aws-modules/terraform-aws-eks/issues/2030
    - https://github.com/bryantbiggs/eks-desired-size-hack
    Manually change the node group size in the AWS console instead.
    EOT
}

variable "wg1_max_size" {
  type        = number
  default     = 2
  description = "Worker-group-1 maximum number of nodes"
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

variable "github_oidc_role_suffix" {
  type        = string
  description = <<-EOT
    The suffix of the IAM role that will be created for the GitHub OIDC provider.
    Will be joined to var.cluster_name with a hyphen.
    EOT
  default     = "github-oidc-mybinderorgdeploy"
}

variable "permissions_boundary_name" {
  type        = string
  description = <<-EOT
    The name of the permissions boundary to attach to all IAM roles.
    Specify if you are using a limited IAM role for deployment.
    EOT
  default     = "system/binderhub_policy"
}
