terraform {
  backend "s3" {
    bucket         = "prod-eks-gitops-terraform-state"
    key            = "gitops/prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "prod-eks-gitops-terraform-locks"
    encrypt        = true
  }
}
