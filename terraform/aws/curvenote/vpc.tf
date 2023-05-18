# data "aws_availability_zones" "available" {}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "4.0.2"

  name = var.cluster_name
  cidr = "10.0.0.0/16"
  # azs                  = data.aws_availability_zones.available.names[:1]
  # EKS requires at least two AZ (though node groups can be placed in just one)
  azs            = ["${var.region}b", "${var.region}c"]
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  # private_subnets      = ["10.0.4.0/24", "10.0.5.0/24"]
  enable_nat_gateway   = false
  single_nat_gateway   = true
  enable_dns_hostnames = true

  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }

  # private_subnet_tags = {
  #   "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  #   "kubernetes.io/role/internal-elb"           = "1"
  # }
}
