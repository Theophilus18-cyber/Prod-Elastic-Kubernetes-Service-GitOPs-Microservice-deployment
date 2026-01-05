variable "services" {
  description = "List of service names to create ECR repositories for"
  type        = set(string)
  default     = ["frontend", "orders", "payments", "delivery", "notifications"]
}

resource "aws_ecr_repository" "service" {
  for_each             = var.services
  name                 = "${var.environment}-${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "repository_urls" {
  value = { for k, v in aws_ecr_repository.service : k => v.repository_url }
}
