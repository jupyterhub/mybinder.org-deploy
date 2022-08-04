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
  description = "GKE location for cluster if different, e.g. us-central1 for regional cluster"
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
