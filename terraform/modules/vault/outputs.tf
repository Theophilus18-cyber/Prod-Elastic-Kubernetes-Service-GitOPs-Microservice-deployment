output "vault_private_ip" {
  value = aws_instance.vault.private_ip
}

output "vault_public_ip" {
  value = aws_instance.vault.public_ip
}
