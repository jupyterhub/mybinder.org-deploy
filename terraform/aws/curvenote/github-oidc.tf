# Allow GitHub workflows to access AWS using OIDC (no hardcoded credentials)
# https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

locals {
  create_github_roles = (var.enable_irsa || var.oidc_created) ? 1 : 0
}

data "aws_iam_openid_connect_provider" "github_oidc_provider" {
  count = local.create_github_roles
  url   = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_oidc_mybinderorgdeploy" {
  count = local.create_github_roles
  name  = "${var.cluster_name}-github-oidc-mybinderorgdeploy"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
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
              # TODO: Remove this, just for development:
              "repo:manics/mybinder.org-deploy:ref:refs/heads/aws-curvenote",
            ]
          }
        }
      }
    ]
  })

  inline_policy {
    name = "EKSDescribeCluster"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action   = ["eks:DescribeCluster"]
          Effect   = "Allow"
          Resource = "arn:aws:eks:${var.region}:${data.aws_caller_identity.current.account_id}:*"
        }
      ]
    })
  }
  permissions_boundary = local.permissions_boundary_arn
}
