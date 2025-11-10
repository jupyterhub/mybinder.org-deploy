# now configure the registry via harbor itself
provider "harbor" {
  url      = ovh_cloud_project_containerregistry.registry.url
  username = ovh_cloud_project_containerregistry_user.admin.login
  password = ovh_cloud_project_containerregistry_user.admin.password
}

# user builds go in mybinder-builds
# these are separate for easier separation of retention policies
resource "harbor_project" "mybinder-builds" {
  name = "mybinder-builds"
}

resource "harbor_robot_account" "builder" {
  name        = "builder"
  description = "BinderHub builder: push new user images"
  level       = "project"
  permissions {
    access {
      action   = "push"
      resource = "repository"
    }
    access {
      action   = "pull"
      resource = "repository"
    }
    kind      = "project"
    namespace = harbor_project.mybinder-builds.name
  }
}

resource "harbor_robot_account" "user-puller" {
  name        = "user-puller"
  description = "Pull access to user images"
  level       = "project"
  permissions {
    access {
      action   = "pull"
      resource = "repository"
    }
    kind      = "project"
    namespace = harbor_project.mybinder-builds.name
  }
}


resource "harbor_retention_policy" "builds" {
  # run retention policy on Saturday morning
  scope    = harbor_project.mybinder-builds.id
  schedule = "0 0 7 * * 6"
  # rule {
  #   repo_matching        = "**"
  #   tag_matching         = "**"
  #   most_recently_pulled = 1
  #   untagged_artifacts   = false
  # }
  rule {
    repo_matching          = "**"
    tag_matching           = "**"
    n_days_since_last_pull = 30
    untagged_artifacts     = false
  }
  rule {
    repo_matching          = "**"
    tag_matching           = "**"
    n_days_since_last_push = 7
    untagged_artifacts     = false
  }
}

resource "harbor_garbage_collection" "gc" {
  # run garbage collection on Sunday morning
  # try to make sure it's not run at the same time as the retention policy
  schedule = "0 0 7 * * 0"
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

# output "registry_culler_name" {
#   value     = harbor_user.culler.username
#   sensitive = true
# }

# output "registry_culler_password" {
#   value     = harbor_user.culler.password
#   sensitive = true
# }

output "registry_builder_name" {
  value     = harbor_robot_account.builder.full_name
  sensitive = true
}

output "registry_builder_token" {
  value     = harbor_robot_account.builder.secret
  sensitive = true
}

output "registry_user_puller_name" {
  value     = harbor_robot_account.user-puller.full_name
  sensitive = true
}
output "registry_user_puller_token" {
  value     = harbor_robot_account.user-puller.secret
  sensitive = true
}
