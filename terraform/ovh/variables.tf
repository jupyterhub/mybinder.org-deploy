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
  (e.g. US-EAST-VA)
  EOT
}

variable "zone" {
  type        = string
  description = <<-EOT
  OVH Zone where more specific
  (e.g. US-EAST-VA-1)
  EOT
}

variable "service_name" {
  type        = string
  description = <<-EOT
  OVH Public Cloud Project ID to create infrastructure in
  EOT
}

variable "name" {
  type        = string
  description = <<-EOT
    The name of the deployment.
    Used in various names.
  EOT
}

variable "vm" {
  type = object({
    # flavor and image: see lookup_flavor_image.py
    flavor_id : string,
    image_id : string,
  })
  default     = null
  nullable    = true
  description = <<-EOT
  VM instance configuration.
  EOT
}

variable "harbor" {
  type = object({
    # flavor and image: see lookup_flavor_image.py
    url : string,
  })
  default     = null
  nullable    = true
  description = <<-EOT
  VM instance configuration.
  EOT
}
