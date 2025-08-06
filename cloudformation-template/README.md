# CloudFormation Templates

This folder contains the infrastructure-as-code templates for deploying the AWS Multi-Account Observability Platform.

## Templates Overview

### Agency360-Analytics.yml
**Purpose**: Deploys the complete analytics account infrastructure for centralized data processing and storage.

**Resources Created**:
- **Aurora PostgreSQL Serverless v2**: Database cluster with auto-scaling (0.5-16 ACU)
- **Lambda Functions**: Receiver and Sender functions with 10GB memory
- **S3 Bucket**: Encrypted data lake with KMS encryption and versioning
- **VPC Infrastructure**: Private subnets, security groups, and VPC endpoints
- **KMS Key**: Customer-managed encryption key with automatic rotation
- **IAM Roles**: Least-privilege policies for Lambda execution
- **EventBridge Rule**: Daily scheduling for data collection
- **Dead Letter Queue**: Error handling and monitoring
- **Secrets Manager**: Aurora credentials with automatic rotation

**Key Features**:
- Serverless architecture with auto-scaling
- Multi-AZ deployment for high availability
- Cross-account S3 access for sender accounts
- VPC endpoints for secure connectivity
- Comprehensive logging and monitoring

**Parameters**:
- `SenderAccounts`: Comma-separated list of AWS account IDs that can send data

### Agency360-Sender.yml
**Purpose**: Deploys sender account infrastructure for data collection from individual AWS accounts.

**Resources Created**:
- **Lambda Function**: Data collection function with comprehensive AWS service access
- **IAM Role**: Extensive permissions for AWS service data collection
- **EventBridge Rule**: Scheduled trigger for daily data collection
- **Dead Letter Queue**: Error handling for failed executions

**Key Features**:
- Comprehensive AWS service permissions (Cost Explorer, Security Hub, Config, etc.)
- Cross-account S3 write access to analytics bucket
- Scheduled execution with error handling
- KMS encryption for data in transit

**Parameters**:
- `AnalyticsBucket`: S3 bucket name from the analytics account

## Deployment Architecture

```
Analytics Account:
├── Aurora PostgreSQL (Private Subnets)
├── Lambda Functions (Receiver + Sender)
├── S3 Bucket (Encrypted Data Lake)
├── VPC with Private Subnets
└── KMS Key for Encryption

Sender Accounts:
├── Lambda Function (Data Collection)
├── EventBridge Rule (Daily Schedule)
└── Cross-Account S3 Access
```

## Security Features

**Network Security**:
- Aurora in private subnets only
- VPC endpoints for AWS services
- Security groups with minimal access
- No internet gateway required

**Data Security**:
- KMS encryption at rest and in transit
- S3 bucket policies with least privilege
- Secrets Manager for database credentials
- IAM roles with constrained permissions

**Monitoring**:
- CloudWatch logs for all functions
- Dead Letter Queues for error tracking
- VPC Flow Logs for network monitoring

## Deployment Instructions

### Template Validation (Required)
**Always validate templates before deployment:**
```bash
# Validate Analytics template
aws cloudformation validate-template --template-body file://Agency360-Analytics.yml

# Validate Sender template
aws cloudformation validate-template --template-body file://Agency360-Sender.yml
```

### Analytics Account

**Option A: AWS Console (Recommended)**
1. **Validate**: Ensure template validation passes (see above)
2. Go to **CloudFormation > Create Stack** in AWS Console
3. Upload `Agency360-Analytics.yml`
4. Stack name: `a360-analytics`
5. Parameters: Set `SenderAccounts` to your account IDs (comma-separated)
6. **Tags**: Add `Environment=prod`, `Project=a360`, `Owner=your-team`
7. Check **I acknowledge that AWS CloudFormation might create IAM resources**
8. Click **Create Stack**

**Option B: AWS CLI**
```bash
aws cloudformation create-stack \
  --stack-name a360-analytics \
  --template-body file://Agency360-Analytics.yml \
  --parameters ParameterKey=SenderAccounts,ParameterValue="123456789012,987654321098" \
  --tags Key=Environment,Value=prod Key=Project,Value=a360 Key=Owner,Value=your-team \
  --capabilities CAPABILITY_IAM
```

### Sender Account

**Option A: AWS Console (Recommended)**
1. **Validate**: Ensure template validation passes (see above)
2. Go to **CloudFormation > Create Stack** in sender account
3. Upload `Agency360-Sender.yml`
4. Stack name: `a360-sender`
5. Parameters: Set `AnalyticsBucket` to the S3 bucket from analytics account
6. **Tags**: Add `Environment=prod`, `Project=a360`, `Owner=your-team`
7. Check **I acknowledge that AWS CloudFormation might create IAM resources**
8. Click **Create Stack**

**Option B: AWS CLI**
```bash
aws cloudformation create-stack \
  --stack-name a360-sender \
  --template-body file://Agency360-Sender.yml \
  --parameters ParameterKey=AnalyticsBucket,ParameterValue=your-analytics-bucket \
  --tags Key=Environment,Value=prod Key=Project,Value=a360 Key=Owner,Value=your-team \
  --capabilities CAPABILITY_IAM
```

## Stack Outputs

### Analytics Stack Outputs
- `VPCId`: VPC ID for QuickSight connections
- `AuroraEndpoint`: Database connection endpoint
- `S3BucketName`: Analytics data bucket name
- `KMSKeyArn`: Encryption key ARN
- `QuickSightSecurityGroup`: Security group for QuickSight VPC connection

### Sender Stack Outputs
- `SenderLambdaFunctionArn`: Data collection function ARN
- `DLQArn`: Dead Letter Queue ARN for monitoring

## Cost Optimization

**Aurora Serverless v2**:
- Scales from 0.5 to 16 ACU based on workload
- Automatic pause/resume capabilities
- Pay only for actual usage

**Lambda**:
- Reserved concurrency limits costs
- Efficient memory allocation (10GB)
- Short execution times with optimized code

**S3**:
- Intelligent tiering for cost optimization
- Lifecycle policies for data archival
- Efficient data compression

## Monitoring and Troubleshooting

**CloudWatch Logs**:
- `/aws/lambda/[function-name]` for execution logs
- VPC Flow Logs for network troubleshooting

**Dead Letter Queues**:
- Monitor failed Lambda executions
- Automatic retry mechanisms

**Stack Events**:
- Monitor deployment progress
- Troubleshoot resource creation issues

## Best Practices

- **Use AWS Console**: Better visibility and error handling during deployment
- **Add Tags**: Essential for resource management and cost tracking
- **Monitor Events**: Watch stack events during deployment for issues
- **Verify Permissions**: Test cross-account access after deployment
- **Sample Data**: Test with sample data before production use