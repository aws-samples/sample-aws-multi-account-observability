# Deployment Guide
There are two implementation for the Analytics account. Based on the V1.xx release and customer feedback we added a mechanism that would allow you to use an EC2 & SSM agent for the Receiver, this is applicable for large datasets that might not be able to process within the 15 minute time window provisioned by lambda.

The below is a comprehensive details on both the different options:

## Table of Contents

- <a href="#option-a--serverless-deployment">Option A: Serverless Deployment</a>
  - <a href="#architecture">Architecture</a>
  - <a href="#process-flow">Process Flow</a>
  - <a href="option-a-serverless-deployment.md" target="_blank">Deployment Guide ⧉</a>
- <a href="#option-b--lambda--ec2--ssm-deployment">Option B: Lambda + EC2 + SSM Deployment</a>
  - <a href="#architecture-1">Architecture</a>
  - <a href="#process-flow-1">Process Flow</a>
  - <a href="option-b-ec2-deployment.md" target="_blank">Deployment Guide ⧉</a>

# Pre-requisites

<table width="100%">
<tr>
<th width="5%">#</th>
<th width="25%">Item</th>
<th width="70%">Description</th>
</tr>
<tr>
<td>1</td>
<td>Repository Link</td>
<td>https://github.com/aws-samples/sample-aws-multi-account-observability</td>
</tr>
<tr>
<td>2</td>
<td>Download</td>
<td>Download <code>sample-aws-multi-account-observability</code> the folder as a zip from AWS Samples repository</td>
</tr>
<tr>
<td>3</td>
<td>Extract</td>
<td>Extract all and place it in a folder of your choice</td>
</tr>
<tr>
<td>4</td>
<td>Verify</td>
<td>Check that you have all the files</td>
</tr>
<tr>
<td>5</td>
<td>QuickSuite Account</td>
<td><em>MUST DO</em> - Please make sure to have an Amazon Quick Suite account created.<br>• Login to AWS Console > Search for Amazon Quick Suite<br>• Create Account & Log in to Amazon Quick Suite and ensure its working.</td>
</tr>
</table>

# Option A : Serverless Deployment
Using a Serverless approach with only Lambda functions handling the transactions.

## Architecture

<table>
<tr>
<td colspan=4 align=center width=100%>
<img width="962" height="767" alt="A360-Option1-Lambda" src="https://github.com/user-attachments/assets/4caca7b8-07b3-488d-9ab3-ca3f47cd0802" />
</td>
</tr>
<tr>
<th width="5%">Step</th>
<th width="30%">Component</th>
<th width="20%">Action</th>
<th width="45%">Description</th>
</tr>
<tr>
<td><strong>1</strong></td>
<td>EventBridge (Daily Schedule)</td>
<td>Triggers</td>
<td>Daily trigger at 01:00 AM activates sender function</td>
</tr>
<tr>
<td><strong>2</strong></td>
<td>Sender Function (Lambda)</td>
<td>Executes</td>
<td>Collects data from AWS services (10GB/15min capacity)</td>
</tr>
<tr>
<td><strong>3</strong></td>
<td>KMS Key</td>
<td>Encrypts</td>
<td>Provides encryption for data security</td>
</tr>
<tr>
<td><strong>4</strong></td>
<td>S3 Data Bucket</td>
<td>Receives</td>
<td>Stores encrypted JSON data from sender accounts</td>
</tr>
<tr>
<td><strong>5</strong></td>
<td>Receiver Function (Lambda)</td>
<td>Processes</td>
<td>Triggered by S3 PUT events, processes JSON data (10GB/15min)</td>
</tr>
<tr>
<td><strong>6</strong></td>
<td>Aurora Primary</td>
<td>Stores</td>
<td>Primary database instance (Serverless v2 - Postgres)</td>
</tr>
<tr>
<td><strong>7</strong></td>
<td>QuickSight / QuickSuite</td>
<td>Visualizes</td>
<td>Connects via VPC endpoint for dashboard access</td>
</tr>
<tr>
<td colspan=4 width=100%>

>ℹ️ **Information**
>- **a - Secrets Manager (Credentials)**: Stores Aurora database credentials securely
>- **b - Aurora Replica (High Availability)**: Read replica in Private Subnet 2 (10.0.5.0/24) - AZ 2
>- **c - Multi-AZ Standby (Disaster Recovery)**: Standby instance in Private Subnet 3 (10.0.6.0/24) - AZ 3
>- **d - QuickSight Endpoint (Secure Access)**: VPC endpoint for QuickSight connectivity
>- **DLQ (SQS) - Error Handling**: Dead Letter Queue for failed message processing

</td>
</tr>
<tr>
<td colspan=4 width=100%>

>🔒 **Security Groups & Network**
>- **RDS Security Group**: Controls database access in Private Subnet 1 (10.0.4.0/24) - AZ 1
>- **RDS Security Group**: Controls database access in Private Subnet 2 (10.0.5.0/24) - AZ 2
>- **RDS Security Group**: Controls database access in Private Subnet 3 (10.0.6.0/24) - AZ 3
>- **QuickSight Security Group**: Controls analytics access in Private Subnet 3 (10.0.6.0/24) - AZ 3

</td>
</tr>

</table>

## Process Flow
<table>
<tr>
<td colspan=4 align=center width=100%>
<img width="962" height="335" alt="A360-Option1-Flow-Lambda" src="https://github.com/user-attachments/assets/59401600-c16a-4141-be83-041b9e6c71dc" /> 
</td>
</tr>
<tr>
<th width="5%">Step</th>
<th width="30%">Component</th>
<th width="20%">Action</th>
<th width="45%">Description</th>
</tr>
<tr>
<td><strong>1</strong></td>
<td>S3 Event (ObjectCreated)</td>
<td>Triggers</td>
<td>New JSON file uploaded to S3 data/ folder</td>
</tr>
<tr>
<td><strong>2</strong></td>
<td>Lambda Function (a360-receiver)</td>
<td>Receives</td>
<td>S3 event notification triggers receiver function</td>
</tr>
<tr>
<td><strong>3</strong></td>
<td>Lambda Function (a360-receiver)</td>
<td>Fetches</td>
<td>Downloads receiver.py script from S3 bucket</td>
</tr>
<tr>
<td><strong>4</strong></td>
<td>Lambda Function (a360-receiver)</td>
<td>Processes</td>
<td>Reads and processes JSON data from uploaded file</td>
</tr>
<tr>
<td><strong>5</strong></td>
<td>Lambda Function (a360-receiver)</td>
<td>Updates/Inserts</td>
<td>Writes processed data to Aurora PostgreSQL database</td>
</tr>
<tr>
<td><strong>6</strong></td>
<td>Lambda Function (a360-receiver)</td>
<td>Moves</td>
<td>Transfers processed JSON file to loaded/ folder in S3</td>
</tr>
<tr>
<td><strong>7</strong></td>
<td>S3 Bucket (Analytics Account)</td>
<td>Stores</td>
<td>Maintains processed files in loaded/ACCOUNT/REGION/YYYY-MM-DD_DAILY.json structure</td>
</tr>
</table>




# Option B : Lambda + EC2 + SSM Deployment
Using a EC2 & SSM agent in the Receiver with a Lambda Function to invoke based on events.

## Architecture

<table>
<tr>
<td colspan=4 align=center width=100%>
<img width="962" height="767" alt="A360-Option2-EC2" src="https://github.com/user-attachments/assets/9f7b4d17-5aaa-483c-b359-3720cf3b5230" />
</td>
</tr>

<tr>
<th width="5%">Step</th>
<th width="20%">Component</th>
<th width="30%">Action</th>
<th width="45">Description</th>
</tr>
<tr>
<td><strong>1</strong></td>
<td>EventBridge (Daily Schedule)</td>
<td>Triggers</td>
<td>Daily trigger at 01:00 AM activates sender function</td>
</tr>
<tr>
<td><strong>2</strong></td>
<td>Sender Function (Lambda)</td>
<td>Executes</td>
<td>Collects data from AWS services (10GB/15min capacity)</td>
</tr>
<tr>
<td><strong>3</strong></td>
<td>KMS Key</td>
<td>Encrypts</td>
<td>Provides encryption for data security</td>
</tr>
<tr>
<td><strong>4</strong></td>
<td>S3 Data Bucket</td>
<td>Receives</td>
<td>Stores encrypted JSON data from sender accounts</td>
</tr>
<tr>
<td><strong>5</strong></td>
<td>Receiver Function (Lambda)</td>
<td>Processes</td>
<td>Triggered by S3 PUT events, processes JSON data (10GB/15min)</td>
</tr>
<tr>
<td><strong>6</strong></td>
<td>SSM Endpoint & EC2 Receiver</td>
<td>Connects & Processes</td>
<td>Downloads receiver.py script from S3 bucket, Reads and processes JSON data from uploaded file</td>
</tr>
<tr>
<td><strong>7</strong></td>
<td>RDS Data Endpoint</td>
<td>Connects</td>
<td>Enables secure database connectivity</td>
</tr>
<tr>
<td><strong>8</strong></td>
<td>Aurora Primary</td>
<td>Stores</td>
<td>Primary database instance (Serverless v2 - Postgres)</td>
</tr>
<tr>
<td><strong>9</strong></td>
<td>QuickSight</td>
<td>Visualizes</td>
<td>Connects via VPC endpoint for dashboard access</td>
</tr>
<tr>
<td colspan=4 width=100%>

>ℹ️ **Information**
>- **a - Secrets Manager (Credentials)**: Stores Aurora database credentials securely
>- **c - EC2 Receiver (Alternative Processing)**: EC2-based receiver (t4g.small) for compliance scenarios
>- **d - Aurora Replica (High Availability)**: Read replica in separate AZ (Postgres)
>- **d - Multi-AZ Standby (Disaster Recovery)**: Standby instance in third AZ (Postgres)
>- **e - QuickSight Endpoint (Secure Access)**: VPC endpoint for QuickSight connectivity

</td>
</tr>
<td colspan=4 width=100%>

>🔒 **Security Groups & Network**
>- **EC2 Security Group**: Controls EC2 access in Private Subnet 1 (10.0.4.0/24)
>- **Lambda Security Group**: Controls Lambda VPC access in Private Subnet 1 (10.0.4.0/24)
>- **RDS Security Group**: Controls database access in Private Subnets 1-3
>- **QuickSight Security Group**: Controls analytics access in Private Subnet 3 (10.0.6.0/24)

</td>
</tr>
</table>

## Process Flow

<table width="100%">
<tr>
<td colspan=4 align=center width=100%>
<img width="962" height="330" alt="A360-Option2-Flow-EC2" src="https://github.com/user-attachments/assets/58109080-795b-4d2e-8bf9-cb50c6de38ab" />
</td>
</tr>
<tr>
<th width="5%">Step</th>
<th width="20%">Component</th>
<th width="30%">Action</th>
<th width="45">Description</th>
</tr>
<tr>
<td><strong>1</strong></td>
<td>S3 Event (ObjectCreated)</td>
<td>Triggers</td>
<td>New JSON file uploaded to S3 data/ folder</td>
</tr>
<tr>
<td><strong>2</strong></td>
<td>Lambda Function (a360-ec2-trigger)</td>
<td>Receives</td>
<td>S3 event notification triggers EC2-trigger function</td>
</tr>
<tr>
<td><strong>3</strong></td>
<td>Lambda Function (a360-ec2-trigger)</td>
<td>Invokes</td>
<td>Calls SSM agent to execute receiver function</td>
</tr>
<tr>
<td><strong>4</strong></td>
<td>SSM (a360-ssm)</td>
<td>Triggers</td>
<td>SSM agent triggers EC2 instance to run receiver</td>
</tr>
<tr>
<td><strong>5</strong></td>
<td>EC2 Instance (a360-ec2)</td>
<td>Fetches</td>
<td>Downloads receiver.py script from S3 bucket</td>
</tr>
<tr>
<td><strong>6</strong></td>
<td>EC2 Instance (a360-ec2)</td>
<td>Processes</td>
<td>Reads and processes JSON data from uploaded file</td>
</tr>
<tr>
<td><strong>7</strong></td>
<td>EC2 Instance (a360-ec2)</td>
<td>Updates/Inserts</td>
<td>Writes processed data to Aurora PostgreSQL database</td>
</tr>
<tr>
<td><strong>8</strong></td>
<td>EC2 Instance (a360-ec2)</td>
<td>Moves</td>
<td>Transfers processed JSON file to loaded/ folder in S3</td>
</tr>
<tr>
<td><strong>9</strong></td>
<td>S3 Bucket (Analytics Account)</td>
<td>Stores</td>
<td>Maintains processed files in loaded/ACCOUNT/REGION/YYYY-MM-DD_DAILY.json structure</td>
</tr>
</table>
