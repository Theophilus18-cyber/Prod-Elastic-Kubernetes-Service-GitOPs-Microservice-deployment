variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (org/repo)"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to link to this role (e.g., main, dev, staging)"
  type        = string
}

variable "role_type" {
  description = "Type of role to create: 'ci' (Docker/ECR) or 'terraform' (Infra Admin)"
  type        = string
  validation {
    condition     = contains(["ci", "terraform"], var.role_type)
    error_message = "Role type must be either 'ci' or 'terraform'."
  }
}

variable "oidc_provider_arn" {
  description = "ARN of the existing GitHub OIDC Provider"
  type        = string
}
