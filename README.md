# Multi Account Observability
[![AWS](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![CloudFormation](https://img.shields.io/badge/CloudFormation-Template-green.svg)](https://aws.amazon.com/cloudformation/)
[![Boto3](https://img.shields.io/badge/Boto3-1.38.0-yellow.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A comprehensive AWS multi-account analytics platform that aggregates, processes, and visualizes cloud infrastructure data across multiple AWS accounts. Built with serverless architecture using AWS Lambda, Aurora PostgreSQL Serverless v2, and Amazon QuickSight.

## Setup
<!-- <div align="center"><img width="888" height="678" alt="View360-A360-LABELED-Option1-Only Lambda" src="https://github.com/user-attachments/assets/84bbe01e-cc6e-47ac-bac1-75c7cbc2f19c" /></div> -->

### 1. Data Collection (Sender Accounts)
<!-- ![Sender Accounts Flow](doc/files/img/view360-sender-flow.png) -->
<div><img width="888" height="335" alt="image" src="https://github.com/user-attachments/assets/60351665-32b0-4e0c-97e0-3ab245019f8a" /></div>

### 2. Data Processing (Analytics Account)
The Analytics account can be set up in 2 different methods that are described below. This can be selected upon running the CloudFormation template.

#### Option A: Serverless (Lambda Only)

##### Data Flow

<div><img width="888" height="335" alt="image" src="https://github.com/user-attachments/assets/59918bf1-51e9-4872-869f-0820caf954a8" /></div>

##### Architecture
<div><img width="888" height="678" alt="View360-A360-LABELED-Option1-Only Lambda" src="https://github.com/user-attachments/assets/e6c06b88-2b35-45c4-8a0e-64654e2855e9" /></div>

#### Option B: Lambda + EC2 + Systems Manager

##### Data Flow
<div><img width="888" height="335" alt="image" src="https://github.com/user-attachments/assets/579bdd53-d453-4a5a-8a15-59b2b3257e11" /></div>

##### Architecture
<div><img width="888" height="678" alt="View360-A360-LABELED-Option2-With EC2" src="https://github.com/user-attachments/assets/b966218a-429e-47bd-9c0a-22c5bc0bc643" /></div>

## File Description

### Analytics Account (Receiver)
- **A360-Analytics.yaml** → CloudFormation template for analytics infrastructure
- **A360-Analytics-Custom-VPC.yaml** → CloudFormation template with custom VPC
- **receiver.py** → Data processing script (stored in S3, executed by Lambda)
- **core-schema.sql** → Database schema for Aurora PostgreSQL
- **core-view.sql** → Analytics views for QuickSight integration

### Sender Accounts (Data Collection)
- **A360-Sender.yaml** → CloudFormation template for sender infrastructure
- **sender.py** → Data collection script (stored in S3, executed by Lambda)

### Flow
```
Sender Account: EventBridge → Lambda → S3 (sender.py) → Collect Data → Upload to Analytics S3
Analytics Account Option A: S3 Event → Lambda → S3 (receiver.py) → Process Data → Aurora → Move to loaded/
Analytics Account Option B: S3 Event → Lambda → EC2 → S3 (receiver.py) → Process Data → Aurora → Move to loaded/
```

## Features

### Data Collection & Processing
- **Multi-Account Support** : Aggregates data from multiple AWS accounts
- **Multi-Region Support**  : Track accounts across multiple AWS regions
- **Comprehensive Coverage**: Collects 15+ data categories per account
- **Real-time Processing**  : Lambda-based serverless data processing
- **Automated Lifecycle**   : S3 files automatically moved to loaded/ folder after processing
- **EC2 Receiver Option**   : Alternative to Lambda for compliance requirements

### Data Categories
- **Account Information**: Basic account details, contacts, and multi-region support
- **Cost Analysis**      : Spending patterns, forecasts, and optimization opportunities
- **Service Usage**      : Detailed AWS service utilization and costs
- **Security Posture**   : Security Hub findings, GuardDuty alerts, KMS, WAF, CloudTrail
- **Configuration**      : AWS Config compliance with enhanced metadata tracking
- **Inventory**          : EC2 instances with SSM Agent compliance monitoring
- **Support Tickets**    : AWS Support case tracking and resolution analytics
- **Marketplace**        : Third-party software usage and costs
- **Trusted Advisor**    : AWS recommendations and best practices
- **Health Events**      : Service health and maintenance notifications
- **Applications**       : Application performance signals and metrics
- **Resilience**         : Disaster recovery assessments and compliance
- **Audit Logs**         : Data processing status and error tracking

### Analytics & Visualization
- **35+ Database Tables**   : Comprehensive schema covering all AWS observability aspects
- **45+ Pre-built Views**   : Optimized database views for common queries
- **QuickSight Integration**: Ready-to-use dashboards and visualizations
- **Cost Optimization**     : Identify savings opportunities and spending trends
- **Security Monitoring**   : Track security findings and compliance status
- **Performance Insights**  : Application and infrastructure performance metrics

## Technology Stack

- **Compute**       : AWS Lambda (Python 3.13, 10GB Memory, 15min Timeout)
- **Compute (Alt)**  : EC2 + Systems Manager (t4g.micro ARM instance)
- **Database**      : Amazon Aurora PostgreSQL Serverless v2 (0.5-16 ACU)
- **Storage**       : Amazon S3 (KMS encryption, versioning)
- **Analytics**     : Amazon QuickSight
- **Infrastructure**: AWS CloudFormation
- **Networking**    : VPC with private subnets, VPC endpoints
- **Security**      : IAM roles, KMS encryption, Security Groups
- **SDK**           : Boto3 1.38.0+ for AWS service integration

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.13+ (for local development)
- Boto3 library for AWS SDK
- AWS account with the following services enabled:
  - Lambda, RDS Aurora, S3, QuickSight
  - IAM, VPC, CloudFormation, KMS
  - Security Hub, GuardDuty, Config (for security data)
  - Cost Explorer, Trusted Advisor (for cost data)
  - Systems Manager (for inventory data)
  - AWS Support (Business/Enterprise for support tickets)

## Quick Start

For detailed deployment instructions, see the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md).

### Deployment Options

**Option A: Serverless (Lambda Only)**
- Fully serverless architecture
- Lambda handles all data processing
- Automatic scaling and pay-per-use
- Recommended for most deployments

**Option B: EC2 + Systems Manager**
- EC2 instance for receiver processing
- Lambda triggers SSM Run Command
- Better for compliance requirements
- Predictable costs for high-frequency processing

### Deployment Sequence (8 Steps)

Both options follow the same 8-step sequence:

1. **Setup Analytics Account** - Deploy `A360-Analytics.yaml` CloudFormation template
2. **Setup S3 Folders** - Upload `scripts/` and `quicksuite/` folders to S3 bucket
3. **Setup Event Triggers** - Configure S3 and EventBridge triggers for receiver function
4. **Setup Database** - Run `core-schema.sql` and `core-view.sql` in Aurora Query Editor
5. **Configure QuickSight VPC** - Create VPC connection for QuickSight
6. **Setup QuickSight Data Source** - Connect QuickSight to Aurora database
7. **Migrate QuickSight Analysis** - Deploy `A360-QS-Migration.yaml` and run migration Lambda
8. **Deploy Sender Accounts** - Deploy `A360-Sender.yaml` in each account to monitor

See the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for detailed step-by-step instructions for each option.

## Database Schema

The complete database schema is defined in SQL files:

- **Tables**: `sql/schema/core-schema.sql` - 35+ tables for comprehensive data storage
- **Views**: `sql/schema/core-view.sql` - 45+ analytics views for QuickSight integration

Key table categories:
- Account & Product Management
- Cost & Financial Analytics
- Security & Compliance
- Configuration Management
- Infrastructure Inventory
- Support Tickets
- Operations & Monitoring

## Configuration

### Environment Variables

Environment variables are automatically configured by CloudFormation and differ by component:

**Receiver Function (Analytics Account)**
```bash
DB_NAME=core
AURORA_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
AURORA_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
REGION=ap-southeast-1
BUCKET=your-s3-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
```

**Sender Function (Sender Accounts)**
```bash
REGION=ap-southeast-1
BUCKET=analytics-account-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
CUSTOMER=customer-name
PARTNER=partner-name
CATEGORY=category-name
ENVIRONMENT=environment-type
PRODUCT=product-name
```

**QuickSight Migration Function (Analytics Account)**
```bash
REGION=ap-southeast-1
AURORA_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
AURORA_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
S3_BUCKET=your-s3-bucket-name
KMS_KEY_ARN=arn:aws:kms:region:account:key/key-id
```


### Data Format
Send JSON data to S3 with the following structure:
```json
{
  "account"   : { "account_id": "123456789012", "region": "ap-southeast-1", ... },
  "cost"      : { "current_period_cost": 1000.00, ... },
  "security"  : { "security_hub": [...], "guard_duty": [...], ... },
  "service"   : [...],
  "inventory" : { "instances": [...], ... },
  "config"    : { "compliance": [...], ... },
  "support_tickets": [...],
  ...
}
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

The platform includes pre-configured QuickSight assets:
- **Datasets**: Connected to Aurora views
- **Dashboards**: Cost, security, performance, and support visualizations
- **Analysis Templates**: Ready-to-use analytical reports
- **Migration Function**: Lambda function (`A360-QS-Migration.yaml`) that automates importing QuickSight templates from S3, creating datasets, and deploying pre-built analyses

Setup QuickSight:
1. Enable QuickSight Enterprise Edition
2. Create VPC connection to Aurora
3. Add Aurora as data source
4. Deploy QuickSight migration stack and execute Lambda to import templates
5. Access pre-built dashboards for cost, security, inventory, and support analytics

## Monitoring & Troubleshooting

### Lambda Logs
```bash
aws logs tail /aws/lambda/A360ReceiverFunction --follow
aws logs tail /aws/lambda/A360SenderFunction --follow
```

## EC2 Receiver Option

Version 2.x introduces EC2-based receiver as an alternative to Lambda:

### Benefits
- Full control over compute environment
- Easier debugging with direct SSH/SSM access
- Predictable costs for high-frequency processing
- Compliance-friendly for organizations with Lambda restrictions

### Deployment
- Automatically created by CloudFormation stack
- Instance Type: t4g.micro (ARM-based, cost-efficient)
- Scheduled: Cron job runs daily at 3 AM
- On-Demand: Lambda → SSM Run Command → EC2 execution

### Monitoring
```bash
# View logs on EC2
tail -f /var/log/receiver.log

# Check cron job
crontab -l -u ec2-user

# View SSM command history
aws ssm list-commands --filters Key=DocumentName,Values=AWS-RunShellScript
```

## Migration from v1.x to v2.x

If you're upgrading from v1.x (deployments before January 2026), see the [Migration Guide](migrations/00-v1.x-to-v2.x-migration/migration-guide.md) for detailed upgrade instructions.

v1.x refers to the original version deployed before January 2026, which lacked:
- Multi-region support
- Support ticket tracking
- Enhanced compliance features
- EC2 receiver option

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review CloudWatch logs
- Verify IAM permissions
- Check Dead Letter Queue for failed messages
- Ensure all AWS services are properly configured

## Additional Resources

- 📖 [Detailed Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- 🔧 [AWS API Documentation](docs/AWS_API_Documentation.md)
- 🔄 [Migration Guide v1.x to v2.x](migrations/00-v1.x-to-v2.x-migration/migration-guide.md)
- 📊 [SQL Helper Guide](sql/mao-sql-helper.md)

---

**View360 Analytics** - Comprehensive AWS multi-account visibility and analytics platform with multi-region support, enhanced compliance tracking, and support ticket integration.
