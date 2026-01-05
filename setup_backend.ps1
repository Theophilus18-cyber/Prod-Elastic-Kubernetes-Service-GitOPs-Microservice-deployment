$bucketName = "prod-eks-gitops-terraform-state"
$tableName = "prod-eks-gitops-terraform-locks"
$region = "us-east-1"

Write-Host "Creating S3 Bucket: $bucketName..."
aws s3api create-bucket --bucket $bucketName --region $region
aws s3api put-bucket-versioning --bucket $bucketName --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket $bucketName --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

Write-Host "Creating DynamoDB Table: $tableName..."
aws dynamodb create-table `
    --table-name $tableName `
    --attribute-definitions AttributeName=LockID,AttributeType=S `
    --key-schema AttributeName=LockID,KeyType=HASH `
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 `
    --region $region

Write-Host "Backend resources created successfully."
