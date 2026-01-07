output "vpc_id" {
  value = module.network.vpc_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "msk_bootstrap_brokers" {
  value = module.msk.bootstrap_brokers
}

output "msk_zookeeper_connect_string" {
  value = module.msk.zookeeper_connect_string
}
