output "private_key_path" {
  value = "${path.module}/${var.environment}-vault-key.pem"
  description = "Path to the generated private key for SSH access"
}

output "vault_server_ip" {
  value = aws_instance.vault.public_ip
  description = "Public IP of the Vault server"
}
