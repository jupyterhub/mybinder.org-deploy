module "harbor" {
  source            = "../modules/harbor"
  name              = var.name
  registry_quota_gb = var.registry_quota_gb
  registry_users    = var.registry_users
}

output "registry_creds" {
  value     = module.harbor.registry_creds
  sensitive = true
}
