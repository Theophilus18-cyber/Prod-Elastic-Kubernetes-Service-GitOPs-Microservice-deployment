

module "network" {
  source = "../../modules/network"

  vpc_cidr             = var.vpc_cidr
  vpc_name             = "${var.environment}-vpc"
  public_subnets_cidr  = var.public_subnets_cidr
  private_subnets_cidr = var.private_subnets_cidr
  availability_zones   = var.availability_zones
  cluster_name         = "${var.environment}-eks"
}

module "eks" {
  source = "../../modules/eks"

  cluster_name    = "${var.environment}-eks"
  subnet_ids      = module.network.private_subnet_ids
  node_group_min_size = var.node_group_min_size
  node_group_max_size = var.node_group_max_size
  node_group_desired_size = var.node_group_desired_size
  node_instance_types = var.node_instance_types
  vpc_cidr    = var.vpc_cidr
}

# Fetch the global OIDC provider (Must be created first)
# You can construct the ARN if you know the account ID, or use a data source if supported (not easy for OIDC).
# We will construct it assuming standard AWS partition.
data "aws_caller_identity" "current" {}

locals {
  oidc_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
}

# Role for GitHub Actions CI (Build & Push) - Locked to dev branch
module "gh_ci_role" {
  source            = "../../modules/github-oidc"
  environment       = var.environment
  github_repo       = "Theophilus18-cyber/Prod-Elastic-Kubernetes-Service-GitOPs-Microservice-deployment"
  github_branch     = "dev"
  role_type         = "ci"
  oidc_provider_arn = local.oidc_provider_arn
}

# Role for Terraform (Infra Management) - Locked to dev branch
module "gh_infra_role" {
  source            = "../../modules/github-oidc"
  environment       = var.environment
  github_repo       = "Theophilus18-cyber/Prod-Elastic-Kubernetes-Service-GitOPs-Microservice-deployment"
  github_branch     = "dev"
  role_type         = "terraform"
  oidc_provider_arn = local.oidc_provider_arn
}

module "vault" {
  source = "../../modules/vault"

  environment   = var.environment
  vpc_id        = module.network.vpc_id
  subnet_id     = module.network.private_subnet_ids[0] # Place in private subnet
  vpc_cidr      = var.vpc_cidr
  instance_type = "t3.small"
}

module "msk" {
  source = "../../modules/msk"

  environment            = var.environment
  cluster_name           = "${var.environment}-kafka"
  vpc_id                 = module.network.vpc_id
  vpc_cidr_block         = var.vpc_cidr
  subnet_ids             = module.network.private_subnet_ids
  number_of_broker_nodes = 2
  instance_type          = "kafka.t3.small"
  eks_cluster_sg_id      = module.eks.cluster_security_group_id
}

# NOTE: CloudFront requires the ALB DNS Name which is generated after the Ingress is deployed.
# You can uncomment this module after the Ingress is created and you have the ALB DNS.
# module "cloudfront" {
#   source = "../../modules/cloudfront"
#
#   alb_dns_name = "REPLACE_WITH_ALB_DNS_NAME"
#   tags         = {
#     Environment = var.environment
#   }
# }
