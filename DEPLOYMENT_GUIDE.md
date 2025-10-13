# View360 Deployment Guide

This is a comprehensive deployment guide for View 360 (Multi account observability) within AWS.

## Introduction & Architecture

### Architecture design
**Standardized multi-account data flow**

| Steps | Description |
|-------|-------------|
| 1 | EventBridge triggers the Sender function Sender retrieves its function files from S3 bucket. Sender retrieves account data• Data is encrypted using KMS key. Encrypted data is transmitted to S3 |
| 2 | S3 event notification triggers Receiver Lambda function, Receiver retrieves its function files from S3 bucket. Receiver Lambda retrieves encrypted content from S3 |
| 3 | Receiver Lambda accesses KMS, Encrypted data is decrypted using KMS key |
| 4 | Receiver Lambda retrieves database credentials from Secrets Manager. Authentication details are validated |
| 5 | Decrypted data is processed. Aurora database is updated with new data |
| 6 | Data is now available in Aurora database. QuickSight can access and query the data for visualization |

## Pre-requisites

1. Download sample-aws-multi-account-observability the folder as a zip from AWS Samples repository
2. Extract all and place it in a folder of your choice
3. Check that you have all the files
4. The AWS team will share a link to the analysis template, download that file and place it in the folder quicksight/

## Configuration Steps

Below is the series of steps that you should follow in a sequential format to ensure proper deployment of this solution.

### SEQ 1: Setup Analytics Account

1. Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps
   a. Create stack
   b. Choose an existing template
   c. Upload the template file
2. Browse and upload the file Agency360-Analytics.yml which could be found within the sample-aws-multi-account-observability/cloudformation-template/ folder
3. Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice.
4. Then click Next
5. There will be a requirement to set 6 parameters

    | Optional / Mandatory | Parameter | Description |
    |----------|-----------|-------------|
    | Optional | Category | Classify whether the account is facing the Internet, Intranet or Both |
    | Optional | CustomerName | Customer name for the account (spare field) |
    | Optional | Environment | Environment type for the account |
    | Optional | PartnerName | Partner name for the account (vendor name) |
    | Mandatory | S3BucketName | Name of the S3 bucket to create* only in small letters NO CAPS. Ensure that the bucket name is unique |
    | Mandatory | SenderAccounts | List of AWS Account IDs that can send data (comma-separated) |

6. Click Next and on the next screen under tags, give it a tag for a good account hygiene.
7. Click Next and proceed to create the CloudFormation template.
8. Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside.
9. The information within the Outputs Tab is the key for all the subsequent steps
10. Analytics Account is now created

### SEQ 2: Setup Folders within the S3

1. There will be 2 new S3 bucket created
   a. --data
   b. --logs
2. Open the newly created S3 Bucket(--data)
3. Upload the below two folders with all the content inside from the aws-multi-account-observability/ folder into this S3 bucket at the root
   a. scripts/
   b. quicksight/

### SEQ 3: Setting Up Event Bridge in the Analytics account

Set the S3 Bucket Event Trigger
1. Navigate to the Analytics Account
2. Open Lambda and search for A360ReceiverFunction a function -A360ReceiverFunction-
3. Click on Add Trigger
4. Use the information below to update the form field for the Trigger Configuration

    | Field | Description |
    |-------|-------------|
    | Select a Source | S3 |
    | Bucket | -dataChoose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | Event types | All object create events |
    | Prefix – optional | data/ |
    | Suffix – optional | .json |

5. Click Add

Set the EventBridge Trigger
1. Navigate to the Analytics Account
2. Open Lambda and search for A360ReceiverFunction a function -A360ReceiverFunction-
3. Click on Add Trigger
4. Use the information below to update the form field for the Trigger Configuration

    | Field | Description |
    |-------|-------------|
    | Select a Source | EventBridge (CloudWatch Events) |
    | Rule | Create a new rule |
    | Rule name | Give it a name of your choice |
    | Rule description | Give it a description of your choice |
    | Rule type | Schedule expression |
    | Schedule expression | rate(24 hours)i.e this lambda is triggered every 24 hours use this link to find more expressions |

5. Click Add

### SEQ 4: Setup Database

1. Open Aurora and RDS and navigate to the newly created cluster
2. Open the newly created cluster -auroradbcluster-
3. Click on Query Editor
4. Use the information below to update the form field for the Connect to database

    | Parameter | Description |
    |-----------|-------------|
    | Database instance or cluster | Choose the newly created Database instance or cluster |
    | Database Username | Connect with a Secrets Manager ARN |
    | Secrets manager ARN | Get the ARN of the Newly Created Secret from the Output Tab inside the Analytics CloudFormation Stack |
    | Enter the name of the database | core |

5. You should now see the Query Editor
6. Create the Tables first
   a. Open the file from this folder path aws-multi-account-observability/sql/core-schema.sql
   b. Copy and Paste the contents of this file inside the query editor and hit Run
   c. *Optional: You can also save it as a query for future use
7. After all the tables have been create moved to the 8
8. Create the Views
   a. Open the file from this folder path aws-multi-account-observability/sql/core-view-schema.sql
   b. Copy and Paste the contents of this file inside the query editor and hit Run
   c. *Optional: You can also save it as a query for future use
9. The database is all set now.

### SEQ 5: Configure QuickSight VPC

1. Open QuickSight in the region your Analytics account is set up
2. Go to Manage QuickSight
3. On the left side click on Manage VPC Connections
4. Click on Add VPC Connection
5. Use the information below to update the form field for the Add VPC Connection

    | Field | Description |
    |-------|-------------|
    | VPC connection name | Give it a name of your choice |
    | VPC ID | Get the VPC id from the Output Tab inside the Analytics CloudFormation Stack |
    | Execution role | aws-quicksight-service-role-v0 |
    | Subnets | Choose all the subnets within the VPC |
    | Security Group IDs | Get the QuickSight Security Group ID from the Output Tab inside the Analytics CloudFormation Stack |
    | DNS resolver endpoints (optional) | Leave it blank |

6. Click Add
   a. The status will show NOT AVAILABLE
   b. It takes around 2 – 3 mins for the VPC Connection status to be AVAILABLE

### SEQ 6: Setup Data Source in Quick Sight

1. Once the VPC connection is in an AVAILABLE status
2. Create a new Data Source in QuickSight
3. Choose Amazon Aurora as the Data your source document. Use the information below to update the form field for the New Amazon Aurora data source

    | Field | Description |
    |-------|-------------|
    | Connection type | Choose the VPC connection that was setup from earlier |
    | Database server | Get the Aurora Endpoint from the Output Tab inside the Analytics CloudFormation Stack |
    | Port | 5432 |
    | Database name | core |
    | Username | postgres |
    | Password | Open the Secrets with the Secrets ARN from the Output Tab inside the Analytics CloudFormation StackGo to retrieve value and the value for the password field. |

5. Validate the connection and it should be GREEN
6. Click Create data source

### SEQ 7: Migrate Analysis

1. Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps
   a. Create stack
   b. Choose an existing template
   c. Upload the template file
2. Browse and upload the file Agency360-QS-Migration.yml which could be found within the sample-aws-multi-account-observability/cloudformation-template/ folder
3. Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice.
4. Then click Next
5. There will be a requirement to set 7 parameters

    | Parameter | Description |
    |-----------|-------------|
    | Region | The region the Analytics Account with QuickSight is Deployed in. |
    | AuroraClusterArn | The ARN of the Aurora Cluster from the Output Tab inside the Analytics CloudFormation Stack |
    | AuroraSecretArn | The ARN of the AuroraSecret from the Output Tab inside the Analytics CloudFormation Stack |
    | S3Bucket | -dataChoose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | S3Uri | The URI of the QuickSight Template stored in the S3 bucket.e.g /quicksight/a360-sample/template.qsGet the S3 URI of this file |
    | NewAnalysisName | Your preferred name of the Analysis |
    | KMSKeyArn | The ARN of the KMS key created from the Output Tab inside the Analytics CloudFormation Stack |

6. Click Next and on the next screen under tags, give it a tag for good account hygiene.
7. Click Next and proceed to create the CloudFormation template.
8. Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside.
9. Open the Lambda and search for a function -qs-migration
10. Open the lambda function and navigate to the Test tab
11. Click Test to execute the template migration

### SEQ 8: Sender Accounts

Note: When you create an Analytics Account, all the sender scripts are loaded in it as well. So don't follow the next steps if you are planning to set up a Sender for the Analytics account

1. Open a Sender Account that was added to the Analytics account upon creation
2. Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps
   a. Create stack
   b. Choose an existing template
   c. Upload the template file
3. Browse and upload the file Agency360-QS-Sender.yml which could be found within the sample-aws-multi-account-observability/cloudformation-template/ folder
4. Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice.
5. Then click Next
6. There will be a requirement to set 8 parameters

    | Parameter | Description |
    |-----------|-------------|
    | S3Bucket | -dataChoose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack |
    | AnalyticsAccount | Analytics Account ID |
    | Region | The region of the Analytics account |
    | KMS | The ARN of the KMS key created from the Output Tab inside the Analytics CloudFormation Stack |
    | CustomerName | Customer name for the account (spare field) |
    | PartnerName | Partner name for the account (vendor name) |
    | Category | Classify whether the account is facing the Internet, Intranet or Both |
    | Environment | Environment type for the account (Production, Uat, Development, etc..) |

7. Click Next and on the next screen under tags, give it a tag for good account hygiene.
8. Click Next and proceed to create the CloudFormation template.
9. Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside.
10. Open the Lambda and search for A360SenderFunction function -A360SenderFunction-
11. Open the lambda function and navigate to the Test tab
12. Click Test to execute it.

## Outcome

1. Navigate to QuickSight and you should see a newly created Analysis
2. If you are unable to see the analysis
3. Go to Manage QuickSight
4. Click on Manage Assets
5. Click on Analyses
6. Select the newly imported Analysis
7. Click on Share
8. Search for your QuickSight user name and select Share
9. Then navigate to the QuickSight home page and click on Analysis
10. You should see the newly created analysis