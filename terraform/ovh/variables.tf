variable "endpoint" {
  type        = string
  description = <<-EOT
  OVH Endpoint to use for making API calls

  One of "ovh-us", "ovh-ca" or "ovh-eu", based on which *kind of OVH account*
  is being used.
  EOT
}


variable "region" {
  type        = string
  description = <<-EOT
  OVH Region to put all infrastructure in
  EOT
}


variable "service_name" {
  type        = string
  description = <<-EOT
  OVH Public Cloud Project ID to create infrastructure in
  EOT
}

variable "registry_name" {
  type        = string
  description = <<-EOT
  Name of the managed registry to create
  EOT
}

variable "registry_plan" {
  type        = string
  description = <<-EOT
  What registry plan to put this registry on.

  Options are:

    - SMALL is 200GB (too small for production loads)
    - MEDIUM is 600GB
    - LARGE is 5TiB
  EOT
}
