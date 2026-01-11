# Multi-Account Observability (MAO) - Deployment Guide

This is a comprehensive deployment guide for Multi-Account Observability within AWS.

## Deployment Options

View360 Analytics offers **two deployment options** for the receiver component:

### **OPTION A: Serverless (Lambda Only)** ⚡
**Recommended for most deployments**

**What it is:**
- Fully serverless architecture
- Lambda handles all data processing automatically
- S3 events trigger Lambda → processes data → writes to Aurora

**Benefits:**
- ✅ Automatic scaling
- ✅ Pay-per-use pricing
- ✅ Zero infrastructure management
- ✅ Built-in high availability

**Use when:**
- Standard AWS deployments
- Variable/unpredictable workloads
- Want minimal operational overhead

**Deploy:** Use `cloudformation/A360-Analytics.yaml`

---

### **OPTION B: EC2 + Systems Manager** 🖥️
**For compliance or control requirements**

**What it is:**
- EC2 instance (t4g.micro ARM) runs receiver script
- Lambda triggers SSM Run Command → EC2 processes data
- Scheduled cron job runs daily at 3 AM

**Benefits:**
- ✅ Full control over compute environment
- ✅ Direct SSH/SSM access for debugging
- ✅ Predictable costs for high-frequency processing
- ✅ Compliance-friendly (no Lambda restrictions)

**Use when:**
- Organization has Lambda restrictions
- Need direct server access for troubleshooting
- High-frequency processing with predictable costs
- Compliance requires traditional compute

**Deploy:** Use `cloudformation/A360-Analytics-Custom-VPC.yaml`

---

## Introduction & Architecture

### Architecture Design
**Standardized multi-account data flow**

| Steps | Description |
|-------|-------------|
| 1 | EventBridge triggers the Sender function. Sender retrieves its function files from S3 bucket. Sender retrieves account data. Data is encrypted using KMS key. Encrypted data is transmitted to S3 |
| 2 | S3 event notification triggers Receiver Lambda function. Receiver retrieves its function files from S3 bucket. Receiver Lambda retrieves encrypted content from S3 |
| 3 | Receiver Lambda accesses KMS. Encrypted data is decrypted using KMS key |
| 4 | Receiver Lambda retrieves database credentials from Secrets Manager. Authentication details are validated |
| 5 | Decrypted data is processed. Aurora database is updated with new data |
| 6 | Data is now available in Aurora database. QuickSight can access and query the data for visualization |

## Pre-requisites

1. Download the multi-account-observability folder as a zip from the repository
2. Extract all files and place them in a folder of your choice
3. Check that you have all the required files:
   - `cloudformation/` folder with CloudFormation templates
   - `scripts/` folder with Python scripts
   - `sql/` folder with database schemas
   - `quicksuite/` folder with QuickSight templates
   - `examples/` folder with sample data
4. Ensure you have appropriate AWS permissions to create the required resources

## Configuration Steps

Below is the series of steps that you should follow in a sequential format to ensure proper deployment of this solution.

### SEQ 1: Setup Analytics Account

1. Open CloudFormation in AWS (the account you wish to be the Analytics account)
   - Create stack
   - Choose an existing template
   - Upload the template file

2. Browse and upload the file `MAO-Analytics.yaml` which can be found within the `cloudformation/` folder

3. Once the S3 URL is generated, click on "View in Infrastructure Composer" and validate the template. This is recommended practice.

4. Click Next

5. There will be a requirement to set 7 parameters:

    | Optional / Mandatory | Parameter | Description |
    |----------|-----------|-------------|
    | Optional | Category | Classify whether the account is facing the Internet, Intranet or Both |
    | Optional | CustomerName | Customer name for the account (spare field) |
    | Optional | Environment | Environment type for the account |
    | Optional | PartnerName | Partner name for the account (vendor name) |
    | Optional | ProductName | Name of the Product/Workload/Application running in this account |
    | Mandatory | S3BucketName | Name of the S3 bucket to create (only lowercase letters, NO CAPS). Ensure that the bucket name is unique |
    | Mandatory | SenderAccounts | List of AWS Account IDs that can send data (comma-separated) |

6. Click Next and on the next screen under tags, give it a tag for good account hygiene.

7. Click Next and proceed to create the CloudFormation template.

8. Upon "CREATE_COMPLETE" navigate to the Outputs Tab and note the information inside.

9. The information within the Outputs Tab is the key for all subsequent steps

10. Analytics Account is now created

### SEQ 2: Setup Folders within the S3

1. There will be 2 new S3 buckets created:
   - `{bucket-name}-data`
   - `{bucket-name}-logs`

2. Open the newly created S3 Bucket (`{bucket-name}-data`)

3. Upload the following folders with all content inside from the multi-account-observability/ folder into this S3 bucket at the root:
   - `scripts/`
   - `quicksuite/`

### SEQ 3: Setting Up Event Triggers in the Analytics Account

#### Set the S3 Bucket Event Trigger
1. Navigate to the Analytics Account
2. Open Lambda and search for the Receiver function (MAO-receiver-function)
3. Click on "Add Trigger"
4. Use the information below to update the form field for the Trigger Configuration:

    | Field | Description |
    |-------|-------------|
    | Select a Source | S3 |
    | Bucket | Choose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | Event types | All object create events |
    | Prefix – optional | data/ |
    | Suffix – optional | .json |

5. Click Add

#### Set the EventBridge Trigger
1. Navigate to the Analytics Account
2. Open Lambda and search for the Receiver function (MAO-receiver-function)
3. Click on "Add Trigger"
4. Use the information below to update the form field for the Trigger Configuration:

    | Field | Description |
    |-------|-------------|
    | Select a Source | EventBridge (CloudWatch Events) |
    | Rule | Create a new rule |
    | Rule name | Give it a name of your choice |
    | Rule description | Give it a description of your choice |
    | Rule type | Schedule expression |
    | Schedule expression | rate(24 hours) - this lambda is triggered every 24 hours |

5. Click Add

### SEQ 4: Setup Database

1. Open Aurora and RDS and navigate to the newly created cluster
2. Open the newly created cluster (aurora-db-cluster)
3. Click on "Query Editor"
4. Use the information below to update the form field for "Connect to database":

    | Parameter | Description |
    |-----------|-------------|
    | Database instance or cluster | Choose the newly created Database instance or cluster |
    | Database Username | Connect with a Secrets Manager ARN |
    | Secrets manager ARN | Get the ARN of the Newly Created Secret from the Output Tab inside the Analytics CloudFormation Stack |
    | Enter the name of the database | core |

5. You should now see the Query Editor

6. Create the Tables first:
   - Open the file from this folder path: `sql/schema/core-table.sql`
   - Copy and Paste the contents of this file inside the query editor and hit Run
   - *Optional: You can also save it as a query for future use

7. After all the tables have been created, move to step 8

8. Create the Views:
   - Open the file from this folder path: `sql/schema/core-view.sql`
   - Copy and Paste the contents of this file inside the query editor and hit Run
   - *Optional: You can also save it as a query for future use

9. The database is all set now.

### SEQ 5: Configure QuickSight VPC

1. Open QuickSight in the region your Analytics account is set up
2. Go to "Manage QuickSight"
3. On the left side click on "Manage VPC Connections"
4. Click on "Add VPC Connection"
5. Use the information below to update the form field for the "Add VPC Connection":

    | Field | Description |
    |-------|-------------|
    | VPC connection name | Give it a name of your choice |
    | VPC ID | Get the VPC id from the Output Tab inside the Analytics CloudFormation Stack |
    | Execution role | aws-quicksight-service-role-v0 |
    | Subnets | Choose all the subnets within the VPC |
    | Security Group IDs | Get the QuickSight Security Group ID from the Output Tab inside the Analytics CloudFormation Stack |
    | DNS resolver endpoints (optional) | Leave it blank |

6. Click Add
   - The status will show "NOT AVAILABLE"
   - It takes around 2 – 3 mins for the VPC Connection status to be "AVAILABLE"

### SEQ 6: Setup Data Source in QuickSight

1. Once the VPC connection is in an "AVAILABLE" status
2. Create a new Data Source in QuickSight
3. Choose "Amazon Aurora" as the Data source. Use the information below to update the form field for the "New Amazon Aurora data source":

    | Field | Description |
    |-------|-------------|
    | Connection type | Choose the VPC connection that was setup from earlier |
    | Database server | Get the Aurora Endpoint from the Output Tab inside the Analytics CloudFormation Stack |
    | Port | 5432 |
    | Database name | core |
    | Username | postgres |
    | Password | Open the Secrets with the Secrets ARN from the Output Tab inside the Analytics CloudFormation Stack. Go to retrieve value and get the value for the password field. |

5. Validate the connection and it should be GREEN
6. Click "Create data source"

### SEQ 7: Migrate Analysis

1. Open CloudFormation in AWS (the Analytics account)
   - Create stack
   - Choose an existing template
   - Upload the template file

2. Browse and upload the file `MAO-QS-Migration.yaml` which can be found within the `cloudformation/` folder

3. Once the S3 URL is generated, click on "View in Infrastructure Composer" and validate the template. This is recommended practice.

4. Click Next

5. There will be a requirement to set 7 parameters:

    | Parameter | Description |
    |-----------|-------------|
    | Region | The region the Analytics Account with QuickSight is deployed in |
    | AuroraClusterArn | The ARN of the Aurora Cluster from the Output Tab inside the Analytics CloudFormation Stack |
    | AuroraSecretArn | The ARN of the AuroraSecret from the Output Tab inside the Analytics CloudFormation Stack |
    | S3Bucket | Choose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | S3Uri | The URI of the QuickSight Template stored in the S3 bucket. e.g. s3://bucket-name/quicksuite/MAO-Sample-Template.qs |
    | NewAnalysisName | Your preferred name of the Analysis |
    | KMSKeyArn | The ARN of the KMS key created from the Output Tab inside the Analytics CloudFormation Stack |

6. Click Next and on the next screen under tags, give it a tag for good account hygiene.

7. Click Next and proceed to create the CloudFormation template.

8. Upon "CREATE_COMPLETE" navigate to the Outputs Tab and note the information inside.

9. Open Lambda and search for the function with "qs-migration" in the name

10. Open the lambda function and navigate to the Test tab

11. Click Test to execute the template migration

### SEQ 8: Sender Accounts

**Note:** When you create an Analytics Account, all the sender scripts are loaded in it as well. So don't follow the next steps if you are planning to set up a Sender for the Analytics account.

1. Open a Sender Account that was added to the Analytics account upon creation

2. Open CloudFormation in AWS (the sender account)
   - Create stack
   - Choose an existing template
   - Upload the template file

3. Browse and upload the file `MAO-Sender.yaml` which can be found within the `cloudformation/` folder

4. Once the S3 URL is generated, click on "View in Infrastructure Composer" and validate the template. This is recommended practice.

5. Click Next

6. There will be a requirement to set 8 parameters:

    | Parameter | Description |
    |-----------|-------------|
    | S3Bucket | Choose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | AnalyticsAccount | Analytics Account ID |
    | Region | The region of the Analytics account |
    | AnalyticsKMSKey | The ARN of the KMS key created from the Output Tab inside the Analytics CloudFormation Stack |
    | CustomerName | Customer name for the account (spare field) |
    | PartnerName | Partner name for the account (vendor name) |
    | Category | Classify whether the account is facing the Internet, Intranet or Both |
    | Environment | Environment type for the account (Production, UAT, Development, etc.) |

7. Click Next and on the next screen under tags, give it a tag for good account hygiene.

8. Click Next and proceed to create the CloudFormation template.

9. Upon "CREATE_COMPLETE" navigate to the Outputs Tab and note the information inside.

10. Open Lambda and search for the Sender function (MAO-sender-function)

11. Open the lambda function and navigate to the Test tab

12. Click Test to execute it.

## Data Collection Components

### Sender Script Capabilities
The sender script (`scripts/sender.py`) collects the following data from each account:

- **Account Information**: Basic account details, contact information, alternate contacts
- **Cost Data**: Cost and usage reports, forecasts, service-level costs
- **Security Data**: Security Hub findings, GuardDuty findings, KMS keys, WAF rules, CloudTrail logs, Secrets Manager, Certificate Manager, Inspector findings
- **Configuration**: AWS Config compliance reports and non-compliant resources
- **Service Resources**: EC2 instances, RDS databases, S3 buckets, Load Balancers, Auto Scaling groups, Lambda functions
- **Inventory**: SSM inventory data including instances, applications, and patches
- **Marketplace Usage**: AWS Marketplace entitlements and usage
- **Trusted Advisor**: Trusted Advisor check results and recommendations
- **Health Events**: AWS Health events and notifications
- **Application Signals**: Application monitoring signals
- **Resilience Hub**: Resilience assessments and recommendations
- **Compute Optimizer**: EC2, EBS, and Lambda optimization recommendations

### Receiver Script Processing
The receiver script (`scripts/receiver.py`) processes incoming data and:

- Validates data structure and integrity
- Decrypts data using KMS
- Performs upsert operations to Aurora PostgreSQL
- Manages parent-child relationships between data entities
- Handles error logging and status tracking
- Moves processed files to the `loaded/` folder

## Database Schema

The solution uses Aurora PostgreSQL with the following main tables:

### Core Tables
- `accounts` - Account information and metadata
- `contact_info` - Account contact details
- `alternate_contacts` - Alternate contact information
- `products` - Product/workload information
- `product_accounts` - Product-account relationships

### Cost & Usage Tables
- `cost_reports` - Cost analysis reports
- `service_costs` - Service-level cost breakdown
- `cost_forecasts` - Cost forecasting data
- `services` - Service usage and costs

### Security Tables
- `security` - Security Hub summaries
- `findings` - Detailed security findings
- `guard_duty_findings` - GuardDuty findings
- `kms_keys` - KMS key information
- `waf_rules` - WAF configuration
- `cloudtrail_logs` - CloudTrail configuration
- `secrets_manager_secrets` - Secrets Manager inventory
- `certificates` - Certificate Manager inventory
- `inspector_findings` - Inspector findings

### Configuration & Inventory Tables
- `config_reports` - Config compliance reports
- `non_compliant_resources` - Non-compliant resources
- `config_inventory` - Resource inventory from Config
- `service_resources` - Service resource details
- `inventory_instances` - SSM inventory instances
- `inventory_applications` - Installed applications
- `inventory_patches` - Patch information

### Optimization & Monitoring Tables
- `compute_optimizer` - Compute optimization recommendations
- `marketplace_usage` - Marketplace usage data
- `trusted_advisor_checks` - Trusted Advisor recommendations
- `health_events` - AWS Health events
- `application_signals` - Application monitoring data
- `resilience_hub_apps` - Resilience Hub assessments

### Logging Tables
- `logs` - Processing logs and status
- `log_messages` - Detailed log messages

## Troubleshooting

### Common Issues

1. **Lambda Function Timeouts**
   - Increase timeout to 900 seconds (15 minutes)
   - Increase memory to 10240 MB for large datasets

2. **Database Connection Issues**
   - Verify Aurora cluster is in "Available" state
   - Check VPC security groups allow PostgreSQL traffic (port 5432)
   - Ensure Secrets Manager permissions are correctly configured

3. **S3 Access Issues**
   - Verify bucket policies allow cross-account access for sender accounts
   - Check KMS key permissions for encryption/decryption
   - Ensure S3 event notifications are properly configured

4. **QuickSight Connection Issues**
   - Verify VPC connection is in "Available" state
   - Check security groups allow QuickSight access
   - Ensure Secrets Manager integration is properly configured

5. **Data Processing Errors**
   - Check CloudWatch logs for detailed error messages
   - Verify JSON data structure matches expected schema
   - Check for data type mismatches in database inserts

### Monitoring and Logs

- **CloudWatch Logs**: All Lambda functions log to CloudWatch with detailed processing information
- **Database Logs**: Processing status is tracked in the `logs` table
- **S3 Access Logs**: S3 access is logged to the dedicated logs bucket
- **VPC Flow Logs**: Network traffic is logged for security monitoring

## Security Considerations

1. **Encryption**: All data is encrypted at rest using KMS and in transit using TLS
2. **Access Control**: IAM roles follow least privilege principle
3. **Network Security**: Resources are deployed in private subnets with VPC endpoints
4. **Secrets Management**: Database credentials are managed through AWS Secrets Manager
5. **Audit Trail**: All API calls are logged through CloudTrail

## Outcome

1. Navigate to QuickSight and you should see a newly created Analysis
2. If you are unable to see the analysis:
   - Go to "Manage QuickSight"
   - Click on "Manage Assets"
   - Click on "Analyses"
   - Select the newly imported Analysis
   - Click on "Share"
   - Search for your QuickSight user name and select Share
3. Then navigate to the QuickSight home page and click on "Analysis"
4. You should see the newly created analysis with multi-account observability data

## Maintenance

### Regular Tasks
- Monitor CloudWatch logs for processing errors
- Review cost reports for unexpected charges
- Update sender account permissions as needed
- Backup Aurora database regularly
- Review and update security configurations

### Scaling Considerations
- Add more sender accounts by updating the Analytics account's sender accounts parameter
- Increase Aurora capacity for larger datasets
- Consider partitioning large tables by date for better performance
- Monitor Lambda concurrency limits for high-volume processing

## Support

For issues and questions:
1. Check CloudWatch logs for detailed error messages
2. Review the troubleshooting section above
3. Verify all prerequisites are met
4. Ensure all CloudFormation stacks deployed successfully