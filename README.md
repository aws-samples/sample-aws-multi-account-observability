# Multi-Account Observability

[![AWS](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.9-blue.svg)](https://python.org)
[![CloudFormation](https://img.shields.io/badge/CloudFormation-Template-green.svg)](https://aws.amazon.com/cloudformation/)
[![Boto3](https://img.shields.io/badge/Boto3-1.42.0-yellow.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A comprehensive AWS multi-account analytics solution built on a hub-spoke architecture that centralizes cloud infrastructure data from distributed AWS accounts. Built with serverless architecture using AWS Lambda, Aurora PostgreSQL Serverless v2, and Amazon Quick Suite, it delivers unified visibility across cost optimization, security posture, compliance status, and operational metrics.

The solution implements an automated pub-sub data flow where spoke accounts publish daily data to the central hub via Lambda and Event Bridge. The hub processes incoming data streams through flexible compute options - either serverless Lambda functions for automatic scaling or EC2-based receivers for compliance-sensitive environments. This decoupled architecture enables seamless scaling across hundreds of AWS accounts while maintaining data sovereignty and security boundaries between organizational units.

## Table of Contents

- [Architecture of Multi Account Observability](#architecture-of-multi-account-observability)
- [Features](#features)
- [Cost](#cost)
- [Prerequisites](#prerequisites)
- [Regions](#regions)
- [Getting Started](#getting-started)
- [Security](#security)
- [License](#license)
- [Contact/Support](#contactsupport)


## Architecture of Multi Account Observability
> **📋 NOTE:** For detailed technical documnetation, see the [Deployment Guide](docs/deployment-guide.md).
<div align=center>
<img src="https://github.com/user-attachments/assets/1ab34c4e-d4c3-4c41-b053-3e0cbdd869e5" alt="View360 Analytics Architecture" width="700px">
</div>
<br/>

This Hub-Spoke architecture enables centralized multi-account observability with flexible processing options and comprehensive security controls.

**Hub (Analytics Account)**: Central aggregation point that receives, processes, and stores data from all spoke accounts. Contains Aurora PostgreSQL database, QuickSight dashboards, and receiver functions for data processing

**Spokes (Sender Accounts)**: Distributed AWS accounts that act as data publishers, each containing lightweight sender functions that collect 15+ data categories and publish encrypted payloads to the hub via S3 event notifications

### Process Flow

| Step | Process | Description | Location |
|------|---------|-------------|----------|
| **1** | EventBridge Trigger | Daily schedule triggers sender Lambda function at 01:00 | Sender Accounts |
| **2** | Data Upload | Sender Lambda uploads collected data to S3 data/ folder | Analytics Account S3 |
| **3** | Encryption | Data encrypted using KMS key | Analytics Account |
| **4** | S3 Event Notification | S3 PUT event triggers processing function | Analytics Account S3 |
| **5** | Processing Options | Choose between Serverless Processor (Lambda) or EC2 Receiver | Analytics Account |
| **6** | Secrets Access | Processing function accesses database credentials from Secrets Manager | Analytics Account |
| **7** | Database Write | Process JSON data and write to Aurora PostgreSQL Primary | Analytics VPC |
| **8** | Database Replication | Data replicated to Aurora Replica and Multi-AZ Standby | Analytics VPC |
| **9** | QuickSight Connection | QuickSight connects to Aurora via VPC endpoint | Analytics VPC |
| **10** | Dashboard Access | Users access dashboards and analytics through QuickSight | Analytics Account |

## Features

- **Multi-Account Analytics**: Aggregates data from multiple AWS accounts and regions with 15+ categories including AWS Cost Explorer, AWS Security Hub, Amazon GuardDuty, AWS Config, AWS Systems Manager, and AWS Support API.

- **Flexible Processing**: Choose serverless Lambda for auto-scaling or EC2 receivers for compliance requirements.

- **Ready-to-Use Dashboards**: 35+ database tables, 45+ pre-built views, and QuickSight integration with cost optimization and security monitoring dashboards.

### Data Category
The solution automatically collects comprehensive data across 15+ AWS service categories from each sender account, providing complete visibility into your cloud infrastructure.

| Category | AWS Service | Data Collected |
|----------|-------------|----------------|
| **Cost** | AWS Cost Explorer | Daily costs, forecasts, usage reports |
| **Security** | AWS Security Hub, Amazon GuardDuty, Amazon Inspector, AWS CloudTrail | Security findings, compliance status, threat detection, vulnerability assessments, API audit logs |
| **Configuration** | AWS Config | Resource compliance, configuration changes |
| **Inventory** | AWS Systems Manager | EC2 instances, patch compliance, inventory |
| **Support** | AWS Support API | Support cases, Trusted Advisor recommendations |
| **Trusted Advisor** | AWS Trusted Advisor | AWS recommendations and best practices |
| **Health** | AWS Health API | Service health events, maintenance notifications |
| **Web Security** | AWS WAF | Web application firewall rules |
| **Certificates** | AWS Certificate Manager | SSL/TLS certificates, expiration dates |
| **Encryption** | AWS KMS | Key usage, encryption status |
| **Secrets** | AWS Secrets Manager | Secret rotation, access patterns |

## Cost
Comprehensive annual cost estimates for the analytics account infrastructure, including all AWS services required for multi-account observability. Costs are based on moderate usage patterns and may vary significantly depending on data volume, number of connected accounts, query frequency, user activity, regional deployment, and specific configuration choices.

| Service | Option A (Serverless) | Option B (EC2) | Comments |
|---------|----------------------|----------------|---------------|
| Aurora PostgreSQL | $2,278 | $2,278 | Same database required for both options |
| Lambda Functions | $100 | $0 | Serverless uses Lambda for processing; EC2 option doesn't |
| EC2 Instance | $0 | $147 | EC2 option uses t4g.small instance for processing |
| VPC Endpoints | $0 | $350 | EC2 requires 4 interface endpoints for private connectivity |
| S3 Storage | $150 | $150 | Same storage requirements for both options |
| QuickSight | $1,176 | $1,176 | Same dashboard and user licensing costs |
| KMS | $16 | $16 | Same encryption requirements |
| CloudWatch | $25 | $25 | Same monitoring and logging needs |
| VPC/Networking | $50 | $50 | Same VPC infrastructure costs |
| Other Services | $12 | $12 | Same supporting services (SQS, Secrets Manager, etc.) |
| **TOTAL/YEAR** | **~$3,807** | **~$4,204** | EC2 option costs $397 more due to instance and endpoints |


>**⚠️ DISCLAIMER**
>
> Cost estimates are for informational purposes only (AWS pricing as of January 2025, US East region). Actual costs may vary based on usage patterns, regional differences, configuration choices, and AWS pricing changes.
> 
> **Recommendation**: Use the [AWS Pricing Calculator](https://calculator.aws) for official estimates and monitor costs with AWS Cost Explorer.
>
> *Estimates do not constitute a quote or commitment.*




## Prerequisites
You need access to an AWS Account. We recommend deployment of the Dashboards in a dedicated Data Collection Account, other than your Management (Payer) Account. We provide CloudFormation templates to build your Analytics Account(Hub) and the Sender Account

For all the Sender Accounts(Spokes), we provide the CloudFormation template to deploy the resources and permissions.

### AWS Services

The following Amazon Web Services must be enabled and accessible in your AWS account for the Multi-Account Observability solution to function properly:

| Required Services | Optional Services |
|-------------------|-------------------|
| AWS Security Token Service (STS) | Amazon Relational Database Service (RDS) |
| AWS Account Management | Amazon Simple Storage Service (S3) |
| AWS Cost Explorer | Elastic Load Balancing v2 |
| AWS Security Hub | AWS Resilience Hub |
| AWS Config | AWS Compute Optimizer |
| AWS Identity and Access Management (IAM) | AWS Support* |
| Amazon Elastic Compute Cloud (EC2) | AWS Trusted Advisor* |
| Amazon CloudWatch Application Signals | AWS Health* |
| AWS Systems Manager | |
| Amazon Inspector | |
| AWS Web Application Firewall (WAF) v2 | |

*Access requires a Business or Enterprise support plan. Without this plan, Health, Trusted Advisor and Support ticket data collection will be unavailable.

## Regions

Make sure you are installing data collection in the same region where you are going to use the data to avoid cross-region charges. Every sender account if used across multiple regiosn need to deploy the Sender Account Cloud Formation template in each region.

## Getting Started
Get your multi-account analytics solution up and running with these simple steps. The deployment process involves setting up the central analytics hub and connecting your AWS accounts as data sources.

> **ℹ️ Note:** For detailed step-by-step instructions, see the [Deployment Guide](docs/deployment-guide.md).


| Step | Description |
|------|-------------|
| **Clone Repository** | `git clone <repository-url>` |
| **Deploy Analytics Account** | Use CloudFormation template `A360-Analytics.yaml`<br>**Option A (Serverless)**: Lambda processing with automatic scaling<br>**Option B (EC2 Receiver)**: EC2-based processing for compliance |
| **Upload Files to S3** | Upload scripts and QuickSight templates to S3 bucket |
| **Setup Database** | Run SQL schema and views in Aurora Query Editor |
| **Deploy Sender Accounts** | Use CloudFormation template `A360-Sender.yaml` in each account |
| **Configure QuickSight** | Enable Enterprise Edition, create VPC connection, and import dashboards |


## Security

When you build systems on AWS infrastructure, security responsibilities are shared between you and AWS. This shared responsibility model reduces your operational burden because AWS operates, manages, and controls the components including the host operating system, the virtualization layer, and the physical security of the facilities in which the services operate. For more information about AWS security, visit [AWS Cloud Security](https://aws.amazon.com/security/).

See [CONTRIBUTING](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License permits use, modification, and distribution of this software for both commercial and non-commercial purposes, provided that the original copyright notice and license terms are included in all copies or substantial portions of the software.

## Contact/Support

### Getting Help
- **Documentation**: Check the [Deployment Guide](docs/deployment-guide.md) for detailed instructions
- **Issues**: Report bugs and request features via [GitHub Issues](../../issues)
- **Troubleshooting**: Review CloudWatch logs and verify IAM permissions

### Support Resources
- 📖 [Detailed Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- 🔧 [AWS API Documentation](docs/aws-api-documentation.md)
- 🔄 [Migration Guide v1.x to v2.x](migrations/00-v1.x-to-v2.x-migration/migration-guide.md)
- 📊 [SQL Helper Guide](sql/a360-sql-helper.md)
- `{}` [Data Format](docs/data_format.md)



