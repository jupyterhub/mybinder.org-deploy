
variable "name" {
  type        = string
  description = <<-EOT
    The name of the deployment.
    Used in various names.
  EOT
}

variable "registry_quota_gb" {
  type = number
  default = 10000
  description = <<-EOT
  harbor registry project quota size in gigabytes
  EOT
}

variable "registry_users" {
  type = set(string)
  default = []
  description = <<-EOT
  harbor registry users
  One builder (push/pull) and one puller (pull-only) robot account
  will be created for each name listed here.
  EOT
}
