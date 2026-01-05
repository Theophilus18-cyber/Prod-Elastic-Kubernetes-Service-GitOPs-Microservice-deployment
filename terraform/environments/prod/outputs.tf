output "vpc_id" {
  value = module.network.vpc_id
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "vault_private_ip" {
  value = module.vault.vault_private_ip
}
