# Option A - Serverless (Only Lambda) : Introduction & Architecture

This is a comprehensive wiki guide for View 360 (Multi account observability) within AWS. Using a Serverless approach with only Lambda functions handling the transactions.
<div align="center"><img width="888" height="678" alt="View360-A360-LABELED-Option1-Only Lambda" src="https://github.com/user-attachments/assets/e6c06b88-2b35-45c4-8a0e-64654e2855e9" /></div>

# Pre-requisites

| # | Item | Description |
|---|------|-------------|
| 1 | Repository Link | https://github.com/aws-samples/sample-aws-multi-account-observability |
| 2 | Download | Download `sample-aws-multi-account-observability` the folder as a zip from AWS Samples repository |
| 3 | Extract | Extract all and place it in a folder of your choice |
| 4 | Verify | Check that you have all the files |
| 5 | Create Folder | Create a folder inside the extracted zip `sample-aws-multi-account-observability` called `quicksuite/` |
| 6 | Download Template | The AWS team will share a link to the analysis template, download that file and place it in the folder `quicksuite/` |
| 7 | QuickSuite Account | *MUST DO* - Please make sure to have an Amazon Quick Suite account created.<br>• Login to AWS Console > Search for Amazon Quick Suite<br>• Create Account & Log in to Amazon Quick Suite and ensure its working. |


# Configuration Steps

Below is the series of steps that you should follow in a sequential format to ensure proper deployment of this solution.

## SEQ 1: Setup Analytics Account

| Step | Description |
|------|-------------|
| 1 | Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps: Create Stack > Choose an existing template > Upload the template file |
| 2 | Browse and upload the file `A360-Analytics.yaml` which could be found within the `sample-aws-multi-account-observability/cloudformation-template/` folder |
| 3 | Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice. |
| 4 | Then click Next |
| 5 | There will be a requirement to set parameters, to configure this account. *Note: For this implementation, please make sure to select **NO** for 1.3 Deploy EC2 Receiver (with VPC Endpoints). |
|   | <div align="center"> <img width="682" height="836" alt="Screenshot 2026-01-09 151323" src="https://github.com/user-attachments/assets/79b4043f-ec2a-49ab-806e-c4951ca8d0f9" /> </div> |
| 6 | Click Next and on the next screen under tags, give it a tag for good account hygiene. |
| 7 | Click Next and proceed to create the CloudFormation template. |
| 8 | Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside. |
| 9 | The information within the Outputs Tab is the key to all the subsequent steps |
| 10 | Analytics Account is now created |



## SEQ 2: Setup Folders within the S3

| Step | Description |
|------|-------------|
| 1 | There will be 2 new S3 bucket created<br>• `<the_name_you_set>-<aws_account_number>-data`<br>• `<the_name_you_set>-<aws_account_number>-logs` |
| 2 | Open the newly created S3 Bucket(`<the_name_you_set>-<aws_account_number>-data`) |
| 3 | Upload the below two folders with all the content inside from the `aws-multi-account-observability/` folder into this S3 bucket at the root<br>• `scripts/`<br>• `quicksuite/` |


## SEQ 3: Setting Up Event Bridge in the Analytics account

### Set the S3 Bucket Event Trigger

| Step | Description |
|------|-------------|
| 1 | Navigate to the Analytics Account |
| 2 | Open Lambda and search for A360ReceiverFunction a function `<stack-name>-A360ReceiverFunction-<hash>` |
| 3 | Click on Add Trigger |
| 4 | Use the information below to update the form field for the Trigger Configuration |
| 4.1 | Select a Source: **S3** |
| 4.2 | Bucket: `<S3BucketName>-data` (Choose the S3 Bucket Name from the Output Tab inside the Analytics CloudFormation Stack) |
| 4.3 | Event types: **All object create events** |
| 4.4 | Prefix – optional: `data/` |
| 4.5 | Suffix – optional: `.json` |
| 5 | Click Add |


### Set the EventBridge Trigger

| Step | Description |
|------|-------------|
| 1 | Navigate to the Analytics Account |
| 2 | Open Lambda and search for A360ReceiverFunction a function `<stack-name>-A360ReceiverFunction-<hash>` |
| 3 | Click on Add Trigger |
| 4 | Use the information below to update the form field for the Trigger Configuration |
| 4.1 | Select a Source: **EventBridge (CloudWatch Events)** |
| 4.2 | Rule: **Create a new rule** |
| 4.3 | Rule name: Give it a name of your choice |
| 4.4 | Rule Description: Give it a description of your choice |
| 4.5 | Rule type: **Schedule expression** |
| 4.6 | Schedule expression: `cron(0 2 * * ? *)`<br>i.e this lambda is triggered every day at 0200 use this link to find more expressions |
| 5 | Click Add |

## SEQ 4: Setup Database

| Step | Description |
|------|-------------|
| 1 | Open Aurora and RDS and navigate to the newly created cluster |
| 2 | Open the newly created cluster `<stack_name>-auroradbcluster-<hash>` |
| 3 | Click on Query Editor |
| 4 | Use the information below to update the form field for the Connect to database |
| 4.1 | Database instance or cluster: Choose the newly created Database instance or cluster |
| 4.2 | Database Username: **Connect with a Secrets Manager ARN** |
| 4.3 | Secrets manager ARN: Get the ARN of the Newly Created Secret from the Output Tab inside the Analytics CloudFormation Stack |
| 4.4 | Enter the name of the database: `core` |
| 5 | You should now see the Query Editor |
| 6 | Create the Tables first |
| 6.1 | Open the file from this folder path `aws-multi-account-observability/sql/core-schema.sql` |
| 6.2 | Copy and Paste the contents of this file inside the query editor and hit Run |
| 6.3 | *Optional: You can also save it as a query for future use |
| 7 | After all the tables have been created move to step 8 |
| 8 | Create the Views |
| 8.1 | Open the file from this folder path `aws-multi-account-observability/sql/core-view-schema.sql` |
| 8.2 | Copy and Paste the contents of this file inside the query editor and hit Run |
| 8.3 | *Optional: You can also save it as a query for future use |
| 9 | The database is all set now. |

## SEQ 5: Configure Quick Suite VPC

| Step | Description |
|------|-------------|
| 1 | Open Amazon Quick Suite in the region your Analytics account is set up |
| 2 | Go to Manage Quick Suite |
| 3 | On the left side click on Manage VPC Connections |
| 4 | Click on Add VPC Connection |
| 5 | Use the information below to update the form field for the Add VPC Connection |
| 5.1 | VPC connection name: Give it a name of your choice |
| 5.2 | VPC ID: Get the VPC id from the Output Tab inside the Analytics CloudFormation Stack |
| 5.3 | Execution role: `aws-quicksight-service-role-v0` |
| 5.4 | Subnets: Choose all the subnets within the VPC |
| 5.5 | Security Group IDs: Get the QuickSight Security Group ID from the Output Tab inside the Analytics CloudFormation Stack |
| 5.6 | DNS resolver endpoints (optional): Leave it blank |
| 6 | Click Add |
| 6.1 | The status will show NOT AVAILABLE |
| 6.2 | It takes around 2 – 3 mins for the VPC Connection status to be AVAILABLE |

## SEQ 6: Setup Data Source in Quick Suite

| Step | Description |
|------|-------------|
| 1 | Once the VPC connection is in an AVAILABLE status |
| 2 | Create a new Data Source in Amazon Quick Suite |
| 3 | Choose Amazon Aurora as the Data Source |
| 4 | Use the information below to update the form field for the New Amazon Aurora data source |
| 4.1 | Connection type: Choose the VPC connection that was setup from earlier |
| 4.2 | Database server: Get the Aurora Endpoint from the Output Tab inside the Analytics CloudFormation Stack |
| 4.3 | Port: `5432` |
| 4.4 | Database name: `core` |
| 4.5 | Username: `postgres` |
| 4.6 | Password: Open the Secrets with the Secrets ARN from the Output Tab inside the Analytics CloudFormation Stack<br>Go to retrieve value and the value for the password field. |
| 5 | Validate the connection and it should be GREEN |
| 6 | Click Create data source |

## SEQ 7: Migrate Analysis

| Step | Description |
|------|-------------|
| 1 | Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps: Create Stack > Choose an existing template > Upload the template file |
| 2 | Browse and upload the file `A360-QS-Migration.yaml` which could be found within the `sample-aws-multi-account-observability/cloudformation-template/` folder |
| 3 | Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice. |
| 4 | Then click Next |
| 5 | There will be a requirement to set parameters<br><br><div align="center"><img width="949" height="1022" alt="Screenshot 2026-01-09 144647" src="https://github.com/user-attachments/assets/b9d29568-7696-4e7f-97ca-1878f1451b39" /></div> |
| 6 | Click Next and on the next screen under tags, give it a tag for good account hygiene. |
| 7 | Click Next and proceed to create the CloudFormation template. |
| 8 | Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside. |
| 9 | Open the Lambda and search for a function `<stack-name>-qs-migration` |
| 10 | Open the lambda function and navigate to the Test tab & Click Test to execute the template migration |

## SEQ 8: Sender Accounts
**Note**: When you create an Analytics Account, all the sender scripts are loaded in it as well. So don't follow the next steps if you are planning to set up a Sender for the Analytics account

| Step | Description |
|------|-------------|
| 1 | Open a Sender Account that was added to the Analytics account upon creation |
| 2 | Open CloudFormation in AWS (the account you wish for it to be an Analytics account) the below steps: Create Stack > Choose an existing template > Upload the template file |
| 3 | Browse and upload the file `A360-Sender.yaml` which could be found within the `sample-aws-multi-account-observability/cloudformation-template/` folder |
| 4 | Once the S3 URL is generated, click on View in Infrastructure Composer and Validate the template. This is recommended practice. |
| 5 | Then click Next |
| 6 | There will be a requirement to set parameters<br><div align="center"> <img width="935" height="1131" alt="Screenshot 2026-01-09 141717" src="https://github.com/user-attachments/assets/aa0f8638-bb2e-49e0-92f8-27ada0816b60" /> </div> |
| 7 | Click Next and on the next screen under tags, give it a tag for good account hygiene. |
| 8 | Click Next and proceed to create the CloudFormation template. |
| 9 | Upon "CREATION_COMPLETE" navigate to the Outputs Tab and note the information inside. |
| 10 | Open the Lambda and search for A360SenderFunction function `<stack-name>-A360SenderFunction-<hash>` |
| 11 | Open the lambda function and navigate to the Test tab |
| 12 | Click Test to execute it. |

# Outcome

| Step | Description |
|------|-------------|
| 1 | Navigate to QuickSuite and you should see a newly created Analysis |
| 2 | If you are unable to see the analysis |
| 3 | Go to Manage QuickSuite |
| 4 | Click on Manage Assets |
| 5 | Click on Analyses |
| 6 | Select the newly imported Analysis |
| 7 | Click on Share |
| 8 | Search for your QuickSuite user name and select Share |
| 9 | Then navigate to the QuickSuite home page and click on Analysis |
| 10 | You should see the newly created analysis like below <br> <div align="center"> <img width="720" height="257" alt="Screenshot 2026-01-09 145033" src="https://github.com/user-attachments/assets/13daa90b-72af-46ef-b2a1-684884085173" /> </div>|



