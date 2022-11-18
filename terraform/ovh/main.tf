terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 0.22.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.3.2"
    }
    harbor = {
      source = "BESTSELLER/harbor"
      # can't use 3.0, which requires harbor 2.2 for robot accounts
      # OVH deploys 2.0.1
      version = "~> 2.0.11"
    }
  }
  # store state on gcs, like other clusters
  backend "s3" {
      bucket = "tf-state-ovh"
      key    = "terraform.tfstate"
      region = "gra"
      endpoint = "s3.gra.io.cloud.ovh.net"
      skip_credentials_validation = true
      skip_region_validation = true
    }
}

provider "ovh" {
  endpoint = "ovh-eu"
  # credentials loaded via source ../secrets/ovh-creds.sh
}

locals {
  service_name = "b309c78177f1458187add722e8db8dc2"
  cluster_name = "ovh2"
  # GRA9 is colocated with registry
  region = "GRA9"
}

# create a private network for our cluster
resource "ovh_cloud_project_network_private" "network" {
  service_name = local.service_name
  name         = local.cluster_name
  regions      = [local.region]
}

resource "ovh_cloud_project_network_private_subnet" "subnet" {
  service_name = local.service_name
  network_id   = ovh_cloud_project_network_private.network.id

  region  = local.region
  start   = "10.0.0.100"
  end     = "10.0.0.254"
  network = "10.0.0.0/24"
  dhcp    = true
}

resource "ovh_cloud_project_kube" "cluster" {
  service_name = local.service_name
  name         = local.cluster_name
  region       = local.region
  version      = "1.24"
  # make sure we wait for the subnet to exist
  depends_on = [ovh_cloud_project_network_private_subnet.subnet]

  # private_network_id is an openstackid for some reason?
  private_network_id = tolist(ovh_cloud_project_network_private.network.regions_attributes)[0].openstackid

  customization {
    apiserver {
      admissionplugins {
        enabled = ["NodeRestriction"]
        # disable AlwaysPullImages, which causes problems
        disabled = ["AlwaysPullImages"]
      }
    }
  }
  update_policy = "MINIMAL_DOWNTIME"
}

# ovh node flavors: https://www.ovhcloud.com/en/public-cloud/prices/

resource "ovh_cloud_project_kube_nodepool" "core" {
  service_name = local.service_name
  kube_id      = ovh_cloud_project_kube.cluster.id
  name         = "core-202211"
  # b2-15 is 4 core, 15GB
  flavor_name   = "b2-15"
  desired_nodes = 1
  max_nodes     = 3
  min_nodes     = 1
  autoscale     = true
  template {
    metadata {
      labels = {
        "mybinder.org/pool-type" = "core"
      }
    }
  }
}

resource "ovh_cloud_project_kube_nodepool" "user" {
  service_name = local.service_name
  kube_id      = ovh_cloud_project_kube.cluster.id
  name         = "user-202211"
  # r2-60 is 4 core, 60GB
  flavor_name   = "r2-60"
  desired_nodes = 1
  max_nodes     = 6
  min_nodes     = 1
  autoscale     = true
  template {
    metadata {
      labels = {
        "mybinder.org/pool-type" = "users"
      }
    }
  }
}

# outputs

output "kubeconfig" {
  value       = ovh_cloud_project_kube.cluster.kubeconfig
  sensitive   = true
  description = <<EOF
    # save output with:
    export KUBECONFIG=$PWD/../../secrets/ovh2-kubeconfig.yml
    terraform output -raw kubeconfig > $KUBECONFIG
    chmod 600 $KUBECONFIG
    kubectl config rename-context kubernetes-admin@ovh2 ovh2
    kubectl config use-context ovh2
    EOF
}

# registry

data "ovh_cloud_project_capabilities_containerregistry_filter" "registry_plan" {
  service_name = local.service_name
  # SMALL is 200GB (too small)
  # MEDIUM is 600GB
  # Large is 5TiB
  plan_name = "MEDIUM"
  region    = "GRA"
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


# now configure the registry via harbor itself
provider "harbor" {
  url      = ovh_cloud_project_containerregistry.registry.url
  username = ovh_cloud_project_containerregistry_user.admin.login
  password = ovh_cloud_project_containerregistry_user.admin.password
}

# chart images go in mybinder-chart
resource "harbor_project" "mybinder-chart" {
  name = "mybinder-chart"
  # chart images need to be public
  # because we can't have two pull secrets for one registry,
  # and harbor < 2.2 can't grant read-only access to more than one project
  # on the same registry
  public = true
}

# user builds go in mybinder-builds
# these are separate for easier separation of retention policies
resource "harbor_project" "mybinder-builds" {
  name = "mybinder-builds"
}


# TODO: robot accounts change with harbor 2.2 / harbor-provider 3.0
# in particular, we can drop the two separate pullers
resource "harbor_robot_account" "chartpress" {
  name        = "chartpress"
  description = "mybinder chartpress: access to push new chart images"
  project_id  = harbor_project.mybinder-chart.id
  actions     = ["push", "pull"]
}

resource "harbor_robot_account" "chart-puller" {
  name        = "chart-puller"
  description = "pull mybinder chart images"
  project_id  = harbor_project.mybinder-chart.id
  actions     = ["pull"]
}

resource "harbor_robot_account" "builder" {
  name        = "builder"
  description = "BinderHub builder: push new user images"
  project_id  = harbor_project.mybinder-builds.id
  actions     = ["push", "pull"]
}

resource "harbor_robot_account" "user-puller" {
  name        = "user-puller"
  description = "Pull access to user images"
  project_id  = harbor_project.mybinder-builds.id
  actions     = ["pull"]
}

# retention policies created by hand
# OVH harbor is too old for terraform provider (2.0.1, need 2.2)
# resource "harbor_retention_policy" "user" {
#   scope    = harbor_project.mybinder-builds.id
#   schedule = "weekly"
#   rule {
#     most_recently_pulled = 1
#   }
#   rule {
#     n_days_since_last_pull = 30
#   }
#   rule {
#     n_days_since_last_push = 7
#   }
# }
#
# resource "harbor_retention_policy" "chart" {
#   scope    = harbor_project.mybinder-chart.id
#   schedule = "weekly"
#   # keep the most recent 5 versions
#   # (by both push and pull, which should usually be the same)
#   rule {
#     most_recently_pulled = 5
#   }
#   rule {
#     most_recently_pushed = 5
#   }
#   rule {
#     n_days_since_last_push = 7
#   }
# }

resource "harbor_garbage_collection" "gc" {
  schedule        = "weekly"
  delete_untagged = true

}

# registry outputs

output "registry_url" {
  value = ovh_cloud_project_containerregistry.registry.url
}

output "registry_admin_login" {
  value     = ovh_cloud_project_containerregistry_user.admin.login
  sensitive = true
}

output "registry_admin_password" {
  value     = ovh_cloud_project_containerregistry_user.admin.password
  sensitive = true
}

output "registry_chartpress_token" {
  value     = harbor_robot_account.chartpress.token
  sensitive = true
}

output "registry_chart_puller_token" {
  value     = harbor_robot_account.chart-puller.token
  sensitive = true
}

output "registry_builder_token" {
  value     = harbor_robot_account.builder.token
  sensitive = true
}

output "registry_user_puller_token" {
  value     = harbor_robot_account.user-puller.token
  sensitive = true
}
