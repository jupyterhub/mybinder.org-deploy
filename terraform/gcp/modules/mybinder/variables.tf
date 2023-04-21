# terraform variables
# put stuff here that should be different for prod and staging

variable "name" {
  type        = string
  description = "Name of the deployment"
}

variable "gke_master_version" {
  type        = string
  description = "GKE min master version"
  default     = "1.17"
}

variable "gke_location" {
  type        = string
  description = "GKE location for cluster if different from provider zone, e.g. us-central1 for regional cluster"
  default     = null
}

variable "use_artifact_registry" {
  type        = bool
  description = "Use artifact registry instead of legacy container registry"
  default     = false
}

variable "registry_location" {
  type        = string
  description = "Registry location for cluster if different from provider region, e.g. us for multi-region"
  default     = null
}

variable "sql_tier" {
  type        = string
  description = "SQL instance tier"
  default     = "db-f1-micro"
}

variable "federation_members" {
  type        = list(any)
  description = "List of federation members by name"
  default     = []
}
