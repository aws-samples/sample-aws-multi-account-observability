# AWS Multi-Account Observability & Analytics
[![AWS](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![CloudFormation](https://img.shields.io/badge/CloudFormation-Template-green.svg)](https://aws.amazon.com/cloudformation/)
[![Boto3](https://img.shields.io/badge/Boto3-1.38.0-yellow.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## What is AWS Multi-Account Observability & Analytics?
A comprehensive AWS multi-account observability platform that aggregates, processes, and visualizes cloud infrastructure data across multiple AWS accounts. Built with serverless architecture using AWS Lambda, Aurora PostgreSQL Serverless v2, and designed for enterprise-scale monitoring with 15+ AWS service integrations, advanced security analytics, and cost optimization insights.

## Architecture

### Data Flow
```
[Sender Account] EventBridge -> Lambda -> S3 (Analytics Account) -> Lambda (Receiver) -> Aurora PostgreSQL
                                  │              │                         │
                                  ▼              ▼                         ▼
                               sender.py  data/{ACCOUNT_ID}/*.json    receiver.py
```

### Components
- **Sender Accounts**: Data collection via scheduled Lambda functions
- **Analytics Account**: Centralized data processing and storage
- **Aurora PostgreSQL**: Serverless v2 database for analytics
- **S3**: Encrypted data lake with KMS encryption
- **EventBridge**: Automated scheduling and triggering

## Project Structure

### Sender Accounts (Data Collection) 
- **Agency360-Sender.yml** → CloudFormation template for sender infrastructure
- **sender.py** → Data collection script (stored in S3, executed by Lambda)

### Flow
```
sample-aws-multi-account-observability/
├── cloudformation-template/
│   ├── Agency360-Analytics.yml    # Analytics account infrastructure
│   └── Agency360-Sender.yml       # Sender account infrastructure
├── scripts/
│   ├── receiver.py                # Data processing script
│   └── sender.py                  # Data collection script
├── sql/
│   ├── core-schema.sql            # Database schema
│   ├── core-view-schema.sql       # Analytics views
│   └── core-utility.sql           # Utility functions
├── requirements.txt               # Python dependencies
└── README.md
```

### Key Files
- **Agency360-Analytics.yml**: Complete infrastructure for analytics account
- **Agency360-Sender.yml**: Infrastructure template for sender accounts
- **receiver.py**: Processes JSON data from S3 and loads into Aurora
- **sender.py**: Collects AWS data and uploads to S3
- **core-schema.sql**: Complete database schema with 30+ tables and advanced analytics

## Features

### Data Collection & Processing
- **Multi-Account Support**: Aggregates data from unlimited AWS accounts with cross-account security
- **Comprehensive Coverage**: Collects 15+ data categories per account with deep service integration
- **Real-time Processing**: Lambda-based serverless data processing with 10GB memory and 15min timeout
- **Automated Lifecycle**: S3 files automatically moved to loaded/ folder after processing
- **Historical Data**: Support for backfill operations with custom date ranges
- **Performance Monitoring**: Processing time metrics and statistics for each data category
- **Error Handling**: Comprehensive error tracking with Dead Letter Queues and retry logic

### Data Categories (15+ AWS Services)
- **Account Management**: Account details, contact info, alternate contacts, partner/customer identification
- **Cost & Financial Analytics**: Current/previous period costs, forecasts, service costs, optimization opportunities
- **Service Usage**: Detailed AWS service utilization and costs by usage type across all regions
- **Comprehensive Security**: Security Hub findings, GuardDuty alerts, compliance status, vulnerability assessments
- **Security Services**: KMS keys, WAF rules (with compliance analysis), CloudTrail, Secrets Manager, ACM certificates
- **Configuration Management**: AWS Config compliance rules, non-compliant resources, remediation tracking
- **Infrastructure Inventory**: EC2 instances, applications, patches via Systems Manager with compliance status
- **Resource Management**: Multi-service inventory (EC2, RDS, S3, ELB, Auto Scaling, Lambda)
- **Optimization**: Compute Optimizer recommendations for EC2, EBS, Lambda cost and performance
- **Marketplace Analytics**: Third-party software usage, costs, and entitlements
- **Operational Intelligence**: Trusted Advisor recommendations, AWS Health events, best practices
- **Application Performance**: Application Signals metrics, traces, and performance monitoring
- **Disaster Recovery**: Resilience Hub assessments, compliance, and recovery planning
- **Processing & Audit**: Data processing status, error tracking, health scores, and operational logs

### Analytics & Visualization
- **33+ Database Tables**: Comprehensive schema covering all AWS observability aspects
- **41+ Optimized Views**: Pre-built analytics views with calculated KPIs and metrics
- **Executive Dashboards**: Summary views with health scores, cost trends, and security posture
- **Cost Optimization**: Advanced cost analysis with forecasting and savings opportunities
- **Security Analytics**: Multi-dimensional security monitoring with compliance tracking
- **Performance Insights**: Application and infrastructure performance with optimization recommendations
- **Compliance Management**: Comprehensive tracking of Config rules, security findings, and remediation
- **Multi-tenant Support**: Product-account relationships for complex organizational structures

## Technology Stack

- **Compute**: AWS Lambda (Python 3.13, 10GB Memory, 15min Timeout, Reserved Concurrency)
- **Database**: Amazon Aurora PostgreSQL Serverless v2 (0.5-16 ACU, Multi-AZ, Enhanced Monitoring)
- **Storage**: Amazon S3 with KMS encryption, versioning, and access logging
- **Infrastructure**: AWS CloudFormation with complete automation and validation
- **Networking**: VPC with private subnets, VPC endpoints, and Flow Logs
- **Security**: IAM roles with least privilege (15+ services), KMS encryption, Security Groups
- **Analytics**: QuickSight integration with VPC connectivity for secure dashboards
- **Scheduling**: EventBridge rules for automated data collection (daily at 1-2 AM)
- **Monitoring**: CloudWatch logs, Dead Letter Queues, and comprehensive error tracking
- **SDK**: Boto3 1.38.0+ with comprehensive AWS service integration (15+ services)
- **Multi-tenant**: Partner/customer identification for SaaS deployments

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.13+ (for local development)
- AWS account with the following services enabled:
  - Lambda, RDS Aurora, S3, EventBridge
  - IAM, VPC, CloudFormation, KMS
  - Security Hub, GuardDuty, Config (for security data)
  - Cost Explorer, Trusted Advisor (for cost data)
  - Systems Manager (for inventory data)

## Quick Start

#### *Click here for the Detailed [Deployment Guide](DEPLOYMENT_GUIDE.md) 

### 1. Deploy Analytics Infrastructure

**Option A: AWS Console (Recommended)**
1. Go to **CloudFormation > Create Stack** in AWS Console
2. Upload `cloudformation-template/Agency360-Analytics.yml`
3. Stack name: `a360-analytics`
4. **Parameters**:
   - `SenderAccounts`: Comma-separated account IDs (e.g., "123456789012,987654321098")
   - `CustomerName`: Customer identification (optional)
   - `PartnerName`: Partner identification (optional)
5. **Tags (Best Practice)**: Add tags like `Environment=prod`, `Project=a360`, `Owner=your-team`
6. Check **I acknowledge that AWS CloudFormation might create IAM resources**
7. Click **Create Stack**

**Option B: AWS CLI**
```bash
aws cloudformation create-stack \
  --stack-name a360-analytics \
  --template-body file://cloudformation-template/Agency360-Analytics.yml \
  --parameters ParameterKey=SenderAccounts,ParameterValue="123456789012,987654321098" \
  --tags Key=Environment,Value=prod Key=Project,Value=a360 Key=Owner,Value=your-team \
  --capabilities CAPABILITY_IAM
```

### 2. Upload Processing Scripts
```bash
# Get bucket name from stack outputs
BUCKET=$(aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' --output text)

# Upload scripts
aws s3 cp scripts/receiver.py s3://$BUCKET/scripts/receiver.py
aws s3 cp scripts/sender.py s3://$BUCKET/scripts/sender.py
```

### 3. Initialize Database Schema
Use Aurora Query Editor in the AWS Console:

1. Navigate to **RDS > Query Editor** in AWS Console
2. Select your Aurora cluster (created by the stack)
3. Connect using the **Secrets Manager** credentials
4. Execute the schema files in order:
   - Copy and paste contents of `sql/core-schema.sql`
   - Copy and paste contents of `sql/core-view-schema.sql`
   - Copy and paste contents of `sql/core-utility.sql` (if needed)

### 4. Deploy Sender Account (Optional)

**Option A: AWS Console (Recommended)**
1. Go to **CloudFormation > Create Stack** in sender account
2. Upload `cloudformation-template/Agency360-Sender.yml`
3. Stack name: `a360-sender`
4. **Parameters**:
   - `AnalyticsAccount`: Analytics account ID
   - `S3Bucket`: S3 bucket name from analytics account
   - `AnalyticsKMSKey`: KMS key ARN from analytics account
   - `CustomerName`: Customer identification (optional)
   - `PartnerName`: Partner identification (optional)
   - `Region`: AWS region (default: ap-southeast-1)
5. **Tags (Best Practice)**: Add tags like `Environment=prod`, `Project=a360`, `Owner=your-team`
6. Check **I acknowledge that AWS CloudFormation might create IAM resources**
7. Click **Create Stack**

**Option B: AWS CLI**
```bash
aws cloudformation create-stack \
  --stack-name a360-sender \
  --template-body file://cloudformation-template/Agency360-Sender.yml \
  --parameters ParameterKey=AnalyticsBucket,ParameterValue=$BUCKET \
  --tags Key=Environment,Value=prod Key=Project,Value=a360 Key=Owner,Value=your-team \
  --capabilities CAPABILITY_IAM
```

## Database Schema

### Core Tables (30+ tables)
**Account & Product Management**:
- **accounts**: AWS account information with partner/customer support
- **contact_info**: Account contact information
- **alternate_contacts**: Billing, operations, security contacts
- **products**: Product/project management
- **product_accounts**: Many-to-many account-product relationships

**Cost & Financial Analytics**:
- **cost_reports**: Period-based cost analysis with forecasting
- **service_costs**: Top service costs breakdown
- **cost_forecasts**: Future cost predictions with confidence intervals
- **services**: Detailed service usage and costs by usage type

**Comprehensive Security**:
- **security**: Security Hub findings summary by service
- **findings**: Detailed security findings with remediation
- **guard_duty_findings**: GuardDuty threat detection
- **kms_keys**: KMS key inventory and rotation status
- **waf_rules**: WAF configurations and compliance
- **waf_rules_detailed**: Detailed WAF rule compliance analysis
- **cloudtrail_logs**: CloudTrail logging status
- **secrets_manager_secrets**: Secrets inventory
- **certificates**: ACM certificate management
- **inspector_findings**: Inspector vulnerability findings

**Infrastructure & Optimization**:
- **inventory_instances**: EC2 instances via Systems Manager
- **inventory_applications**: Installed applications
- **inventory_patches**: Patch compliance status
- **service_resources**: Multi-service resource inventory
- **compute_optimizer**: EC2, EBS, Lambda optimization recommendations
- **config_reports**: Config compliance reports
- **non_compliant_resources**: Non-compliant resources tracking
- **config_inventory**: Configuration-based resource tracking

**Operations & Monitoring**:
- **marketplace_usage**: Marketplace product usage
- **trusted_advisor_checks**: Trusted Advisor recommendations
- **health_events**: AWS Health events
- **application_signals**: Application performance signals
- **resilience_hub_apps**: Resilience Hub assessments
- **logs**: Processing status and health scores
- **log_messages**: Detailed processing messagesiance reports
- **non_compliant_resources**: Non-compliant resources
- **inventory_instances**: EC2 instances via Systems Manager
- **inventory_applications**: Installed applications
- **inventory_patches**: Patch compliance status
- **marketplace_usage**: Marketplace product usage
- **trusted_advisor_checks**: Trusted Advisor recommendations
- **health_events**: AWS Health events
- **application_signals**: Application performance signals
- **resilience_hub_apps**: Resilience Hub assessments
- **logs**: Processing status and health scores
- **log_messages**: Detailed processing messages

## Configuration

### Environment Variables (Auto-configured by CloudFormation)
```bash
DB_NAME=core
AURORA_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
AURORA_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
REGION=ap-southeast-1
BUCKET=your-s3-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
```

### S3 Storage Structure
```
s3://ANALYTICS_ACCOUNT_BUCKET/
├── data/
│   └── {account-id}/
│       ├── 2025-01-15_DAILY.json
│       └── 2025-01-31_MONTHLY.json
├── loaded/
│   └── {account-id}/
│       └── processed-files...
└── scripts/
    ├── sender.py
    └── receiver.py
```

### Data Format
JSON data structure with comprehensive AWS service data:
```json
{
  "account": {
    "account_id": "123456789012",
    "account_name": "Production Account",
    "contact_info": {...},
    "alternate_contacts": {...}
  },
  "cost": {
    "current_period_cost": 1000.00,
    "previous_period_cost": 950.00,
    "top_services": [...],
    "forecast": [...]
  },
  "security": {
    "security_hub": [...],
    "guard_duty": [...],
    "kms": [...],
    "waf": [...],
    "cloudtrail": [...]
  },
  "service": [...],
  "inventory": {...},
  "config": {...},
  "marketplace": [...],
  "trusted_advisor": [...],
  "health": [...],
  "application": [...],
  "resilience_hub": [...],
  "logs": {...}
}
```


## Usage Examples

### Query Cost Trends
```sql
SELECT 
    a.account_name,
    cr.current_period_cost,
    cr.cost_difference_percentage,
    cr.period_start,
    cr.period_granularity
FROM cost_reports cr
JOIN accounts a ON cr.account_id = a.id
WHERE cr.period_granularity = 'MONTHLY'
ORDER BY cr.cost_difference_percentage DESC;
```

### Security Compliance Overview
```sql
SELECT 
    a.account_name,
    s.service,
    s.total_findings,
    s.critical_count,
    s.high_count,
    ROUND((s.resolved_findings::numeric / s.total_findings * 100), 2) as resolution_rate
FROM security s
JOIN accounts a ON s.account_id = a.id
WHERE s.critical_count > 0
ORDER BY s.critical_count DESC;
```

### Service Cost Analysis
```sql
SELECT 
    a.account_name,
    s.service,
    s.cost,
    s.currency,
    s.date_from,
    s.date_to
FROM services s
JOIN accounts a ON s.account_id = a.id
WHERE s.cost > 100
ORDER BY s.cost DESC;
```

### WAF Security Compliance
```sql
SELECT 
    a.account_name,
    wr.web_acl_name,
    COUNT(*) as total_rules,
    SUM(CASE WHEN wr.is_compliant THEN 1 ELSE 0 END) as compliant_rules,
    ROUND(SUM(CASE WHEN wr.is_compliant THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 2) as compliance_percentage
FROM waf_rules_detailed wr
JOIN accounts a ON wr.account_id = a.id
GROUP BY a.account_name, wr.web_acl_name
ORDER BY compliance_percentage ASC;
```

## Security Features

- **VPC Isolation**: Aurora database in private subnets only
- **KMS Encryption**: All data encrypted at rest and in transit
- **IAM Roles**: Least privilege access with constrained policies
- **VPC Endpoints**: Secure connectivity without internet access
- **Security Groups**: Network-level access controls
- **S3 Security**: Bucket policies, versioning, access logging
- **Dead Letter Queues**: Error handling and monitoring
- **CloudWatch Logs**: Comprehensive logging and monitoring
- **Secrets Manager**: Automatic password rotation for Aurora

## QuickSight Integration

The platform includes VPC connectivity for secure QuickSight integration:

### Setup QuickSight with VPC Connection

1. **Enable QuickSight Enterprise Edition**
   - Go to QuickSight console
   - Upgrade to Enterprise Edition if needed
   - Enable VPC connections

2. **Create VPC Connection**
   - In QuickSight, go to **Manage QuickSight > VPC connections**
   - Click **Add VPC connection**
   - Configure:
     - **VPC ID**: Use VPC created by the stack
     - **Subnet IDs**: Select private subnets from the stack
     - **Security Group**: Use QuickSight security group from stack outputs
     - **Availability Zones**: Select AZs matching your subnets

3. **Add Aurora as Data Source**
   - Go to **Datasets > New dataset**
   - Select **PostgreSQL**
   - Configure connection:
     - **Data source name**: `A360-Core`
     - **Database server**: Aurora endpoint from stack outputs
     - **Port**: `5432`
     - **Database**: `core`
     - **Username**: `postgres`
     - **Password**: Retrieve from Secrets Manager
     - **VPC connection**: Select the VPC connection created above

4. **Create Datasets and Dashboards**
   - Use the comprehensive database schema for analytics
   - Create datasets from key tables: `accounts`, `cost_reports`, `security`, `services`, `etc..`
   - Build dashboards for:
     - **Cost Analytics**: Track spending trends and forecasts
     - **Security Posture**: Monitor compliance and findings
     - **Inventory Management**: Track resources and patch compliance
     - **Performance Monitoring**: Application signals and health events

### Pre-built Analytics Views
The platform provides optimized views for common queries:
- Cost trends and forecasting
- Security compliance dashboards
- Service utilization reports
- Multi-account inventory tracking

## Monitoring & Troubleshooting

### Check Processing Status
```sql
SELECT 
    a.account_name,
    l.account_status,
    l.cost_status,
    l.security_status,
    l.config_status,
    l.date_created
FROM logs l
JOIN accounts a ON l.account_id = a.id
ORDER BY l.date_created DESC;
```

### View Error Messages
```sql
SELECT 
    a.account_name,
    lm.message,
    lm.message_type,
    lm.created_at
FROM log_messages lm
JOIN logs l ON lm.log_id = l.id
JOIN accounts a ON l.account_id = a.id
WHERE lm.message_type = 'ERROR'
ORDER BY lm.created_at DESC;
```

### Lambda Logs
```bash
# Receiver function logs
aws logs tail /aws/lambda/a360-analytics-Agency360ReceiverFunction-[RANDOM] --follow

# Sender function logs
aws logs tail /aws/lambda/a360-analytics-Agency360SenderFunction-[RANDOM] --follow
```

### Check Dead Letter Queue
```bash
# Get DLQ ARN from stack outputs
DLQ_ARN=$(aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs[?OutputKey==`DLQArn`].OutputValue' --output text)

# Get queue URL from ARN
DLQ_URL=$(aws sqs get-queue-url --queue-name $(echo $DLQ_ARN | cut -d':' -f6) --query 'QueueUrl' --output text)

# Check for failed messages
aws sqs receive-message --queue-url $DLQ_URL
```

### Stack Outputs Reference
```bash
# View all stack outputs
aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs'

# Get specific outputs
aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs[?OutputKey==`AuroraEndpoint`].OutputValue' --output text
aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' --output text
aws cloudformation describe-stacks --stack-name a360-analytics --query 'Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue' --output text
```

## Performance and Scaling

### Lambda Configuration
- **Memory**: 10GB for processing large datasets
- **Timeout**: 15 minutes for comprehensive data collection
- **Concurrency**: Reserved concurrency of 10 per function
- **Dead Letter Queue**: Error handling and retry logic

### Aurora Serverless v2
- **Auto-scaling**: 0.5 to 16 ACU based on workload
- **High Availability**: Multi-AZ deployment
- **Backup**: 7-day retention with point-in-time recovery
- **Encryption**: KMS encryption at rest

### Data Processing
- **Batch Processing**: Efficient upsert operations
- **Type Casting**: Automatic PostgreSQL type conversion
- **Error Handling**: Comprehensive logging and monitoring
- **File Management**: Automatic cleanup after processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with sample data
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review CloudWatch logs
- Verify IAM permissions
- Check Dead Letter Queue for failed messages
- Ensure all AWS services are properly configured

---

**Agency 360 Analytics** - Comprehensive AWS multi-account visibility and analytics platform
