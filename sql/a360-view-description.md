# Multi-Account Observability - View Reference Documentation

## Overview
This document provides comprehensive attribute-level documentation for all 42 database views in the Multi-Account Observability solution. Each view enriches base table data with account metadata and product associations.

## Common Attributes
All views (except view_products) include these standard attributes:
- **account**: AWS account ID (12-digit identifier)
- **account_region**: AWS region or 'Global'
- **account_name**: Human-readable account name
- **account_type**: Account classification
- **account_category**: Account categorization
- **account_status**: Current account status
- **account_partner**: Partner organization name
- **account_customer**: Customer organization name
- **account_full**: Concatenated format "account_id-account_name"
- **project_product_name**: Associated product name

---

## 1. view_accounts
**Purpose**: Master account information with product associations  
**Base Table**: accounts  
**Use Case**: Central account registry, account management dashboards

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | VARCHAR(12) | AWS account ID |
| account_name | VARCHAR(255) | Account display name |
| account_email | VARCHAR(255) | Account root email |
| account_status | VARCHAR(50) | Status (ACTIVE, SUSPENDED) |
| account_arn | VARCHAR(255) | AWS account ARN |
| partner_name | TEXT | Partner organization |
| customer_name | TEXT | Customer organization |
| joined_method | VARCHAR(50) | How account joined organization |
| joined_timestamp | TIMESTAMP | When account joined |
| account_type | VARCHAR(50) | Account type classification |
| csp | VARCHAR(50) | Cloud service provider |
| region | TEXT | Primary region |
| category | TEXT | Account category |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 2. view_contact_info
**Purpose**: Account contact information  
**Base Table**: contact_info  
**Use Case**: Contact management, communication workflows

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| address_line1 | VARCHAR(255) | Street address line 1 |
| address_line2 | VARCHAR(255) | Street address line 2 |
| address_line3 | VARCHAR(255) | Street address line 3 |
| city | VARCHAR(100) | City name |
| country_code | VARCHAR(2) | ISO country code |
| postal_code | VARCHAR(20) | Postal/ZIP code |
| state_or_region | VARCHAR(100) | State or region |
| company_name | VARCHAR(255) | Company name |
| phone_number | VARCHAR(20) | Contact phone |
| website_url | VARCHAR(255) | Company website |
| full_name | VARCHAR(255) | Contact person name |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 3. view_alternate_contacts
**Purpose**: Secondary contact persons for accounts  
**Base Table**: alternate_contacts  
**Use Case**: Escalation contacts, multi-stakeholder management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| contact_type | VARCHAR(50) | Type (BILLING, OPERATIONS, SECURITY) |
| full_name | VARCHAR(255) | Contact person name |
| title | VARCHAR(255) | Job title |
| email | VARCHAR(255) | Contact email |
| phone_number | VARCHAR(20) | Contact phone |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 4. view_acct_serv
**Purpose**: AWS services enabled and used per account  
**Base Table**: services  
**Use Case**: Service adoption tracking, usage analysis

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| service | VARCHAR(255) | AWS service name |
| date_from | DATE | Period start date |
| date_to | DATE | Period end date |
| cost | DECIMAL(20,10) | Service cost |
| currency | VARCHAR(3) | Currency code (USD) |
| utilization | DECIMAL(20,10) | Service utilization metric |
| utilization_unit | VARCHAR(100) | Unit of utilization |
| usage_types | TEXT | Comma-separated usage types |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 5. view_acct_cost_rep
**Purpose**: Cost reports with period analysis  
**Base Table**: cost_reports  
**Use Case**: Financial reporting, cost trend analysis

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| current_period_cost | NUMERIC(20,10) | Current period total cost |
| previous_period_cost | NUMERIC(20,10) | Previous period total cost |
| cost_difference | NUMERIC(20,10) | Absolute cost change |
| cost_difference_percentage | NUMERIC(20,10) | Percentage cost change |
| potential_monthly_savings | NUMERIC(20,10) | Identified savings opportunities |
| anomalies_detected | INTEGER | Number of cost anomalies |
| saving_opportunities_count | INTEGER | Count of savings recommendations |
| period_start | DATE | Report period start |
| period_end | DATE | Report period end |
| period_granularity | ENUM | MONTHLY, WEEKLY, or DAILY |
| created_at | TIMESTAMP | Record creation time |
| date_from | DATE | Alias for period_start |
| date_to | DATE | Alias for period_end |

---

## 6. view_acct_serv_cost
**Purpose**: Service-level cost breakdown  
**Base Table**: service_costs  
**Use Case**: Detailed service cost analysis, chargeback

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| cost_report_id | INTEGER | Foreign key to cost_reports |
| service_name | VARCHAR(255) | AWS service name |
| cost | NUMERIC(20,10) | Service cost for period |
| created_at | TIMESTAMP | Record creation time |
| date_from | DATE | Period start (from cost_reports) |
| date_to | DATE | Period end (from cost_reports) |

---

## 7. view_acct_cost_rep_forecast
**Purpose**: Cost forecasting and predictions  
**Base Table**: cost_forecasts  
**Use Case**: Budget planning, cost projections

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| cost_report_id | INTEGER | Foreign key to cost_reports |
| period_start | DATE | Forecast period start |
| period_end | DATE | Forecast period end |
| amount | NUMERIC(20,10) | Forecasted cost amount |
| prediction_interval_lower_bound | NUMERIC(20,10) | Lower confidence bound |
| prediction_interval_upper_bound | NUMERIC(20,10) | Upper confidence bound |
| created_at | TIMESTAMP | Record creation time |
| date_from | DATE | Report period start (from cost_reports) |
| date_to | DATE | Report period end (from cost_reports) |

---

## 8. view_acct_security
**Purpose**: Security findings summary by service  
**Base Table**: security  
**Use Case**: Security posture monitoring, compliance dashboards

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| service | VARCHAR(255) | Security service (SecurityHub, GuardDuty) |
| total_findings | INTEGER | Total security findings |
| critical_count | INTEGER | Critical severity findings |
| high_count | INTEGER | High severity findings |
| medium_count | INTEGER | Medium severity findings |
| low_count | INTEGER | Low severity findings |
| informational_count | INTEGER | Informational findings |
| open_findings | INTEGER | Currently open findings |
| resolved_findings | INTEGER | Resolved findings |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 9. view_acct_security_findings_details
**Purpose**: Detailed security finding records  
**Base Table**: findings  
**Use Case**: Security investigation, remediation tracking

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| security_id | INTEGER | Foreign key to security |
| finding_id | VARCHAR(255) | Unique finding identifier |
| service | VARCHAR(255) | Source service |
| title | TEXT | Finding title |
| description | TEXT | Detailed description |
| severity | VARCHAR(50) | CRITICAL, HIGH, MEDIUM, LOW |
| status | VARCHAR(50) | Finding status |
| resource_type | VARCHAR(255) | Affected resource type |
| resource_id | VARCHAR(255) | Affected resource ID |
| created_at | TIMESTAMP | Finding creation time |
| updated_at | TIMESTAMP | Finding update time |
| recommendation | TEXT | Remediation recommendation |
| compliance_status | VARCHAR(50) | Compliance check status |
| region | VARCHAR(50) | AWS region |
| workflow_state | VARCHAR(50) | Workflow status |
| record_state | VARCHAR(50) | Record state |
| product_name | VARCHAR(255) | Security product name |
| company_name | VARCHAR(255) | Security vendor |
| product_arn | VARCHAR(255) | Product ARN |
| generator_id | VARCHAR(255) | Finding generator ID |
| generator | VARCHAR(255) | Finding generator |

---

## 10. view_products
**Purpose**: Product catalog  
**Base Table**: products  
**Use Case**: Product management, portfolio tracking

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(255) | Product name |
| owner | VARCHAR(255) | Product owner |
| position | VARCHAR(255) | Product position/priority |
| description | TEXT | Product description |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |
| project_product_name | VARCHAR(255) | Same as name |

**Note**: This view has NULL values for all account-related fields.


## 11. view_product_acct
**Purpose**: Product-account relationship mapping  
**Base Table**: product_accounts  
**Use Case**: Track product deployments across accounts

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| product_id | INTEGER | Foreign key to products |
| account_id | INTEGER | Foreign key to accounts |
| created_at | TIMESTAMP | Relationship creation time |
| updated_at | TIMESTAMP | Relationship update time |

---

## 12. view_acct_products
**Purpose**: Products with account associations  
**Base Table**: products (joined with accounts)  
**Use Case**: Account-centric product view

### Attributes
Same as view_products plus all common account attributes.

---

## 13. view_acct_logs
**Purpose**: Account activity and status logs  
**Base Table**: logs  
**Use Case**: Audit trail, data collection monitoring

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| date_created | TIMESTAMP | Log entry timestamp |
| account_status | VARCHAR(50) | Account data collection status |
| cost_status | VARCHAR(50) | Cost data collection status |
| service_status | VARCHAR(50) | Service data collection status |
| security_status | VARCHAR(50) | Security data collection status |
| config_status | VARCHAR(50) | Config data collection status |
| inventory_status | VARCHAR(50) | Inventory data collection status |
| marketplace_status | VARCHAR(50) | Marketplace data collection status |
| trusted_advisor_status | VARCHAR(50) | TA data collection status |
| health_status | VARCHAR(50) | Health data collection status |
| application_status | VARCHAR(50) | Application data collection status |
| resilience_hub_status | VARCHAR(50) | Resilience Hub data collection status |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 14. view_acct_log_messages
**Purpose**: Detailed log messages  
**Base Table**: log_messages  
**Use Case**: Troubleshooting, error tracking

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| log_id | INTEGER | Foreign key to logs |
| message | TEXT | Log message content |
| message_type | TEXT | Message type/category |
| created_at | TIMESTAMP | Message creation time |

---

## 15. view_config_reports
**Purpose**: AWS Config compliance reports  
**Base Table**: config_reports  
**Use Case**: Compliance monitoring, governance

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| date_from | DATE | Report period start |
| date_to | DATE | Report period end |
| compliance_score | NUMERIC(5,2) | Overall compliance score (0-100) |
| total_rules | INTEGER | Total Config rules evaluated |
| compliant_rules | INTEGER | Rules in compliance |
| non_compliant_rules | INTEGER | Rules not in compliance |
| curr_non_compliant | INTEGER | Current non-compliant resources |
| curr_compliant | INTEGER | Current compliant resources |
| created_at | TIMESTAMP | Record creation time |

---

## 16. view_non_compliant_resources
**Purpose**: Resources failing compliance checks  
**Base Table**: non_compliant_resources  
**Use Case**: Compliance remediation, audit evidence

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| config_report_id | INTEGER | Foreign key to config_reports |
| resource_type | VARCHAR(255) | AWS resource type |
| resource_id | VARCHAR(255) | Resource identifier |
| compliance_type | VARCHAR(50) | Compliance check type |
| rule_name | VARCHAR(255) | Config rule name |
| created_at | TIMESTAMP | Record creation time |
| annotation | TEXT | Compliance annotation |
| evaluation_mode | TEXT | Evaluation mode |
| conformance_pack | TEXT | Conformance pack name |
| status | VARCHAR(255) | Remediation status |

---

## 17. view_service_resources
**Purpose**: Service resource inventory  
**Base Table**: service_resources  
**Use Case**: Resource inventory, capacity planning

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| service_name | VARCHAR(255) | AWS service name |
| resource_type | VARCHAR(255) | Resource type |
| resource_id | VARCHAR(255) | Resource identifier |
| resource_name | VARCHAR(255) | Resource name |
| region | VARCHAR(50) | AWS region |
| availability_zone | VARCHAR(50) | Availability zone |
| state | VARCHAR(50) | Resource state |
| instance_type | VARCHAR(50) | EC2 instance type |
| vpc_id | VARCHAR(255) | VPC identifier |
| engine | VARCHAR(100) | Database engine |
| instance_class | VARCHAR(100) | RDS instance class |
| multi_az | BOOLEAN | Multi-AZ deployment |
| size_gb | INTEGER | Storage size in GB |
| volume_type | VARCHAR(50) | EBS volume type |
| creation_date | TIMESTAMP | Resource creation date |
| type | VARCHAR(100) | Resource type classification |
| scheme | VARCHAR(50) | Load balancer scheme |
| instance_count | INTEGER | Instance count |
| min_size | INTEGER | Auto Scaling min size |
| max_size | INTEGER | Auto Scaling max size |
| available_ip_count | INTEGER | Available IP addresses |
| created_at | TIMESTAMP | Record creation time |

---

## 18. view_service_resources_summary
**Purpose**: Aggregated resource counts  
**Base Table**: service_resources (aggregated)  
**Use Case**: Resource utilization dashboards

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| account_id | VARCHAR(12) | AWS account ID |
| account_region | TEXT | Account region |
| account_name | VARCHAR(255) | Account name |
| account_type | VARCHAR(50) | Account type |
| account_category | TEXT | Account category |
| account_status | VARCHAR(50) | Account status |
| account_partner | TEXT | Partner name |
| account_customer | TEXT | Customer name |
| service_name | VARCHAR(255) | AWS service name |
| resource_type | VARCHAR(255) | Resource type |
| resource_region | VARCHAR(50) | Resource region |
| availability_zone | VARCHAR(50) | Availability zone |
| resource_count | BIGINT | Total resource count |
| active_resources | BIGINT | Active/running resources |
| inactive_resources | BIGINT | Stopped/inactive resources |

---

## 19. view_compute_optimizer
**Purpose**: AWS Compute Optimizer recommendations  
**Base Table**: compute_optimizer  
**Use Case**: Cost optimization, rightsizing

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| resource_type | VARCHAR(50) | Resource type (EC2, Lambda, EBS) |
| resource_arn | VARCHAR(255) | Resource ARN |
| resource_name | VARCHAR(255) | Resource name |
| finding | VARCHAR(50) | Optimization finding |
| current_instance_type | VARCHAR(50) | Current EC2 instance type |
| current_memory_size | INTEGER | Current Lambda memory (MB) |
| current_volume_type | VARCHAR(50) | Current EBS volume type |
| current_volume_size | INTEGER | Current volume size (GB) |
| recommended_instance_type | VARCHAR(50) | Recommended instance type |
| recommended_memory_size | INTEGER | Recommended memory (MB) |
| recommended_volume_type | VARCHAR(50) | Recommended volume type |
| recommended_volume_size | INTEGER | Recommended volume size (GB) |
| savings_opportunity_percentage | DECIMAL(5,2) | Potential savings percentage |
| estimated_monthly_savings_usd | DECIMAL(10,2) | Estimated monthly savings |
| performance_risk | DECIMAL(3,2) | Performance risk score |
| cpu_utilization_max | DECIMAL(5,2) | Max CPU utilization |
| memory_utilization_avg | DECIMAL(5,2) | Average memory utilization |
| migration_effort | VARCHAR(50) | Migration effort level |
| created_at | TIMESTAMP | Record creation time |

---

## 20. view_guard_duty_findings
**Purpose**: Amazon GuardDuty threat findings  
**Base Table**: guard_duty_findings  
**Use Case**: Threat detection, security monitoring

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| detector_id | VARCHAR(255) | GuardDuty detector ID |
| finding_type | VARCHAR(255) | Type of threat detected |
| severity | NUMERIC(3,1) | Severity score (0-10) |
| title | TEXT | Finding title |
| description | TEXT | Finding description |
| confidence | NUMERIC(3,1) | Confidence score (0-10) |
| region | VARCHAR(50) | AWS region |
| created_at | TIMESTAMP | Finding creation time |
| updated_at | TIMESTAMP | Finding update time |


## 21. view_kms_keys
**Purpose**: AWS KMS encryption key inventory  
**Base Table**: kms_keys  
**Use Case**: Encryption key management, compliance

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| key_id | VARCHAR(255) | KMS key ID |
| arn | VARCHAR(255) | KMS key ARN |
| description | TEXT | Key description |
| key_usage | VARCHAR(50) | Key usage (ENCRYPT_DECRYPT) |
| key_state | VARCHAR(50) | Key state (Enabled, Disabled) |
| creation_date | TIMESTAMP | Key creation date |
| enabled | BOOLEAN | Key enabled status |
| key_rotation_enabled | BOOLEAN | Automatic rotation enabled |
| created_at | TIMESTAMP | Record creation time |

---

## 22. view_waf_rules
**Purpose**: AWS WAF web ACL summary  
**Base Table**: waf_rules  
**Use Case**: Web application firewall management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| name | VARCHAR(255) | Web ACL name |
| waf_id | VARCHAR(255) | WAF ID |
| arn | VARCHAR(255) | Web ACL ARN |
| scope | VARCHAR(50) | REGIONAL or CLOUDFRONT |
| description | TEXT | Web ACL description |
| default_action | JSONB | Default action (ALLOW/BLOCK) |
| rules_count | INTEGER | Number of rules |
| logging_enabled | BOOLEAN | Logging enabled status |
| geo_blocking_enabled | BOOLEAN | Geo-blocking enabled |
| blocked_countries | TEXT | Blocked country codes |
| created_at | TIMESTAMP | Record creation time |

---

## 23. view_waf_rules_detailed
**Purpose**: Detailed WAF rule configurations  
**Base Table**: waf_rules_detailed  
**Use Case**: Advanced WAF rule analysis, compliance

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| web_acl_name | VARCHAR(255) | Web ACL name |
| rule_name | VARCHAR(255) | Rule name |
| priority | INTEGER | Rule priority |
| action | TEXT | Rule action |
| statement_type | VARCHAR(100) | Statement type |
| is_managed_rule | BOOLEAN | AWS managed rule |
| is_custom_rule | BOOLEAN | Custom rule |
| rate_limit | BOOLEAN | Rate limiting enabled |
| logging_enabled | BOOLEAN | Logging enabled |
| geo_blocking | BOOLEAN | Geo-blocking enabled |
| sql_injection | BOOLEAN | SQL injection protection |
| sample_request_enabled | BOOLEAN | Sample requests enabled |
| cloudwatch_enabled | BOOLEAN | CloudWatch metrics enabled |
| has_xss_protection | BOOLEAN | XSS protection enabled |
| waf_version | VARCHAR(10) | WAF version (v1/v2) |
| is_compliant | BOOLEAN | Compliance status |
| scope | VARCHAR(20) | REGIONAL or CLOUDFRONT |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 24. view_cloudtrail_logs
**Purpose**: AWS CloudTrail configuration  
**Base Table**: cloudtrail_logs  
**Use Case**: API activity auditing, compliance

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| name | VARCHAR(255) | Trail name |
| arn | VARCHAR(255) | Trail ARN |
| is_logging | BOOLEAN | Currently logging |
| is_multi_region | BOOLEAN | Multi-region trail |
| s3_bucket | VARCHAR(255) | S3 bucket for logs |
| kms_key_id | VARCHAR(255) | KMS key for encryption |
| log_file_validation | BOOLEAN | Log file validation enabled |
| latest_delivery_time | TIMESTAMP | Last log delivery time |
| created_at | TIMESTAMP | Record creation time |

---

## 25. view_secrets_manager_secrets
**Purpose**: AWS Secrets Manager inventory  
**Base Table**: secrets_manager_secrets  
**Use Case**: Secrets lifecycle management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| name | VARCHAR(255) | Secret name |
| arn | VARCHAR(255) | Secret ARN |
| description | TEXT | Secret description |
| created_date | TIMESTAMP | Secret creation date |
| last_changed_date | TIMESTAMP | Last modification date |
| rotation_enabled | BOOLEAN | Automatic rotation enabled |
| created_at | TIMESTAMP | Record creation time |

---

## 26. view_certificates
**Purpose**: AWS Certificate Manager inventory  
**Base Table**: certificates  
**Use Case**: SSL/TLS certificate management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| arn | VARCHAR(255) | Certificate ARN |
| domain_name | VARCHAR(255) | Primary domain name |
| status | VARCHAR(50) | Certificate status |
| type | VARCHAR(50) | Certificate type (AMAZON_ISSUED, IMPORTED) |
| not_after | TIMESTAMP | Expiration date |
| created_at | TIMESTAMP | Record creation time |

---

## 27. view_inspector_findings
**Purpose**: Amazon Inspector vulnerability findings  
**Base Table**: inspector_findings  
**Use Case**: Vulnerability assessment, remediation

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| finding_arn | VARCHAR(255) | Finding ARN |
| severity | VARCHAR(50) | Severity level |
| status | VARCHAR(50) | Finding status |
| type | VARCHAR(100) | Finding type |
| title | TEXT | Finding title |
| description | TEXT | Finding description |
| first_observed_at | TIMESTAMP | First observation time |
| created_at | TIMESTAMP | Record creation time |

---

## 28. view_inventory_instances
**Purpose**: EC2 instance inventory from Systems Manager  
**Base Table**: inventory_instances  
**Use Case**: Instance management, patch compliance

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| instance_id | VARCHAR(255) | EC2 instance ID |
| instance_type | VARCHAR(50) | Instance type |
| platform | VARCHAR(50) | Operating system platform |
| ip_address | VARCHAR(45) | IP address |
| computer_name | VARCHAR(255) | Computer hostname |
| ping_status | VARCHAR(50) | SSM agent ping status |
| last_ping_date_time | TIMESTAMP | Last ping time |
| agent_version | VARCHAR(50) | SSM agent version |
| created_at | TIMESTAMP | Record creation time |
| platform_type | VARCHAR(255) | Platform type |
| platform_version | VARCHAR(50) | OS version |
| is_latest_version | BOOLEAN | Latest agent version |
| association_status | VARCHAR(255) | Association status |
| association_execution_date | TIMESTAMP | Last association execution |
| association_success_date | TIMESTAMP | Last successful association |

---

## 29. view_inventory_applications
**Purpose**: Applications installed on instances  
**Base Table**: inventory_applications  
**Use Case**: Software inventory, license management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| instance_id | INTEGER | Foreign key to inventory_instances |
| name | VARCHAR(255) | Application name |
| version | VARCHAR(100) | Application version |
| publisher | VARCHAR(255) | Software publisher |
| install_time | TIMESTAMP | Installation time |
| created_at | TIMESTAMP | Record creation time |

---

## 30. view_inventory_patches
**Purpose**: Patch compliance status  
**Base Table**: inventory_patches  
**Use Case**: Patch management, compliance reporting

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| instance_id | INTEGER | Foreign key to inventory_instances |
| title | VARCHAR(255) | Patch title |
| classification | VARCHAR(100) | Patch classification |
| severity | VARCHAR(50) | Patch severity |
| state | VARCHAR(50) | Patch state (Installed, Missing) |
| installed_time | TIMESTAMP | Installation time |
| created_at | TIMESTAMP | Record creation time |
| instance_name | VARCHAR(255) | Instance ID (from join) |
| instance_type | VARCHAR(50) | Instance type (from join) |


## 31. view_marketplace_usage
**Purpose**: AWS Marketplace subscription usage  
**Base Table**: marketplace_usage  
**Use Case**: Marketplace cost tracking, subscription management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| product_code | VARCHAR(255) | Marketplace product code |
| product_name | VARCHAR(255) | Product name |
| cost_consumed | NUMERIC(20,10) | Cost consumed |
| currency | VARCHAR(3) | Currency code |
| period_start | DATE | Usage period start |
| period_end | DATE | Usage period end |
| status | VARCHAR(50) | Subscription status |
| created_at | TIMESTAMP | Record creation time |

---

## 32. view_trusted_advisor_checks
**Purpose**: AWS Trusted Advisor recommendations  
**Base Table**: trusted_advisor_checks  
**Use Case**: Best practices, optimization recommendations

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| check_name | VARCHAR(255) | Check name |
| category | VARCHAR(100) | Category (Cost, Security, Performance) |
| severity | VARCHAR(50) | Severity level |
| recommendation | TEXT | Recommendation text |
| affected_resources_count | INTEGER | Number of affected resources |
| potential_savings | NUMERIC(20,10) | Potential cost savings |
| timestamp | TIMESTAMP | Check execution time |
| created_at | TIMESTAMP | Record creation time |

---

## 33. view_health_events
**Purpose**: AWS Health service events  
**Base Table**: health_events  
**Use Case**: Service health monitoring, incident tracking

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| arn | VARCHAR(255) | Event ARN |
| service | VARCHAR(100) | Affected AWS service |
| event_type_code | VARCHAR(255) | Event type code |
| region | VARCHAR(50) | Affected region |
| start_time | TIMESTAMP | Event start time |
| end_time | TIMESTAMP | Event end time |
| status_code | VARCHAR(50) | Event status |
| created_at | TIMESTAMP | Record creation time |

---

## 34. view_application_signals
**Purpose**: CloudWatch Application Signals  
**Base Table**: application_signals  
**Use Case**: Application performance monitoring

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| service_name | VARCHAR(255) | Application service name |
| namespace | VARCHAR(255) | CloudWatch namespace |
| key_attributes | JSONB | Key-value attributes |
| created_at | TIMESTAMP | Record creation time |

---

## 35. view_resilience_hub_apps
**Purpose**: AWS Resilience Hub application assessments  
**Base Table**: resilience_hub_apps  
**Use Case**: Application resilience assessment

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| app_arn | VARCHAR(255) | Application ARN |
| name | VARCHAR(255) | Application name |
| compliance_status | VARCHAR(50) | Compliance status |
| resiliency_score | NUMERIC(5,2) | Resiliency score (0-100) |
| status | VARCHAR(50) | Application status |
| cost | NUMERIC(20,10) | Estimated cost |
| created_at | TIMESTAMP | Record creation time |
| description | TEXT | Application description |
| creation_time | TIMESTAMP | Application creation time |
| last_assessment_time | TIMESTAMP | Last assessment time |
| rpo | INTEGER | Recovery Point Objective (seconds) |
| rto | INTEGER | Recovery Time Objective (seconds) |
| last_drill | TIMESTAMP | Last resilience drill time |

---

## 36. view_summary
**Purpose**: Comprehensive account summary with all metrics  
**Base Table**: Aggregated from multiple tables  
**Use Case**: Executive dashboards, account overview

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| account_id | INTEGER | Account internal ID |
| account | VARCHAR(12) | AWS account ID |
| account_region | TEXT | Account region |
| account_name | VARCHAR(255) | Account name |
| account_type | VARCHAR(50) | Account type |
| account_category | TEXT | Account category |
| account_status | VARCHAR(50) | Account status |
| account_partner | TEXT | Partner name |
| account_customer | TEXT | Customer name |
| account_full | TEXT | Concatenated account identifier |
| account_csp | VARCHAR(50) | Cloud service provider |
| number_of_products | BIGINT | Count of associated products |
| period_granularity | ENUM | Report granularity |
| date_from | DATE | Period start |
| date_to | DATE | Period end |
| current_period_cost | NUMERIC | Current period cost |
| previous_period_cost | NUMERIC | Previous period cost |
| cost_difference | NUMERIC | Cost change |
| cost_difference_percentage | NUMERIC | Cost change percentage |
| potential_savings | NUMERIC | Potential savings |
| service_count | BIGINT | Number of service records |
| unique_services | BIGINT | Count of unique services |
| total_service_cost | NUMERIC | Total service costs |
| services_used | TEXT | Comma-separated service list |
| total_findings | BIGINT | Total security findings |
| open_findings | BIGINT | Open security findings |
| resolved_findings | BIGINT | Resolved security findings |
| critical_findings | BIGINT | Critical severity findings |
| high_findings | BIGINT | High severity findings |
| medium_findings | BIGINT | Medium severity findings |
| low_findings | BIGINT | Low severity findings |
| security_resolution_rate | NUMERIC | Finding resolution rate |
| account_email | VARCHAR(255) | Account email |
| joined_method | VARCHAR(50) | Join method |
| joined_timestamp | TIMESTAMP | Join timestamp |
| account_age_days | NUMERIC | Account age in days |

---

## 37. view_acct_summary
**Purpose**: Account summary with health scores  
**Base Table**: Aggregated from accounts, cost_reports, security, inventory  
**Use Case**: Account health monitoring, quick overview

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| All account fields | Various | All fields from accounts table |
| latest_cost | NUMERIC | Most recent period cost |
| cost_trend_percentage | NUMERIC | Cost trend percentage |
| savings_opportunity | NUMERIC | Identified savings |
| security_findings | BIGINT | Total security findings |
| critical_findings | BIGINT | Critical findings |
| high_findings | BIGINT | High findings |
| instance_count | BIGINT | Total instance count |
| running_instances | BIGINT | Running instance count |
| security_health_score | INTEGER | Health score (1-5, 5=best) |

---

## 38. view_product_summary
**Purpose**: Product-level summary with metrics  
**Base Table**: Aggregated from products, accounts, cost_reports, services, security  
**Use Case**: Product performance tracking, portfolio management

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| account_id | INTEGER | Account internal ID |
| account | VARCHAR(12) | AWS account ID |
| account_region | TEXT | Account region |
| account_name | VARCHAR(255) | Account name |
| account_full | TEXT | Concatenated identifier |
| project_product_name | VARCHAR(255) | Product name |
| account_csp | VARCHAR(50) | Cloud service provider |
| account_type | VARCHAR(50) | Account type |
| account_category | TEXT | Account category |
| account_status | VARCHAR(50) | Account status |
| account_partner | TEXT | Partner name |
| account_customer | TEXT | Customer name |
| product_id | INTEGER | Product ID |
| product_owner | VARCHAR(255) | Product owner |
| product_position | VARCHAR(255) | Product position |
| product_description | TEXT | Product description |
| period_granularity | ENUM | Report granularity |
| date_from | DATE | Period start |
| date_to | DATE | Period end |
| current_period_cost | NUMERIC | Current cost |
| previous_period_cost | NUMERIC | Previous cost |
| cost_difference | NUMERIC | Cost change |
| cost_difference_percentage | NUMERIC | Cost change percentage |
| potential_savings | NUMERIC | Savings opportunities |
| service_count | BIGINT | Service count |
| unique_services | BIGINT | Unique services |
| total_service_cost | NUMERIC | Total service cost |
| services_used | TEXT | Services list |
| total_findings | BIGINT | Security findings |
| open_findings | BIGINT | Open findings |
| resolved_findings | BIGINT | Resolved findings |
| critical_findings | BIGINT | Critical findings |
| high_findings | BIGINT | High findings |
| medium_findings | BIGINT | Medium findings |
| low_findings | BIGINT | Low findings |
| security_resolution_rate | NUMERIC | Resolution rate |
| account_email | VARCHAR(255) | Account email |
| joined_method | VARCHAR(50) | Join method |
| joined_timestamp | TIMESTAMP | Join timestamp |
| account_age_days | NUMERIC | Account age in days |

---

## 39. view_acct_security_findings_summary
**Purpose**: Security findings aggregated summary  
**Base Table**: security (with calculated fields)  
**Use Case**: Security metrics, KPI dashboards

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| All common account attributes | Various | Standard account fields |
| service | VARCHAR(255) | Security service |
| total_findings | INTEGER | Total findings |
| critical_count | INTEGER | Critical findings |
| high_count | INTEGER | High findings |
| medium_count | INTEGER | Medium findings |
| low_count | INTEGER | Informational findings |
| informational_count | INTEGER | Informational findings |
| open_findings | INTEGER | Open findings |
| resolved_findings | INTEGER | Resolved findings |
| suppressed_count | INTEGER | Suppressed (calculated as 0) |
| in_progress_count | INTEGER | In progress (calculated as 0) |
| active_issues | INTEGER | Active issues (same as open) |
| region_finding | VARCHAR | Region (calculated as 'N/A') |
| resolved_count | INTEGER | Resolved count |
| severity | VARCHAR | Highest severity level |
| resolution_rate_percent | NUMERIC | Resolution rate percentage |
| risk_level | VARCHAR | Risk level classification |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 40. view_compute_optimizer_summary
**Purpose**: Aggregated Compute Optimizer recommendations  
**Base Table**: compute_optimizer (aggregated)  
**Use Case**: Cost optimization reporting, executive summaries

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| All common account attributes | Various | Standard account fields |
| resource_type | VARCHAR(50) | Resource type |
| finding | VARCHAR(50) | Optimization finding |
| resource_count | BIGINT | Count of resources |
| total_monthly_savings | NUMERIC | Total potential savings |
| avg_savings_percentage | NUMERIC | Average savings percentage |
| avg_performance_risk | NUMERIC | Average performance risk |
| not_optimized_count | BIGINT | Not optimized resources |
| savings_opportunities | BIGINT | Count of savings opportunities |

---

## 41. view_acct_support_tickets
**Purpose**: AWS Support ticket tracking  
**Base Table**: support_tickets  
**Use Case**: Support case management, SLA tracking

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| case_id | VARCHAR(255) | Support case ID |
| display_id | VARCHAR(50) | Display case ID |
| subject | TEXT | Case subject |
| status | VARCHAR(50) | Case status |
| severity_code | VARCHAR(50) | Severity level |
| service_code | VARCHAR(255) | Affected service |
| category_code | VARCHAR(50) | Case category |
| time_created | TIMESTAMP | Case creation time |
| submitted_by | VARCHAR(255) | Submitter email |
| language | VARCHAR(10) | Case language |
| date_from | DATE | Report period start |
| date_to | DATE | Report period end |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## 42. view_ri_sp_daily_savings
**Purpose**: Reserved Instance and Savings Plan daily savings tracking  
**Base Table**: ri_sp_daily_savings  
**Use Case**: Cost savings tracking, RI/SP utilization

### Attributes
| Attribute | Type | Description |
|-----------|------|-------------|
| id | SERIAL | Primary key |
| account_id | INTEGER | Foreign key to accounts |
| date_from | DATE | Period start |
| date_to | DATE | Period end |
| reservation_type | VARCHAR(50) | RI or Savings Plan |
| subscription_id | VARCHAR(255) | Subscription identifier |
| offering_id | VARCHAR(255) | Offering ID |
| savings_plan_arn | VARCHAR(255) | Savings Plan ARN |
| service | VARCHAR(100) | AWS service |
| instance_type | VARCHAR(100) | Instance type |
| instance_count | INTEGER | Instance count |
| instance_family | VARCHAR(100) | Instance family |
| instance_tenancy | VARCHAR(50) | Tenancy type |
| offering_class | VARCHAR(50) | Offering class |
| product_types | TEXT | Product types |
| region | VARCHAR(50) | AWS region |
| utilization_percentage | NUMERIC(5,2) | Utilization percentage |
| on_demand_cost | NUMERIC(12,2) | On-Demand cost |
| reservation_cost | NUMERIC(12,2) | RI/SP cost |
| net_savings | NUMERIC(12,2) | Net savings |
| commitment | NUMERIC(12,2) | Commitment amount |
| upfront_cost | NUMERIC(12,2) | Upfront payment |
| recurring_cost | NUMERIC(12,2) | Recurring cost |
| recurring_frequency | VARCHAR(20) | Payment frequency |
| usage_price | NUMERIC(12,2) | Usage price |
| currency | VARCHAR(10) | Currency code |
| start_date | TIMESTAMP | Subscription start |
| end_date | TIMESTAMP | Subscription end |
| returnable_until | TIMESTAMP | Return deadline |
| duration_seconds | INTEGER | Duration in seconds |
| offering_type | VARCHAR(50) | Offering type |
| state | VARCHAR(50) | Subscription state |
| description | TEXT | Description |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Record update time |

---

## Appendix: Query Examples

### Example 1: Get account cost summary
```sql
SELECT 
    account_full,
    current_period_cost,
    cost_difference_percentage,
    potential_savings
FROM view_summary
WHERE period_granularity = 'MONTHLY'
ORDER BY current_period_cost DESC;
```

### Example 2: Find critical security findings
```sql
SELECT 
    account_name,
    service,
    title,
    severity,
    resource_type
FROM view_acct_security_findings_details
WHERE severity = 'CRITICAL' 
    AND status = 'ACTIVE'
ORDER BY created_at DESC;
```

### Example 3: Identify cost optimization opportunities
```sql
SELECT 
    account_name,
    resource_type,
    finding,
    estimated_monthly_savings_usd,
    performance_risk
FROM view_compute_optimizer
WHERE finding = 'NotOptimized'
    AND estimated_monthly_savings_usd > 10
ORDER BY estimated_monthly_savings_usd DESC;
```

### Example 4: Track patch compliance
```sql
SELECT 
    account_name,
    instance_name,
    COUNT(*) as missing_patches,
    COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical_patches
FROM view_inventory_patches
WHERE state = 'Missing'
GROUP BY account_name, instance_name
ORDER BY critical_patches DESC;
```

---

## Document Information
- **Version**: 2.0
- **Last Updated**: 2025
- **Total Views**: 42
- **Database**: PostgreSQL (Aurora Serverless v2)

