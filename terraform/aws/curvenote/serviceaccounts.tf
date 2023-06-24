# IAM roles for Kubernetes Service Accounts

# https://registry.terraform.io/modules/terraform-aws-modules/iam/aws/latest/submodules/iam-role-for-service-accounts-eks
# https://github.com/terraform-aws-modules/terraform-aws-iam/tree/v5.2.0/modules/iam-role-for-service-accounts-eks

locals {
  create_irsa_roles     = (var.enable_irsa || var.oidc_created) ? 1 : 0
  eks_oidc_provider_arn = (local.create_irsa_roles == 1) ? data.aws_iam_openid_connect_provider.binderhub_eks_oidc_provider[0].arn : null
}

data "aws_iam_openid_connect_provider" "binderhub_eks_oidc_provider" {
  count = local.create_irsa_roles
  url   = module.eks.cluster_oidc_issuer_url
}

module "irsa_eks_role_load_balancer" {
  count                                  = local.create_irsa_roles
  source                                 = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version                                = "5.19.0"
  role_name                              = "${var.cluster_name}-IRSA-aws-load-balancer-controller"
  attach_load_balancer_controller_policy = true
  role_permissions_boundary_arn          = local.permissions_boundary_arn
  policy_name_prefix                     = "${var.cluster_name}-AmazonEKS_"

  oidc_providers = {
    default = {
      provider_arn               = local.eks_oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
}

module "irsa_eks_role_ebs_csi" {
  count                         = local.create_irsa_roles
  source                        = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version                       = "5.19.0"
  role_name                     = "${var.cluster_name}-IRSA-ebs-csi-controller-sa"
  attach_ebs_csi_policy         = true
  role_permissions_boundary_arn = local.permissions_boundary_arn
  policy_name_prefix            = "${var.cluster_name}-AmazonEKS_"

  oidc_providers = {
    default = {
      provider_arn               = local.eks_oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}

# BinderHub ECR IAM role
# https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistry.html
resource "aws_iam_policy" "binderhub-ecr" {
  name        = "${var.cluster_name}-ecr-policy"
  path        = "/"
  description = "BinderHub ECR create/read/write"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:CreateRepository",
          "ecr:DescribeImages",
          "ecr:DescribeRepositories",

          "ecr:ListImages",

          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:GetAuthorizationToken",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",

          "ecr:BatchDeleteImage",
          "ecr:DeleteLifecyclePolicy",
          "ecr:DeleteRepository",
          "ecr:GetLifecyclePolicy",
          "ecr:PutLifecyclePolicy",
        ]
        Effect   = "Allow"
        Resource = "arn:aws:ecr:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Action = [
          "ecr:GetAuthorizationToken",
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}


module "irsa_eks_role_binderhub_ecr" {
  count                         = local.create_irsa_roles
  source                        = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version                       = "5.19.0"
  role_name                     = "${var.cluster_name}-IRSA-aws-binderhub-ecr"
  role_permissions_boundary_arn = local.permissions_boundary_arn
  policy_name_prefix            = "${var.cluster_name}-AmazonEKS_"

  oidc_providers = {
    default = {
      provider_arn               = local.eks_oidc_provider_arn
      namespace_service_accounts = ["aws-curvenote:binderhub-container-registry-helper"]
    }
  }

  role_policy_arns = {
    binderhub-ecr = aws_iam_policy.binderhub-ecr.arn
  }
}
