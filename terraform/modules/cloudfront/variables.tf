variable "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer (ALB)"
  type        = string
}

variable "comment" {
  description = "Comment for the CloudFront distribution"
  type        = string
  default     = "CloudFront Distribution for EKS"
}

variable "tags" {
  description = "Tags to apply to the distribution"
  type        = map(string)
  default     = {}
}
