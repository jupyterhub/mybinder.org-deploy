# Roles to allow access to EKS

# Allow GitHub workflows to access AWS using OIDC (no hardcoded credentials)
# https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

locals {
  create_github_roles = (var.enable_irsa || var.oidc_created) ? 1 : 0
}

data "aws_iam_openid_connect_provider" "github_oidc_provider" {
  count = local.create_github_roles
  url   = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_policy" "eks_access" {
  name        = "${var.cluster_name}-eks-access"
  description = "Kubernetes EKS access to ${var.cluster_name}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["eks:DescribeCluster"]
        Effect   = "Allow"
        Resource = module.eks.cluster_arn
      }
    ]
  })
}

resource "aws_iam_role" "github_oidc_mybinderorgdeploy" {
  count = local.create_github_roles
  name  = "${var.cluster_name}-${var.github_oidc_role_suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github_oidc_provider[0].arn
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = [
              # GitHub repositories and refs allowed to use this role
              "repo:jupyterhub/mybinder.org-deploy:ref:refs/heads/main",
            ]
          }
        }
      }
    ]
  })
  inline_policy {}
  managed_policy_arns = [
    aws_iam_policy.eks_access.arn,
  ]
  permissions_boundary = local.permissions_boundary_arn
}

resource "aws_iam_role" "github_oidc_mybinderorgdeploy_terraform" {
  count = local.create_github_roles
  name  = "${var.cluster_name}-${var.github_oidc_role_suffix}-terraform"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github_oidc_provider[0].arn
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = [
              # GitHub repositories and refs allowed to use this role
              "repo:jupyterhub/mybinder.org-deploy:ref:refs/heads/main",
              # Can't have branch and environment in the same condition
              # https://github.com/aws-actions/configure-aws-credentials/issues/746
              "repo:jupyterhub/mybinder.org-deploy:environment:aws-curvenote",
            ]
          }
        }
      }
    ]
  })
  inline_policy {}
  managed_policy_arns = [
    local.permissions_boundary_arn,
  ]
  permissions_boundary = local.permissions_boundary_arn
}

# IAM role that can be assumed by anyone in the AWS account (assuming they have sufficient permissions)
resource "aws_iam_role" "eks_access" {
  name = "${var.cluster_name}-eks-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
      }
    ]
  })
  inline_policy {}
  managed_policy_arns = [
    aws_iam_policy.eks_access.arn,
  ]
  permissions_boundary = local.permissions_boundary_arn
}
