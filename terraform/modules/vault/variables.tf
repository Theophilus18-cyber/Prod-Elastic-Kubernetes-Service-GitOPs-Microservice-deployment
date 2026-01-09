variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Vault will be deployed"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID where Vault will be deployed"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for Vault"
  type        = string
  default     = "t3.micro"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC to allow internal access"
  type        = string
}

variable "key_name" {
  description = "SSH key name fo EC2"
  type        = string
  default     = "my-key" # Placeholder
}

output "vault_public_ip" {
  description = "Public IP of the Vault EC2 instance"
  value       = aws_instance.vault.public_ip
}


