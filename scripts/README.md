# Scripts Documentation

This folder contains the core Python scripts for the AWS Multi-Account Observability Platform.

## sender.py
**Purpose**: Data collection script that runs in sender accounts to gather AWS service data.

**Key Functions**:
- Collects data from 15+ AWS services with comprehensive coverage
- Aggregates account information, security findings, cost data, and inventory
- Uploads JSON data to S3 in the analytics account with KMS encryption
- Supports DAILY, WEEKLY, MONTHLY, and YEARLY intervals
- Handles historical data loading for backfill operations
- Includes performance timing and processing metrics

**Execution**:
- Triggered by EventBridge rule (daily at 2 AM by default)
- Can be invoked manually with `{"history": true}` for historical data
- Historical data supports custom date ranges: `{"history": true, "start": "5-9-2025", "end": "10-9-2025"}`
- Automatically encrypts data with KMS before S3 upload
- Includes comprehensive error handling and retry logic

**Data Categories Collected**:
- **Account Information**: Account details, contact info, alternate contacts
- **Cost Analysis**: Current/previous period costs, forecasts, service costs
- **Service Usage**: Detailed AWS service utilization and costs by usage type
- **Security Posture**: Security Hub findings, GuardDuty alerts, compliance status
- **Configuration**: AWS Config compliance rules and non-compliant resources
- **Inventory**: EC2 instances, applications, patches via Systems Manager
- **Security Services**: KMS keys, WAF rules, CloudTrail, Secrets Manager, ACM
- **Marketplace**: Third-party software usage and costs
- **Trusted Advisor**: AWS recommendations and best practices
- **Health Events**: Service health and maintenance notifications
- **Application Signals**: Application performance metrics and traces
- **Resilience Hub**: Disaster recovery assessments and compliance
- **Compute Optimizer**: EC2, EBS, Lambda optimization recommendations
- **Service Resources**: Comprehensive AWS resource inventory
- **Config Inventory**: Resource configuration and compliance data

**New Features**:
- Enhanced WAF rules analysis with compliance checking
- Compute Optimizer integration for cost optimization
- Service resources inventory across multiple AWS services
- Config-based resource inventory for compliance tracking
- Performance timing for each data collection step
- Partner/Customer name support for multi-tenant environments

## receiver.py
**Purpose**: Data  processing script that runs in the analytics account to process and load data into Aurora PostgreSQL.

**Key Functions**:
- Monitors S3 for new JSON files from sender accounts
- Processes and validates incoming data structure with 15+ data categories
- Performs efficient upsert operations into 25+ database tables
- Handles complex parent-child relationships with foreign key integrity
- Advanced PostgreSQL type casting with custom type mapping
- Moves processed files to `loaded/` folder for cleanup and audit

**Processing Flow**:
1. Triggered by S3 PUT events or manual execution
2. Downloads and validates JSON data structure
3. Loads data into Aurora using optimized batch upserts
4. Tracks detailed processing status and statistics
5. Moves processed files to avoid reprocessing
6. Comprehensive error handling and logging

**Database Operations**:
- **Advanced Upserts**: Handles 25+ tables with complex relationships
- **Type Casting**: Custom PostgreSQL type mapping for timestamps, JSONB, arrays
- **Parent-Child Loading**: Proper sequence for accounts → cost_reports → forecasts
- **Security Data**: Comprehensive security hub, findings, WAF rules, certificates
- **Inventory Management**: Instances → applications → patches relationships
- **Performance Optimization**: Cached queries and batch operations
- **Data Integrity**: Foreign key constraints and validation

**Enhanced Features**:
- **Comprehensive Security Loading**: Security Hub, GuardDuty, KMS, WAF, CloudTrail, Secrets Manager, ACM, Inspector
- **Advanced Cost Processing**: Cost reports with service costs and forecasting
- **Inventory Relationships**: Proper parent-child loading for instances and applications
- **Marketplace Integration**: Product usage and cost tracking
- **Resilience Hub**: Disaster recovery and compliance data
- **Compute Optimizer**: Performance and cost optimization recommendations
- **Service Resources**: Multi-service resource inventory (EC2, RDS, S3, ELB, etc.)
- **Config Inventory**: Configuration compliance and resource tracking
- **Processing Statistics**: Detailed metrics on created, updated, and skipped records

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
CUSTOMER=customer-name  # optional: for multi-tenant environments
PARTNER=partner-name    # optional: for partner identification
```

## Data Flow

```
sender.py → S3 (data/{account-id}/*.json) → receiver.py → Aurora PostgreSQL
                                                    ↓
                                            loaded/{account-id}/*.json
```

**File Naming Convention**:
- Daily: `2025-01-15_DAILY.json`
- Monthly: `2025-01-31_MONTHLY.json`
- Historical: Custom date ranges with same format

**Processing Statistics**:
- Records created, updated, skipped
- Processing time per data category
- Total execution time and performance metrics

## Error Handling

- **Dead Letter Queues**: Failed executions are sent to DLQ for investigation
- **Comprehensive Logging**: All operations logged to CloudWatch with detailed error messages
- **Status Tracking**: Processing status stored in logs table with per-service status
- **Retry Logic**: Automatic retries for transient failures with exponential backoff
- **Data Validation**: Structure validation before processing
- **File Management**: Automatic cleanup and error recovery
- **Performance Monitoring**: Timing metrics for each processing step
- **Graceful Degradation**: Continues processing even if individual services fail

## Local Development

**Setup**:
1. Uncomment the dotenv imports in both files
2. Create a `.env` file with required environment variables
3. For sender.py: Use the testing section at the bottom for historical data loading
4. For receiver.py: Use the `testing()` function with sample JSON files

**Testing Functions**:
- **sender.py**: `lambda_handler({"history": True, "start": "5-9-2025", "end": "10-9-2025"})`
- **receiver.py**: `testing()` function for processing sample data files

**Sample Data**:
- Place sample JSON files in `data/` folder for receiver testing
- Use the format: `2025-09-15_DAILY.json`

## Monitoring

Monitor script execution through:
- **CloudWatch Logs**: `/aws/lambda/[function-name]` with detailed execution logs
- **Database Monitoring**: 
  - `logs` table for processing status per account and service
  - `log_messages` table for detailed error messages and warnings
- **Dead Letter Queue**: Failed executions with retry mechanisms
- **S3 Bucket Structure**: 
  - `data/` folder for incoming files
  - `loaded/` folder for processed files
- **Performance Metrics**: Processing time per data category and total execution time
- **Statistics Tracking**: Created, updated, and skipped record counts

**Key Monitoring Queries**:
```sql
-- Check processing status
SELECT account_id, account_status, cost_status, security_status 
FROM logs ORDER BY date_created DESC;

-- View error messages
SELECT message, message_type, created_at 
FROM log_messages WHERE message_type = 'ERROR';
```