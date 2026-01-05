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
  node_instance_types = var.node_instance_types
}

module "vault" {
  source = "../../modules/vault"

  environment   = var.environment
  vpc_id        = module.network.vpc_id
  subnet_id     = module.network.private_subnet_ids[0]
  vpc_cidr      = var.vpc_cidr
  instance_type = "t3.medium" # Larger instance for prod
}
