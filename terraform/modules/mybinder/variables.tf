# terraform variables
# put stuff here that should be different for prod and staging

variable "name" {
  type        = string
  description = "Name of the deployment"
}

variable "gke_master_version" {
  type        = string
  description = "GKE min master version"
  default     = "1.16"
}

variable "sql_tier" {
  type        = string
  description = "SQL instance tier"
  default     = "db-f1-micro"
}

variable "deployer_permissions" {
  type        = list(string)
  description = "Permissions for the deployer"
  default = [
    "container.apiServices.delete",
    "container.apiServices.get",
    "container.apiServices.list",
    "container.clusters.create",
    "container.clusters.get",
    "container.clusters.getCredentials",
    "container.clusters.list",
    "container.configMaps.update",
    "container.customResourceDefinitions.create",
    "container.customResourceDefinitions.delete",
    "container.customResourceDefinitions.get",
    "container.customResourceDefinitions.list",
    "container.customResourceDefinitions.update",
    "container.customResourceDefinitions.updateStatus",
    "container.daemonSets.get",
    "container.daemonSets.list",
    "container.deployments.create",
    "container.deployments.get",
    "container.deployments.list",
    "container.deployments.update",
    "container.pods.get",
    "container.pods.list",
    "container.pods.portForward",
    "container.services.get",
  ]
}
