# IAM roles for Kubernetes Service Accounts

# https://registry.terraform.io/modules/terraform-aws-modules/iam/aws/latest/submodules/iam-role-for-service-accounts-eks
# https://github.com/terraform-aws-modules/terraform-aws-iam/tree/v5.2.0/modules/iam-role-for-service-accounts-eks

module "irsa_eks_role_load_balancer" {
  source                                 = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  role_name                              = "IRSA-aws-load-balancer-controller"
  attach_load_balancer_controller_policy = true

  oidc_providers = {
    default = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
}

module "irsa_eks_role_ebs_csi" {
  source                = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  role_name             = "IRSA-aws-ebs-csi-driver"
  attach_ebs_csi_policy = true

  oidc_providers = {
    default = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}

# BinderHub ECR IAM role
# https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonelasticcontainerregistry.html
resource "aws_iam_policy" "binderhub-ecr" {
  name        = "binderhub-ecr-policy"
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
          # "ecr:ListImages",

          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:GetAuthorizationToken",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Effect   = "Allow"
        Resource = "*"
        # Resource= "arn:aws:ecr:region:111122223333:repository/repository-name"
      },
      {
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        Action = [
          "ecr:BatchDeleteImage",
          "ecr:DeleteLifecyclePolicy",
          "ecr:DeleteRepository",
          "ecr:GetLifecyclePolicy",
          "ecr:PutLifecyclePolicy",
        ]
        Effect   = "Allow"
        Resource = "*"
        # Resource= "arn:aws:ecr:region:111122223333:repository/repository-name"
      },
    ]
  })
}


module "irsa_eks_role_binderhub_ecr" {
  source    = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  role_name = "IRSA-aws-binderhub-ecr"

  oidc_providers = {
    default = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["binder:aws-binderhub-ecr"]
    }
  }

  role_policy_arns = {
    binderhub-ecr = aws_iam_policy.binderhub-ecr.arn
  }
}

