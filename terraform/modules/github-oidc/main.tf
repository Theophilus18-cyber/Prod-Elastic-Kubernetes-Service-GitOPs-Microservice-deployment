resource "aws_iam_role" "this" {
  name = "${var.environment}-github-${var.role_type}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" : "repo:${var.github_repo}:ref:refs/heads/${var.github_branch}"
          }
        }
      },
    ]
  })
}

# -------------------------------------------------------------------------------------------------
# CI Role Policies (ECR Push Only)
# -------------------------------------------------------------------------------------------------
resource "aws_iam_role_policy" "ci_ecr_push" {
  count = var.role_type == "ci" ? 1 : 0
  name  = "${var.environment}-ci-ecr-push-policy"
  role  = aws_iam_role.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "GetAuthorizationToken"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "AllowPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart"
        ]
        Resource = "arn:aws:ecr:*:*:repository/${var.environment}-*"
      }
    ]
  })
}

# -------------------------------------------------------------------------------------------------
# Terraform Role Policies (Admin / Infra)
# -------------------------------------------------------------------------------------------------
# NOTE: For a real prod environment, you'd restrict this further. 
# For now, we give AdministratorAccess to Terraform but ONLY from the protected branch.
resource "aws_iam_role_policy_attachment" "terraform_admin" {
  count      = var.role_type == "terraform" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  role       = aws_iam_role.this.name
}

# EKS Access for Terraform (to update auth config map if needed)
resource "aws_iam_role_policy_attachment" "terraform_eks" {
  count      = var.role_type == "terraform" ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.this.name
}
