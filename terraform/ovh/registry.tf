data "ovh_cloud_project_capabilities_containerregistry_filter" "registry_plan" {
  service_name = local.service_name
  # SMALL is 200GB (too small)
  # MEDIUM is 600GB
  # LARGE is 5TiB
  plan_name = "LARGE"
  region    = local.region
}

resource "ovh_cloud_project_containerregistry" "registry" {
  service_name = local.service_name
  plan_id      = data.ovh_cloud_project_capabilities_containerregistry_filter.registry_plan.id
  region       = data.ovh_cloud_project_capabilities_containerregistry_filter.registry_plan.region
  name         = "mybinder-ovh"
}

# admin user (needed for harbor provider)
resource "ovh_cloud_project_containerregistry_user" "admin" {
  service_name = ovh_cloud_project_containerregistry.registry.service_name
  registry_id  = ovh_cloud_project_containerregistry.registry.id
  email        = "mybinder-admin@mybinder.org"
  login        = "mybinder-admin"
}


