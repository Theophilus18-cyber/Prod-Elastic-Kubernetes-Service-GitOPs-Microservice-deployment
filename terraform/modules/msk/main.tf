resource "aws_security_group" "msk" {
  name_prefix = "${var.cluster_name}-msk-sg"
  vpc_id      = var.vpc_id
  description = "Security group for MSK cluster"

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "Allow Kafka interaction within VPC"
  }
  
  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "Allow Kafka TLS interaction within VPC"
  }

  ingress {
    from_port   = 2181
    to_port     = 2181
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "Allow Zookeeper interaction within VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-msk-sg"
  }
}

resource "aws_msk_cluster" "main" {
  cluster_name           = var.cluster_name
  kafka_version          = "3.5.1"
  number_of_broker_nodes = var.number_of_broker_nodes

  broker_node_group_info {
    instance_type   = var.instance_type
    client_subnets  = var.subnet_ids
    security_groups = [aws_security_group.msk.id]
    
    storage_info {
      ebs_storage_info {
        volume_size = 20
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "PLAINTEXT" # Simpler for internal microservices initally
      in_cluster    = true
    }
  }

  tags = {
    Environment = var.environment
  }
}
