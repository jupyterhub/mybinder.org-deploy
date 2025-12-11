resource "ovh_cloud_project_user" "harbor" {
  service_name = var.service_name
  description  = "s3 user for container image registry"
  role_name    = "objectstore_operator"
}

resource "ovh_cloud_project_user_s3_credential" "harbor" {
  service_name = var.service_name
  user_id      = ovh_cloud_project_user.harbor.id
}

resource "ovh_cloud_project_storage" "registry" {
  service_name = var.service_name
  region_name = var.region
  name = "mybinder-registry-${var.name}"
  owner_id = ovh_cloud_project_user_s3_credential.harbor.user_id
}

resource "ovh_cloud_project_user_s3_policy" "policy" {
  service_name = ovh_cloud_project_user.harbor.service_name
  user_id      = ovh_cloud_project_user.harbor.id
  policy       = jsonencode({
    "Statement":[{
      "Sid": "RWContainer",
      "Effect": "Allow",
      "Action":["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket", "s3:ListMultipartUploadParts", "s3:ListBucketMultipartUploads", "s3:AbortMultipartUpload", "s3:GetBucketLocation"],
      "Resource":["arn:aws:s3:::${ovh_cloud_project_storage.registry.name}", "arn:aws:s3:::${ovh_cloud_project_storage.registry.name}/*"]
    },
    {
      # deny bucket creation, etc.
      "Sid" : "default-deny",
      "Effect" : "Deny",
      "Action" : [
        "s3:CreateBucket",
        "s3:DeleteBucket",
      ],
      "Resource" : ["arn:aws:s3:::*"]
    },
]})
}

output "registry_s3" {
  description = "s3 credentials for harbor registry"
  sensitive   = true
  value = {
    aws_access_key_id = ovh_cloud_project_user_s3_credential.harbor.access_key_id
    aws_secret_access_key = ovh_cloud_project_user_s3_credential.harbor.secret_access_key
  }
}
