# Agency 360 Analytics
[![AWS](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![CloudFormation](https://img.shields.io/badge/CloudFormation-Template-green.svg)](https://aws.amazon.com/cloudformation/)
[![Boto3](https://img.shields.io/badge/Boto3-1.35.0-yellow.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A comprehensive AWS multi-account analytics platform that aggregates, processes, and visualizes cloud infrastructure data across multiple AWS accounts. Built with serverless architecture using AWS Lambda, Aurora PostgreSQL, and Amazon QuickSight.

## Architecture
![Agency 360 Architecture](doc/files/img/agency360-architecture.png)

### 1. Data Collection (Sender Accounts)
![Sender Accounts Flow](doc/files/img/agency360-sender-flow.png)

### 2. Data Processing (Analytics Account)
![Analytics Accounts Flow](doc/files/img/agency360-analytics-flow.png)

### Complete Flow
```
[Sender Account] EventBridge -> Lambda -> S3 (Analytics Account) ----------> Lambda (Receiver) -> Aurora -> QuickSight
                                  │              │                                  │
                                  ▼              ▼                                  ▼
                               sender.py  data/SENDER_ACCOUNT/*.json            receiver.py
```

## File Description

### Analytics Account (Receiver)
- **Agency360-Analytics.yml** → CloudFormation template for analytics infrastructure
- **receiver.py** → Data processing script (stored in S3, executed by Lambda)
- **core-schema.sql** → Database schema for Aurora PostgreSQL
- **core-view-schema.sql** → Analytics views for QuickSight integration

### Sender Accounts (Data Collection) (https://github.com/ruvigh/agency-360-sender/)
- **Agency360-Sender.yml** → CloudFormation template for sender infrastructure
- **sender.py** → Data collection script (stored in S3, executed by Lambda)

### Flow
```
Sender Account: EventBridge → Lambda (lambda.py) → S3 (sender.py) → Collect Data → Upload to Analytics S3
Analytics Account: S3 Event → Lambda → S3 (receiver.py) → Process Data → Aurora → Delete Files
```

## Features

### Data Collection & Processing
- **Multi-Account Support** : Aggregates data from multiple AWS accounts
- **Comprehensive Coverage**: Collects 12+ data categories per account
- **Real-time Processing**  : Lambda-based serverless data processing
- **Automated Cleanup**     : S3 files automatically deleted after processing

### Data Categories
- **Account Information**: Basic account details and contact info
- **Cost Analysis**      : Spending patterns, forecasts, and optimization opportunities
- **Service Usage**      : Detailed AWS service utilization and costs
- **Security Posture**   : Security Hub findings, GuardDuty alerts, compliance status
- **Configuration**      : AWS Config compliance and resource configurations
- **Inventory**          : EC2 instances, applications, and patch management
- **Marketplace**        : Third-party software usage and costs
- **Trusted Advisor**    : AWS recommendations and best practices
- **Health Events**      : Service health and maintenance notifications
- **Applications**       : Application performance signals and metrics
- **Resilience**         : Disaster recovery assessments and compliance
- **Audit Logs**         : Data processing status and error tracking

### Analytics & Visualization
- **14 Pre-built Views**    : Optimized database views for common queries
- **QuickSight Integration**: Ready-to-use dashboards and visualizations
- **Cost Optimization**     : Identify savings opportunities and spending trends
- **Security Monitoring**   : Track security findings and compliance status
- **Performance Insights**  : Application and infrastructure performance metrics

## Technology Stack

- **Compute**       : AWS Lambda (Python 3.13, 10GB Memory, 15min Timeout)
- **Database**      : Amazon Aurora PostgreSQL Serverless v2
- **Storage**       : Amazon S3
- **Analytics**     : Amazon QuickSight
- **Infrastructure**: AWS CloudFormation
- **Networking**    : VPC with public/private subnets
- **Security**      : IAM roles, KMS encryption, VPC endpoints
- **SDK**           : Boto3 for AWS service integration

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.13+ (for local development)
- Boto3 library for AWS SDK
- AWS account with the following services enabled:
  - Lambda, RDS Aurora, S3, QuickSight
  - IAM, VPC, CloudFormation

## Quick Start

### 1. Deploy Infrastructure
```bash
aws cloudformation create-stack \
  --stack-name agency360-analytics \
  --template-body file://Agency360-Analytics.yml \
  --parameters ParameterKey=S3BucketName,ParameterValue=your-bucket-name \
               ParameterKey=SenderAccounts,ParameterValue="123456789012,987654321098" \
  --capabilities CAPABILITY_IAM
```

### 2. Upload Processing Script
```bash
aws s3 cp receiver.py s3://your-bucket-name/scripts/receiver.py
```

### 3. Initialize Database Schema
```bash
# Connect to Aurora cluster and run:
psql -h your-aurora-endpoint -U postgres -d core -f sql/core-schema.sql
psql -h your-aurora-endpoint -U postgres -d core -f sql/core-view-schema.sql
```

### 4. Test with Sample Data
```bash
aws s3 cp sample.json s3://your-bucket-name/data/sample.json
aws lambda invoke --function-name agency360-receiver response.json
```

## Database Schema

### Core Tables
- **accounts**            : AWS account information and contacts
- **services**            : Service usage and costs
- **cost_reports**        : Cost analysis and forecasts
- **security**            : Security findings and compliance
- **inventory_instances** : EC2 instances and applications
- **logs**                : Processing status and audit trail

### Analytics Views
- `view_acct_serv`    : Account-service cost analysis
- `view_acct_security`: Security posture overview
- `view_summary`      : Comprehensive account dashboard
- `view_acct_products`: Product-account relationships
- more..

## Configuration

### Environment Variables
```bash
DB_NAME=core
AURORA_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
AURORA_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
REGION=ap-southeast-1
BUCKET=your-s3-bucket-name
```
### S3 Storage Structure
```
s3://ANALYTICS_ACCOUNT_BUCKET/
├── data/
│   └── {account-id}/
│       ├── 2025-01-15_DAILY.json
│       └── 2025-01-31_MONTHLY.json
└── scripts/
    └── sender.py
    └── receiver.py.py
```
### Data Format
Send JSON data to S3 with the following structure:
```json
{
  "account"   : { "account_id": "123456789012", ... },
  "cost"      : { "current_period_cost": 1000.00, ... },
  "security"  : { "security_hub": [...], ... },
  "service"   : [...],
  "inventory" : { "instances": [...], ... }
  ...
}
```
... and more


## Usage Examples

### Query Cost Trends
```sql
SELECT account_name, current_period_cost, cost_difference_percentage
FROM view_acct_cost_rep
WHERE period_granularity = 'MONTHLY'
ORDER BY cost_difference_percentage DESC;
```

### Security Compliance Overview
```sql
SELECT account_name, service, total_findings, critical_count, resolution_rate
FROM view_acct_security
WHERE critical_count > 0
ORDER BY critical_count DESC;
```

### Service Cost Analysis
```sql
SELECT account_name, service_name, cost, cost_report_name
FROM view_acct_serv_cost
WHERE cost > 100
ORDER BY cost DESC;
```

## Security Features

- **VPC Isolation**: Database in private subnets
- **Encryption**: KMS encryption for data at rest
- **IAM Roles**: Least privilege access principles
- **VPC Endpoints**: Secure S3 and QuickSight connectivity
- **Security Groups**: Network-level access controls

## QuickSight Integration

The platform includes pre-configured QuickSight assets:
- **Datasets**: Connected to Aurora views
- **Dashboards**: Cost, security, and performance visualizations
- **Analysis Templates**: Ready-to-use analytical reports

Import QuickSight assets:
```bash
cd quicksight
./import.sh
```

## Monitoring & Troubleshooting

### Check Processing Status
```sql
SELECT account_name, latest_account_status, latest_cost_status, 
       latest_security_status, health_score
FROM view_acct_logs
ORDER BY health_score ASC;
```

### View Error Messages
```sql
SELECT account_name, message, message_type, log_date
FROM view_acct_log_messages
WHERE message_type = 'ERROR'
ORDER BY log_date DESC;
```

### Lambda Logs
```bash
aws logs tail /aws/lambda/agency360-receiver --follow
```

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
- Ensure all AWS services are properly configured

---

**Agency 360 Analytics** - Comprehensive AWS multi-account visibility and analytics platform