# output "cluster_name" {
#   description = "Kubernetes Cluster Name"
#   value       = var.cluster_name
# }

# output "cluster_oidc_issuer_url" {
#   description = "The URL on the EKS cluster for the OpenID Connect identity provider"
#   value       = module.eks.cluster_oidc_issuer_url
# }

# data "tls_certificate" "cluster_tls_certificate" {
#   url = module.eks.cluster_oidc_issuer_url
# }

# output "cluster_tls_certificate_sha1_fingerprint" {
#   description = "The SHA1 fingerprint of the public key of the cluster's certificate"
#   value       = data.tls_certificate.cluster_tls_certificate.certificates[*].sha1_fingerprint
# }
