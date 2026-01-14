# Multi Account Observability - AWS API Data Collection & Processing Documentation

## System Architecture

**Sender (sender.py)**: Data collection from AWS APIs → S3 storage  
**Receiver (receiver.py)**: S3 data retrieval → Aurora PostgreSQL database

## Data Categories Overview

| Type | Sender Function | Receiver Function | Database Tables |
|------|----------------|-------------------|----------------|
| Account Information | `get_account_details()` | `load_account_data()` | `accounts`, `contact_info`, `alternate_contacts`, `products`, `product_accounts` |
| Cost Analysis | `get_cost()` | `load_cost_data()` | `cost_reports`, `service_costs`, `cost_forecasts` |
| Service Usage | `get_services()` | `load_service_data()` | `services` |
| Security Posture | `get_security()` | `load_security_data()` | `security`, `findings`, `guard_duty_findings`, `kms_keys`, `waf_rules`, `waf_rules_detailed`, `cloudtrail_logs`, `secrets_manager_secrets`, `certificates`, `inspector_findings` |
| Configuration | `get_config()` | `load_config_data()` | `config_reports`, `non_compliant_resources` |
| Inventory | `get_inventory()` | `load_inventory_data()` | `inventory_instances`, `inventory_applications`, `inventory_patches` |
| Marketplace | `get_marketplace()` | `load_marketplace_data()` | `marketplace_usage` |
| Trusted Advisor | `get_trusted_advisor()` | `load_trusted_advisor_data()` | `trusted_advisor_checks` |
| Health Events | `get_health()` | `load_health_data()` | `health_events` |
| Applications | `get_application_signals()` | `load_application_data()` | `application_signals` |
| Resilience | `get_resilience_hub_apps()` | `load_resilience_hub_data()` | `resilience_hub_apps` |
| Compute Optimizer | `get_compute_optimizer()` | `load_compute_optimizer_data()` | `compute_optimizer` |
| Service Resources | `get_services_resources()` | `load_service_resources_data()` | `service_resources` |
| Config Inventory | `get_config_resource_inventory()` | `load_config_inventory_data()` | `config_inventory` |
| Support Tickets | `get_support_tickets()` | `load_support_tickets_data()` | `support_tickets` |
| Audit Logs | `set_log()` | `load_logs_data()` | `logs`, `log_messages` |

## AWS Services and API Methods (Sender)

| AWS Service | API Method | Sender Function | Data Retrieved | Processing Notes |
|-------------|------------|-----------------|----------------|------------------|
| **STS** | `get_caller_identity()` | `get_account_details()` | Account ID, user ARN, user ID | Required for authentication |
| **Account** | `get_account_information()` | `get_account_details()` | Account name, creation date, status | Optional - handles errors gracefully |
| **Account** | `get_contact_information()` | `get_account_details()` | Company details, address, phone | Nested in account data |
| **Account** | `get_alternate_contact()` | `get_account_details()` | Billing/Operations/Security contacts | Loops through contact types |
| **Cost Explorer** | `get_cost_and_usage()` | `get_cost()`, `get_services()` | Service costs, usage, trends | Multiple calls for different groupings |
| **Cost Explorer** | `get_cost_forecast()` | `get_cost()` | 30-day cost predictions | Error handling for unavailable forecasts |
| **Config** | `describe_compliance_by_config_rule()` | `get_config()` | Compliance status by rule | Fast compliance overview |
| **Config** | `get_compliance_details_by_config_rule()` | `get_config()` | Non-compliant resource details | Parallel processing with ThreadPoolExecutor |
| **SSM** | `describe_instance_information()` | `get_inventory()` | Managed instance details | Base for inventory collection |
| **SSM** | `get_inventory()` | `get_inventory()` | Applications, services, patches | Limited to supported inventory types |
| **SSM** | `describe_instance_patches()` | `get_patch_details()` | Individual patch status | Called per instance for detailed patch info |
| **Security Hub** | `get_findings()` | `get_security_hub()` | Security findings with filters | Date range and severity filtering |
| **GuardDuty** | `list_detectors()` | `get_guard_duty_security()` | Detector IDs | Loops through all detectors |
| **GuardDuty** | `list_findings()` | `get_guard_duty_security()` | Finding IDs with date filter | Date range criteria applied |
| **GuardDuty** | `get_findings()` | `get_guard_duty_security()` | Detailed threat findings | Limited to 50 findings per detector |
| **KMS** | `list_keys()` | `get_kms_security()` | Key IDs and metadata | Filters by creation date |
| **KMS** | `describe_key()` | `get_kms_security()` | Key details and state | Per-key detailed information |
| **KMS** | `get_key_rotation_status()` | `get_kms_security()` | Rotation status | Handles access denied gracefully |
| **WAF v2** | `list_web_acls()` | `get_waf_security()` | Web ACL names and IDs | Both REGIONAL and CLOUDFRONT scopes |
| **WAF v2** | `get_web_acl()` | `get_waf_security()` | ACL rules and configuration | Detailed rule analysis |
| **WAF v2** | `list_resources_for_web_acl()` | `get_waf_security()` | Associated resources | ALB and CloudFront associations |
| **WAF v2** | `get_logging_configuration()` | `get_waf_security()` | Logging status | Error handling for missing configs |
| **CloudTrail** | `describe_trails()` | `get_cloudtrail_security()` | Trail configurations | Multi-region trail support |
| **CloudTrail** | `get_trail_status()` | `get_cloudtrail_security()` | Logging status and times | Active logging verification |
| **CloudTrail** | `lookup_events()` | `get_cloudtrail_security()` | Recent events in date range | Limited to 5 events for activity check |
| **Secrets Manager** | `list_secrets()` | `get_secrets_security()` | Secret metadata and rotation | Date filtering for recent activity |
| **ACM** | `list_certificates()` | `get_certificate_security()` | Certificate ARNs and domains | All certificates regardless of date |
| **ACM** | `describe_certificate()` | `get_certificate_security()` | Expiration and validation details | Per-certificate detailed info |
| **Inspector v2** | `list_findings()` | `get_inspector()` | Vulnerability findings | Date range filtering |
| **Support** | `describe_trusted_advisor_checks()` | `get_trusted_advisor()` | Available check categories | English language only |
| **Support** | `describe_trusted_advisor_check_result()` | `get_trusted_advisor()` | Check results and recommendations | Only warning/error status checks |
| **Application Signals** | `list_services()` | `get_application_signals()` | Service metrics and attributes | 24-hour time limit adjustment |
| **Resilience Hub** | `list_apps()` | `get_resilience_hub_apps()` | App summaries and assessments | Date filtering for recent activity |
| **Resilience Hub** | `describe_app()` | `get_resilience_hub_apps()` | Detailed app configuration | Per-app policy details |
| **Resilience Hub** | `describe_resiliency_policy()` | `get_resilience_hub_apps()` | RTO/RPO values | Policy-based resilience metrics |
| **Health** | `describe_events()` | `get_health()` | Service health events | Global service, us-east-1 only |
| **Marketplace** | `get_entitlements()` | `get_marketplace()` | Product entitlements | May fail if no marketplace products |
| **Compute Optimizer** | `get_ec2_instance_recommendations()` | `get_compute_optimizer()` | EC2 optimization recommendations | Error handling per service type |
| **Compute Optimizer** | `get_ebs_volume_recommendations()` | `get_compute_optimizer()` | EBS optimization recommendations | Separate error handling |
| **Compute Optimizer** | `get_lambda_function_recommendations()` | `get_compute_optimizer()` | Lambda memory recommendations | Independent of other services |
| **EC2** | `describe_instances()` | `get_services_resources()` | Instance inventory | Comprehensive resource cataloging |
| **EC2** | `describe_volumes()` | `get_services_resources()` | EBS volume inventory | Storage resource tracking |
| **EC2** | `describe_subnets()` | `get_services_resources()` | Network resource inventory | VPC and IP address tracking |
| **RDS** | `describe_db_instances()` | `get_services_resources()` | Database inventory | Engine and configuration details |
| **S3** | `list_buckets()` | `get_services_resources()` | Storage bucket inventory | Basic bucket information |
| **S3** | `put_object()` | `upload_to_s3()` | Data storage with KMS encryption | JSON serialization with datetime handling |
| **ELB v2** | `describe_load_balancers()` | `get_services_resources()` | Load balancer inventory | Network load distribution resources |
| **Auto Scaling** | `describe_auto_scaling_groups()` | `get_services_resources()` | Auto scaling group inventory | Compute scaling resources |
| **Lambda** | `list_functions()` | `get_services_resources()` | Serverless function inventory | Function metadata for optimization |
| **Support** | `describe_cases()` | `get_support_tickets()` | Support case history | Date range filtering with pagination |

## Data Processing Pipeline (Receiver)

| Stage | Function | Database Operations | Key Features |
|-------|----------|-------------------|-------------|
| **S3 Management** | `S3Manager` | File listing, reading, moving | Lightning-fast operations, processed file management |
| **Database Operations** | `DBManager` | Upsert with type casting | PostgreSQL type casting, parameter formatting |
| **Account Processing** | `load_account_data()` | Parent-child upsert pattern | Products, contacts, alternate contacts |
| **Cost Processing** | `load_cost_data()` | Hierarchical data loading | Reports → service costs → forecasts |
| **Security Processing** | `load_security_data()` | Multi-service parallel loading | 9 security services with ThreadPoolExecutor |
| **Config Processing** | `load_config_data()` | Report with resources | Config reports → non-compliant resources |
| **Inventory Processing** | `load_inventory_data()` | Instance-based relationships | Instances → applications → patches |
| **Parallel Processing** | `process_file_data()` | 14 concurrent loaders | ThreadPoolExecutor for optimal performance |

## Complete Data Processing Flow

### Sender Pipeline (sender.py)
| Step | Stage | Component | Description |
|------|-------|-----------|-------------|
| **Step 1** | **Permission Testing** | `AWSBoto3Permissions.test()` | Validates access to required services |
| **Step 2** | **Account Authentication** | `get_account_details()` | STS caller identity and account info |
| **Step 3** | **Parallel Data Collection** | 15 concurrent functions | Cost analysis with forecasting |
| | | | Security posture across 9 services |
| | | | Resource inventory and optimization |
| | | | Compliance and health monitoring |
| **Step 4** | **Data Serialization** | JSON encoding | Datetime handling |
| **Step 5** | **S3 Upload** | KMS-encrypted storage | File size tracking |
| **Step 6** | **Execution Modes** | Daily collection | Default mode |
| | | Historical processing | Date range processing |

### Receiver Pipeline (receiver.py)
| Step | Stage | Component | Description |
|------|-------|-----------|-------------|
| **Step 1** | **Permission Validation** | Aurora RDS-Data & S3 | Access verification |
| **Step 2** | **S3 File Discovery** | Automated scanning | `data/` prefix |
| **Step 3** | **Parallel Processing** | ThreadPoolExecutor | 14 concurrent database loaders |
| **Step 4** | **Database Operations** | Upsert operations | PostgreSQL type casting |
| | | Relationship management | Parent-child relationships |
| | | Key handling | Composite unique keys |
| **Step 5** | **File Management** | Automatic move | `loaded/` folder after processing |
| **Step 6** | **Statistics Tracking** | Counters | CREATED/UPDATED/SKIPPED/TOTAL |

### Data Flow Sequence
```
AWS APIs → sender.py → S3 (data/) → receiver.py → Aurora PostgreSQL → S3 (loaded/)
```

## Error Handling and Logging

### Sender Error Handling
- **Service-Level Logging**: `set_log()` with status tracking per data category
- **Graceful Degradation**: Optional services continue on failure
- **Timeout Configuration**: 5s connect, 10s read, 2 retry attempts
- **Date Range Validation**: Automatic date adjustment for service limits
- **Parallel Error Isolation**: ThreadPoolExecutor prevents cascade failures

### Receiver Error Handling
- **File Validation**: JSON structure and required attribute checking
- **Database Resilience**: Upsert operations with conflict resolution
- **Type Safety**: PostgreSQL type casting with validation
- **Transaction Isolation**: Per-file processing with rollback capability
- **Progress Tracking**: Real-time statistics and performance monitoring

### Logging Categories
- 🟢 **SUCCESS**: Successful operations
- 🟡 **FAIL**: Non-critical failures (optional services)
- 🔴 **ERROR**: Critical failures requiring attention
- 🔵 **INFO**: Informational messages
- ⏱️ **TIMING**: Performance metrics

## Security and Compliance

### Data Protection
- **KMS Encryption**: All S3 objects encrypted with customer-managed keys
- **Aurora Encryption**: Database-level encryption for stored data
- **Secrets Management**: AWS Secrets Manager for database credentials
- **Network Security**: VPC-based Aurora deployment

### Access Control
- **IAM Roles**: Least privilege access for sender and receiver
- **Service Permissions**: Granular API permissions per data category
- **Database Access**: RDS Data API with IAM authentication
- **S3 Bucket Policies**: Restricted access to data and loaded prefixes

### Audit and Compliance
- **Complete Audit Trail**: All API calls and database operations logged
- **Processing Metrics**: Detailed timing and success/failure tracking
- **Data Lineage**: S3 path tracking from collection to database
- **Error Forensics**: Comprehensive error logging with context

### Configuration Management
- **Environment Variables**: Secure configuration via environment
- **Regional Deployment**: Configurable AWS region support
- **Customer Segmentation**: Multi-tenant support with customer/partner tagging
- **Product Classification**: Flexible product and category assignment

## Performance Optimization

### Sender Optimizations
- **Parallel Collection**: ThreadPoolExecutor for concurrent API calls
- **Date Range Filtering**: Efficient data collection with time boundaries
- **Pagination Handling**: Automatic pagination for large result sets
- **Connection Pooling**: Boto3 client reuse and connection management

### Receiver Optimizations
- **Batch Processing**: Efficient upsert operations with composite keys
- **Type Casting**: PostgreSQL-native type conversion
- **Connection Reuse**: Single RDS Data API client for all operations
- **Memory Management**: Streaming JSON processing for large files

### Database Schema Features
- **Composite Unique Keys**: Efficient conflict resolution
- **JSONB Storage**: Native JSON support for complex data structures
- **Timestamp Handling**: Timezone-aware datetime processing
- **Relationship Management**: Parent-child data integrity