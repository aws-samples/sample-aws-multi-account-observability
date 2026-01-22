# Scripts Documentation

This folder contains the core Python scripts for the View360 Analytics platform - a comprehensive AWS multi-account analytics platform that aggregates, processes, and visualizes cloud infrastructure data across multiple AWS accounts.

## sender.py
**Purpose**: Data collection script that runs in sender accounts to gather AWS service data.

**Key Functions**:
- Collects data from 15+ AWS services with comprehensive coverage
- Multi-region support for tracking accounts across multiple AWS regions
- Aggregates account information, security findings, cost data, and inventory
- Uploads JSON data to S3 in the analytics account with KMS encryption
- Supports DAILY, WEEKLY, MONTHLY, and YEARLY intervals
- Handles historical data loading for backfill operations
- Includes performance timing and processing metrics
- Enhanced compliance tracking and support ticket integration

**Execution**:
- Triggered by EventBridge rule (daily at 2 AM by default)
- Can be invoked manually with `{"history": true}` for historical data
- Historical data supports custom date ranges: `{"history": true, "start": "5-9-2025", "end": "10-9-2025"}`
- Automatically encrypts data with KMS before S3 upload
- Includes comprehensive error handling and retry logic

**Data Categories Collected**:
- **Account Information**: Basic account details, contacts, and multi-region support
- **Cost Analysis**: Spending patterns, forecasts, and optimization opportunities
- **Service Usage**: Detailed AWS service utilization and costs
- **Security Posture**: Security Hub findings, GuardDuty alerts, KMS, WAF, CloudTrail
- **Configuration**: AWS Config compliance with enhanced metadata tracking
- **Inventory**: EC2 instances with SSM Agent compliance monitoring
- **Support Tickets**: AWS Support case tracking and resolution analytics
- **Marketplace**: Third-party software usage and costs
- **Trusted Advisor**: AWS recommendations and best practices
- **Health Events**: Service health and maintenance notifications
- **Applications**: Application performance signals and metrics
- **Resilience**: Disaster recovery assessments and compliance
- **Audit Logs**: Data processing status and error tracking

**Enhanced Features (v2.x)**:
- Multi-region support for comprehensive global coverage
- Support ticket tracking and resolution analytics
- Enhanced compliance features with detailed metadata
- Partner/Customer name support for multi-tenant environments
- Performance timing for each data collection step
- Enhanced WAF rules analysis with compliance checking

## receiver.py
**Purpose**: Data  processing script that runs in the analytics account to process and load data into Aurora PostgreSQL.

**Key Functions**:
- Monitors S3 for new JSON files from sender accounts
- Processes and validates incoming data structure with 15+ data categories
- Performs efficient upsert operations into 35+ database tables
- Handles complex parent-child relationships with foreign key integrity
- Advanced PostgreSQL type casting with custom type mapping
- Moves processed files to `loaded/` folder for cleanup and audit
- Supports both Lambda and EC2 execution modes

**Processing Flow**:
1. Triggered by S3 PUT events or manual execution
2. Downloads and validates JSON data structure
3. Loads data into Aurora using optimized batch upserts
4. Tracks detailed processing status and statistics
5. Moves processed files to avoid reprocessing
6. Comprehensive error handling and logging

**Database Operations**:
- **Advanced Upserts**: Handles 35+ tables with complex relationships
- **Type Casting**: Custom PostgreSQL type mapping for timestamps, JSONB, arrays
- **Parent-Child Loading**: Proper sequence for accounts → cost_reports → forecasts
- **Security Data**: Comprehensive security hub, findings, WAF rules, certificates
- **Support Tickets**: AWS Support case tracking and analytics
- **Inventory Management**: Instances → applications → patches relationships
- **Performance Optimization**: Cached queries and batch operations
- **Data Integrity**: Foreign key constraints and validation

**Enhanced Features (v2.x)**:
- **Multi-Region Processing**: Support for accounts across multiple AWS regions
- **Support Ticket Analytics**: AWS Support case tracking and resolution metrics
- **Enhanced Compliance**: Detailed metadata tracking and compliance features
- **EC2 Receiver Option**: Alternative to Lambda for compliance requirements
- **Comprehensive Security Loading**: Security Hub, GuardDuty, KMS, WAF, CloudTrail
- **Advanced Cost Processing**: Cost reports with service costs and forecasting
- **Processing Statistics**: Detailed metrics on created, updated, and skipped records

## Deployment Options

Both deployment options use the same `A360-Analytics.yaml` CloudFormation template. The difference is in the parameter selection during deployment:

**Option A: Serverless (Lambda Only)**
- Uses `A360-Analytics.yaml` with **Deploy EC2 Receiver = NO**
- Fully serverless architecture with Lambda handling all data processing
- Automatic scaling and pay-per-use pricing
- Recommended for most deployments

**Option B: EC2 + Systems Manager**
- Uses `A360-Analytics.yaml` with **Deploy EC2 Receiver = YES**
- EC2 instance for receiver processing with VPC endpoints
- Lambda triggers SSM Run Command on EC2
- Better for compliance requirements
- Predictable costs for high-frequency processing

## CloudFormation Templates

### Analytics Account Templates
- **A360-Analytics.yaml** → Main deployment template (supports both options)
- **A360-QS-Migration.yaml** → QuickSight template migration

### Sender Account Template
- **A360-Sender.yaml** → Data collection infrastructure for sender accounts

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
REGION=ap-southeast-1
BUCKET=analytics-s3-bucket-name
ANALYTICS_KMS_KEY=arn:aws:kms:region:account:key/key-id
CUSTOMER=customer-name    # optional: for multi-tenant environments
PARTNER=partner-name      # optional: for partner identification
CATEGORY=category-name    # optional: account classification
ENVIRONMENT=environment-type  # optional: environment classification
PRODUCT=product-name      # optional: product identification
```

## Architecture & Data Flow

### Complete Flow
```
[Sender Account] EventBridge -> Lambda -> S3 (Analytics Account) ----------> Lambda / EC2 (Receiver) -> Aurora -> QuickSight
                                  │              │                                  │
                                  ▼              ▼                                  ▼
                               sender.py  data/SENDER_ACCOUNT/*.json            receiver.py
```

### Detailed Data Flow
```
sender.py → S3 (data/{account-id}/*.json) → receiver.py → Aurora PostgreSQL → QuickSight
                                                    ↓
                                            loaded/{account-id}/*.json
```

### EC2 Receiver Option (v2.x)
```
S3 Event → Lambda → SSM Run Command → EC2 Instance → receiver.py → Aurora PostgreSQL
```

**File Naming Convention**:
- Daily: `2025-01-15_DAILY.json`
- Monthly: `2025-01-31_MONTHLY.json`
- Historical: Custom date ranges with same format

**Database Schema**:
- **Tables**: 35+ tables for comprehensive data storage
- **Views**: 45+ analytics views for QuickSight integration
- **Schema Files**: `sql/schema/core-schema.sql` and `sql/schema/core-view.sql`

**Processing Statistics**:
- Records created, updated, skipped
- Processing time per data category
- Total execution time and performance metrics

## Deployment Sequence (8 Steps)

Both deployment options follow the same 8-step sequence:

1. **Setup Analytics Account** - Deploy CloudFormation template
2. **Setup S3 Folders** - Upload `scripts/` and `quicksuite/` folders
3. **Setup Event Triggers** - Configure S3 and EventBridge triggers
4. **Setup Database** - Run schema and view SQL files
5. **Configure QuickSight VPC** - Create VPC connection
6. **Setup QuickSight Data Source** - Connect to Aurora database
7. **Migrate QuickSight Analysis** - Deploy migration template
8. **Deploy Sender Accounts** - Deploy sender template in each account

See the [Deployment Guide](../DEPLOYMENT_GUIDE.md) for detailed instructions.

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

## EC2 Receiver Option (v2.x)

Version 2.x introduces EC2-based receiver as an alternative to Lambda:

### Benefits
- Full control over compute environment
- Easier debugging with direct SSH/SSM access
- Predictable costs for high-frequency processing
- Compliance-friendly for organizations with Lambda restrictions

### Deployment
- Automatically created by `A360-Analytics.yaml` with **Deploy EC2 Receiver = YES**
- Instance Type: t4g.micro (ARM-based, cost-efficient)
- Scheduled: Cron job runs daily at 3 AM
- On-Demand: Lambda → SSM Run Command → EC2 execution

### Monitoring EC2 Receiver
```bash
# View logs on EC2
tail -f /var/log/receiver.log

# Check cron job
crontab -l

# View SSM command history
aws ssm list-commands --filters Key=DocumentName,Values=AWS-RunShellScript
```

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

### Lambda Monitoring
```bash
aws logs tail /aws/lambda/A360ReceiverFunction --follow
aws logs tail /aws/lambda/A360SenderFunction --follow
```

**Key Monitoring Queries**:
```sql
-- Check processing status
SELECT account_id, account_status, cost_status, security_status 
FROM logs ORDER BY date_created DESC;

-- View error messages
SELECT message, message_type, created_at 
FROM log_messages WHERE message_type = 'ERROR';
```

## Migration from v1.x to v2.x

If upgrading from v1.x (deployments before January 2026), see the [Migration Guide](../migrations/00-v1.x-to-v2.x-migration/migration-guide.md) for detailed upgrade instructions.

v1.x refers to the original version which lacked:
- Multi-region support
- Support ticket tracking
- Enhanced compliance features
- EC2 receiver option

## Helper Function

### Get Config Data

- If you would like to get the status of all `COMPLIANT` & `NON_COMPLIANT` resources on a daily basis, In the `sender.py` Replace the  `get_config` with the below function.
- The reason why we did not use this is because, for a very active account on a daily basis it takes all the resources which can be very data intensive, hence we only take what happened on the day the script runs. We need to take the compliant reosurces as well, so the database gets updated.


```
def get_config(self):
    try:
        if not self.get_date():
            return None
        
        config_client = boto3.client('config', region_name=REGION)
        
        # Step 0: Convert dates to compare
        if not self.start_date or not self.end_date:
            return None
        
        # Use start_date for both start and end to get single day range
        start_datetime  = datetime.combine(self.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_datetime    = datetime.combine(self.start_date, datetime.min.time()).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

        # Step 1: Build Conformance Mapping
        rule_to_pack_mapping    = {}
        try:
            for pack in config_client.describe_conformance_packs()['ConformancePackDetails']:
                pack_name = pack['ConformancePackName']
                
                try:
                    pack_compliance = config_client.describe_conformance_pack_compliance(
                        ConformancePackName=pack_name
                    )
                    
                    for rule_compliance in pack_compliance['ConformancePackRuleComplianceList']:
                        if rule_name := rule_compliance.get('ConfigRuleName'):
                            rule_to_pack_mapping[rule_name] = pack_name
                            
                except Exception as e:
                    self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Conformance Pack: " + str(e)})
                    pass
                    
        except Exception as e:
            self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Conformance Pack: " + str(e)})
            pass

        # Step 2: Get all compliance data
        compliant_count         = 0
        non_compliant_count     = 0
        non_compliant_resources = []
        curr_non_compliant      = 0 # Non-Compliant rules on the date this script is run
        curr_compliant          = 0 # Compliant rules on the date this script is run

        paginator = config_client.get_paginator('describe_compliance_by_config_rule')
        
        for page in paginator.paginate(ComplianceTypes=['COMPLIANT', 'NON_COMPLIANT']):
            for rule in page.get('ComplianceByConfigRules', []):
                compliance_type = rule.get('Compliance', {}).get('ComplianceType')
                
                if compliance_type in ('COMPLIANT', 'NON_COMPLIANT'):

                    if compliance_type == 'COMPLIANT':
                        compliant_count += 1
                    elif compliance_type == 'NON_COMPLIANT':
                        non_compliant_count += 1

                    rule_name           = rule['ConfigRuleName']
                    conformance_pack    = rule_to_pack_mapping.get(rule_name, 'Standalone')
                    has_matching_result = False

                    try:
                        details = config_client.get_compliance_details_by_config_rule(
                            ConfigRuleName=rule_name,
                            ComplianceTypes=[compliance_type],
                            Limit=50
                        )

                        for eval_result in details['EvaluationResults']:
                            #config_rule_invoked_time = eval_result.get('ConfigRuleInvokedTime')
                            result_time = eval_result.get('ResultRecordedTime')

                            # Convert result_time to UTC for comparison
                            if result_time:
                                result_time_utc = result_time.astimezone(timezone.utc)
                                
                                #if start_datetime <= result_time_utc <= end_datetime:
                                has_matching_result = True
                                qualifier   = eval_result['EvaluationResultIdentifier']['EvaluationResultQualifier']
                                non_compliant_resources.append({
                                                                'rule_name'                 : rule_name,
                                                                'resource_id'               : qualifier.get('ResourceId'),
                                                                'resource_type'             : qualifier.get('ResourceType'),
                                                                'config_rule_invoked_time'  : result_time,
                                                                'conformance_pack'          : conformance_pack,
                                                                'compliance_type'           : eval_result.get('ComplianceType'),
                                                                'annotation'                : eval_result.get('Annotation'),
                                                                'evaluation_mode'           : qualifier.get('EvaluationMode')
                                                                })
                        if has_matching_result:
                            
                            if compliance_type == 'COMPLIANT':
                                curr_compliant += 1 # Compliant rules on the date this script is run
                            elif compliance_type == 'NON_COMPLIANT':
                                curr_non_compliant += 1 # Non-Compliant rules on the date this script is run
                                
                    except Exception as e:
                        self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Compliance rules: "+str(e)})


                
                    rule_name           = rule['ConfigRuleName']
                    conformance_pack    = rule_to_pack_mapping.get(rule_name, 'Standalone')
                    has_matching_result = False
                    
                    

        # Step 3: Calculate totals and score
        
        total_rules     = compliant_count + non_compliant_count
        compliance_score= round((compliant_count / max(total_rules, 1)) * 100, 2) if total_rules > 0 else 0
        config_data     = {
                            'date_from'                 : self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
                            'date_to'                   : self.end_date.strftime('%Y-%m-%d') if self.end_date else '',
                            'compliance_score'          : compliance_score,
                            'total_rules'               : total_rules,
                            'compliant_rules'           : compliant_count,
                            'non_compliant_rules'       : non_compliant_count,
                            'curr_non_compliant'        : curr_non_compliant,
                            'curr_compliant'            : curr_compliant,
                            'non_compliant_resources'   : non_compliant_resources
                            }
        print({'curr_non_compliant': curr_non_compliant,'curr_compliant': curr_compliant,})
        
        self.data.set_data(attr=AWSResourceType.CONFIG, data=config_data)
        self.set_log(def_type=AWSResourceType.CONFIG)

        return config_data
        
    except Exception as e:
        self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': str(e)})
        return None
```