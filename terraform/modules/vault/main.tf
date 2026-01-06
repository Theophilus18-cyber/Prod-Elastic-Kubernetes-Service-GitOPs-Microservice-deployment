resource "aws_security_group" "vault" {
  name        = "${var.environment}-vault-sg"
  description = "Security group for Vault EC2 instance"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr] # Allow access from within VPC
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Open to world, restrict this in production!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Generate SSH Key Pair for Vault
resource "tls_private_key" "vault" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "vault" {
  key_name   = "${var.environment}-vault-key"
  public_key = tls_private_key.vault.public_key_openssh
}

resource "local_file" "private_key" {
  content  = tls_private_key.vault.private_key_pem
  filename = "${path.module}/${var.environment}-vault-key.pem"
}

resource "aws_instance" "vault" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = aws_key_pair.vault.key_name

  vpc_security_group_ids = [aws_security_group.vault.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo yum install -y yum-utils
              sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/AmazonLinux/hashicorp.repo
              sudo yum -y install vault
              # Basic Vault dev server config (Do NOT use for production securely)
              cat <<EOT > /etc/vault.d/vault.hcl
              ui = true
              disable_mlock = true
              storage "file" {
                path = "/opt/vault/data"
              }
              listener "tcp" {
                address     = "0.0.0.0:8200"
                tls_disable = 1
              }
              api_addr = "http://127.0.0.1:8200"
              cluster_addr = "https://127.0.0.1:8201"
              EOT
              sudo systemctl enable vault
              sudo systemctl start vault
              EOF

  tags = {
    Name = "${var.environment}-vault-server"
  }
}
