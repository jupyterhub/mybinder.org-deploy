# now configure the registry via harbor itself

# load harbor credentials from harbor chart config
# (avoids redundancy)
locals {
  config        = yamldecode(file("${path.module}/../../config/${var.name}.yaml"))
  secret_config = yamldecode(file("${path.module}/../../secrets/config/${var.name}.yaml"))
}

provider "harbor" {
  url      = "https://${local.config.harbor.expose.ingress.hosts.core}"
  username = "admin"
  password = local.secret_config.harbor.harborAdminPassword
}

# user builds go in mybinder-builds
# these are separate for easier separation of retention policies
resource "harbor_project" "mybinder-builds" {
  name = "mybinder-builds"
  storage_quota = var.registry_quota_gb
}

resource "harbor_robot_account" "builder" {
  for_each    = var.registry_users
  name        = "${each.key}-builder"
  description = "BinderHub builder for ${each.key}: push new user images"
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
  for_each    = var.registry_users
  name        = "${each.key}-user-puller"
  description = "Pull access to user images for ${each.key}"
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
  schedule        = "0 0 7 * * 0"
  delete_untagged = true
}

# registry outputs
output "registry_creds" {
  value = merge(
    {
      for name in var.registry_users:
        harbor_robot_account.builder[name].full_name => harbor_robot_account.builder[name].secret
    }, {
      for name in var.registry_users:
        harbor_robot_account.user-puller[name].full_name => harbor_robot_account.user-puller[name].secret
    },
  )
  sensitive = true
}
