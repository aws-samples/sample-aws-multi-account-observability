# CloudFormation Templates

This folder contains the infrastructure-as-code templates for deploying the AWS Multi-Account Observability Platform.

## Templates Overview

### Agency360-Analytics.yml
**Purpose**: Deploys the complete analytics account infrastructure for centralized data processing and storage.

**Resources Created**:
- **Aurora PostgreSQL Serverless v2**: Database cluster with auto-scaling (0.5-16 ACU)
- **Lambda Functions**: Receiver and Sender functions with 10GB memory, 15min timeout
- **S3 Bucket**: Encrypted data lake with KMS encryption, versioning, and access logging
- **VPC Infrastructure**: Private subnets, security groups, and VPC endpoints
- **KMS Key**: Customer-managed encryption key with automatic rotation
- **IAM Roles**: Comprehensive least-privilege policies for 15+ AWS services
- **EventBridge Rule**: Daily scheduling for data collection (2 AM)
- **Dead Letter Queue**: Error handling and monitoring with KMS encryption
- **Secrets Manager**: Aurora credentials with automatic rotation
- **VPC Flow Logs**: Network monitoring and security
- **QuickSight Integration**: VPC endpoint and security group for analytics

**Enhanced Security Features**:
- **Network Isolation**: Aurora in private subnets only
- **Encryption**: KMS encryption for all data at rest and in transit
- **Access Control**: Constrained S3 bucket policies with cross-account access
- **Monitoring**: VPC Flow Logs and comprehensive CloudWatch logging
- **Compliance**: Secure transport enforcement and public access blocking

**Lambda Configuration**:
- **Runtime**: Python 3.13
- **Memory**: 10GB for processing large datasets
- **Timeout**: 15 minutes for comprehensive data collection
- **Concurrency**: Reserved concurrency of 10 per function
- **Environment Variables**: Complete configuration for 15+ AWS services

**Parameters**:
- `SenderAccounts`: Comma-separated list of AWS account IDs that can send data
- `CustomerName`: Customer identification for multi-tenant environments
- `PartnerName`: Partner identification for business relationships

### Agency360-Sender.yml
**Purpose**: Deploys sender account infrastructure for data collection from individual AWS accounts.

**Resources Created**:
- **Lambda Function**: Data collection function with 15+ AWS service integrations
- **IAM Role**: Comprehensive permissions for extensive AWS service data collection
- **EventBridge Rule**: Scheduled trigger for daily data collection (1 AM)
- **Dead Letter Queue**: Error handling for failed executions with SQS encryption
- **KMS Key**: Dedicated encryption key for Lambda environment variables

**Comprehensive Service Permissions**:
- **Core Services**: Account, STS, Cost Explorer, Config, Security Hub
- **Security Services**: GuardDuty, IAM, KMS, WAF, CloudTrail, Secrets Manager, ACM, Inspector
- **Infrastructure**: EC2, RDS, S3, ELB, Auto Scaling, Lambda
- **Optimization**: Compute Optimizer for cost and performance recommendations
- **Monitoring**: Systems Manager, Application Signals, Resilience Hub, Health
- **Marketplace**: AWS Marketplace entitlements and usage
- **Support**: Trusted Advisor recommendations and checks

**Enhanced Security**:
- **Cross-Account Access**: Secure S3 access to analytics bucket with KMS encryption
- **Least Privilege**: Resource-constrained permissions where possible
- **Encryption**: KMS encryption for environment variables and data in transit
- **Regional Constraints**: WAF access limited to specific regions

**Lambda Configuration**:
- **Runtime**: Python 3.13
- **Memory**: 10GB for processing large datasets
- **Timeout**: 15 minutes for comprehensive data collection
- **Concurrency**: Reserved concurrency of 10
- **Environment Variables**: Complete configuration including customer/partner identification

**Parameters**:
- `AnalyticsAccount`: Analytics account ID for cross-account access
- `S3Bucket`: S3 bucket name from the analytics account
- `AnalyticsKMSKey`: KMS key ARN for data encryption
- `CustomerName`: Customer identification for multi-tenant environments
- `PartnerName`: Partner identification for business relationships
- `Region`: AWS region for deployment (default: ap-southeast-1)

## Deployment Architecture

```
Analytics Account:
├── Aurora PostgreSQL Serverless v2 (Private Subnets)
├── Lambda Functions (Receiver + Sender) - 10GB/15min
├── S3 Bucket (Encrypted Data Lake + Access Logs)
├── VPC with Private Subnets + Flow Logs
├── KMS Key for Encryption + Auto Rotation
├── QuickSight VPC Endpoint + Security Group
├── Dead Letter Queue (SQS) + KMS Encryption
└── Comprehensive IAM Policies (15+ Services)

Sender Accounts:
├── Lambda Function (15+ Service Data Collection)
├── EventBridge Rule (Daily 1 AM Schedule)
├── Cross-Account S3 Access (KMS Encrypted)
├── Dead Letter Queue (Error Handling)
├── KMS Key (Environment Variables)
└── Comprehensive Service Permissions
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
5. **Parameters**:
   - `SenderAccounts`: Comma-separated account IDs (e.g., "123456789012,987654321098")
   - `CustomerName`: Customer identification (optional)
   - `PartnerName`: Partner identification (optional)
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
5. **Parameters**:
   - `AnalyticsAccount`: Analytics account ID
   - `S3Bucket`: S3 bucket name from analytics account
   - `AnalyticsKMSKey`: KMS key ARN from analytics account
   - `CustomerName`: Customer identification (optional)
   - `PartnerName`: Partner identification (optional)
   - `Region`: AWS region (default: ap-southeast-1)
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
- `QuickSightVPCEndpointId`: QuickSight VPC endpoint ID
- `QuickSightSecurityGroup`: Security group for QuickSight VPC connection
- `AuroraClusterArn`: Aurora PostgreSQL cluster ARN
- `AuroraEndpoint`: Database connection endpoint
- `AuroraSecretArn`: Aurora master password secret ARN
- `S3BucketName`: Analytics data bucket name
- `KMSKeyArn`: Encryption key ARN
- `DLQArn`: Dead Letter Queue ARN for monitoring
- `ReceiverLambdaFunctionArn`: Data processing function ARN
- `SenderLambdaFunctionArn`: Data collection function ARN

### Sender Stack Outputs
- `LambdaFunctionArn`: Data collection function ARN
- `LambdaRoleArn`: Lambda execution role ARN
- `PolicyArn`: Custom IAM policy ARN

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