# Scripts Documentation

This folder contains the core Python scripts for the AWS Multi-Account Observability Platform.

## Sender: sender.py
**Purpose**: Data collection script that runs in sender accounts to gather AWS service data.

**Key Functions**:
- Collects data from 12+ AWS services (Cost Explorer, Security Hub, Config, etc.)
- Aggregates account information, security findings, cost data, and inventory
- Uploads JSON data to S3 in the analytics account
- Supports DAILY, WEEKLY, MONTHLY, and YEARLY intervals
- Handles historical data loading for backfill operations

**Execution**:
- Triggered by EventBridge rule (daily at 2 AM by default)
- Can be invoked manually with `{"history": true}` for historical data
- Automatically encrypts data with KMS before S3 upload

**Data Categories Collected**:
- Account details and contacts
- Cost analysis and forecasts
- Security Hub findings and GuardDuty alerts
- AWS Config compliance
- Service usage and costs
- Systems Manager inventory
- Marketplace usage
- Trusted Advisor recommendations
- Health events
- Application signals
- Resilience Hub assessments

## Receiver: receiver.py
**Purpose**: Data processing script that runs in the analytics account to process and load data into Aurora PostgreSQL.

**Key Functions**:
- Monitors S3 for new JSON files from sender accounts
- Processes and validates incoming data structure
- Performs efficient upsert operations into 25+ database tables
- Handles parent-child relationships (e.g., accounts → findings)
- Automatic type casting for PostgreSQL compatibility
- Moves processed files to `loaded/` folder for cleanup

**Processing Flow**:
1. Triggered by S3 PUT events
2. Downloads and validates JSON data
3. Loads data into Aurora using optimized upserts
4. Tracks processing status in logs table
5. Moves processed files to avoid reprocessing

**Database Operations**:
- Upserts data into accounts, cost_reports, security, services tables
- Maintains referential integrity with foreign keys
- Handles complex nested data structures (security findings, cost forecasts)
- Automatic timestamp management for audit trails

## Environment Variables

## Environment Variables

### receiver.py
```bash
DB_NAME=core
AURORA_CLUSTER_ARN=arn:aws:rds:region:account:cluster:cluster-name
AURORA_SECRET_ARN=arn:aws:secretsmanager:region:account:secret:secret-name
REGION=ap-southeast-1
BUCKET=analytics-s3-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
```

### sender.py
```bash
REGION=ap-southeast-1  # defaults to ap-southeast-1 if not set
BUCKET=analytics-s3-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
```

## Data Flow

```
sender.py → S3 (data/{account-id}/*.json) → receiver.py → Aurora PostgreSQL
```

## Error Handling

- **Dead Letter Queues**: Failed executions are sent to DLQ for investigation
- **Comprehensive Logging**: All operations logged to CloudWatch
- **Status Tracking**: Processing status stored in logs table
- **Retry Logic**: Automatic retries for transient failures

## Local Development

For local testing, uncomment the dotenv imports and create a `.env` file with required environment variables.

## Monitoring

Monitor script execution through:
- CloudWatch Logs: `/aws/lambda/[function-name]`
- Database logs table for processing status
- Dead Letter Queue for failed executions
- S3 bucket structure for data flow verification