variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "cluster_name" {
  description = "Name of the MSK cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where MSK will be deployed"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block of the VPC to allow traffic from"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for MSK brokers"
  type        = list(string)
}

variable "instance_type" {
  description = "The type of instance to use for the Kafka brokers"
  type        = string
  default     = "kafka.t3.small"
}

variable "eks_cluster_sg_id" {
  description = "Security Group ID of the EKS Cluster"
  type        = string
}

variable "number_of_broker_nodes" {
  description = "Number of broker nodes"
  type        = number
  default     = 2
}
