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

variable "deployer_permissions" {
  type        = list(string)
  description = "Permissions for the deployer"
  default = [
    "container.apiServices.delete",
    "container.apiServices.get",
    "container.apiServices.list",
    "container.clusterRoleBindings.get",
    "container.clusterRoleBindings.update",
    "container.clusterRoles.get",
    "container.clusterRoles.update",
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
    "container.mutatingWebhookConfigurations.get",
    "container.mutatingWebhookConfigurations.update",
    "container.pods.get",
    "container.pods.list",
    "container.pods.portForward",
    "container.roleBindings.get",
    "container.roleBindings.update",
    "container.roles.get",
    "container.roles.update",
    "container.secrets.create",
    "container.secrets.delete",
    "container.secrets.get",
    "container.secrets.list",
    "container.secrets.update",
    "container.serviceAccounts.get",
    "container.serviceAccounts.update",
    "container.services.get",
    "container.services.update",
    "container.validatingWebhookConfigurations.get",
    "container.validatingWebhookConfigurations.update",
  ]
}
