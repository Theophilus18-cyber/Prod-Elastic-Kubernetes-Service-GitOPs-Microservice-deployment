output "vpc_id" {
  value = module.network.vpc_id
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "gh_ci_role_arn" {
  value = module.gh_ci_role.role_arn
}

output "gh_infra_role_arn" {
  value = module.gh_infra_role.role_arn
}

output "msk_bootstrap_brokers" {
  value = module.msk.bootstrap_brokers
}

output "msk_zookeeper_connect_string" {
  value = module.msk.zookeeper_connect_string
}
