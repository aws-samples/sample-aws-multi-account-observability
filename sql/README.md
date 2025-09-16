# SQL Schema Documentation

This folder contains the SQL files for setting up the Aurora PostgreSQL database schema for the AWS Multi-Account Observability Platform.

## core-schema.sql
**Purpose**: Creates the complete database schema with 30+ tables for storing comprehensive AWS observability data.

**Core Account Management**:
- **accounts**: Main account table with partner/customer support
- **contact_info**: Account contact information
- **alternate_contacts**: Billing, operations, security contacts
- **products**: Product/project management
- **product_accounts**: Many-to-many account-product relationships

**Cost & Financial Analytics**:
- **cost_reports**: Period-based cost analysis with forecasting
- **service_costs**: Top service costs breakdown
- **cost_forecasts**: Future cost predictions with confidence intervals
- **services**: Detailed service usage and costs by usage type

**Comprehensive Security Coverage**:
- **security**: Security Hub findings summary by service
- **findings**: Detailed security findings with remediation
- **guard_duty_findings**: GuardDuty threat detection
- **kms_keys**: KMS key inventory and rotation status
- **waf_rules**: WAF configurations and compliance
- **waf_rules_detailed**: Detailed WAF rule analysis with compliance checking
- **cloudtrail_logs**: CloudTrail logging status
- **secrets_manager_secrets**: Secrets inventory
- **certificates**: ACM certificate management
- **inspector_findings**: Inspector vulnerability findings

**Infrastructure & Inventory**:
- **inventory_instances**: EC2 instances via Systems Manager
- **inventory_applications**: Installed applications
- **inventory_patches**: Patch compliance status
- **service_resources**: Multi-service resource inventory (EC2, RDS, S3, ELB, etc.)
- **config_inventory**: Configuration-based resource tracking

**Optimization & Compliance**:
- **compute_optimizer**: EC2, EBS, Lambda optimization recommendations
- **config_reports**: Config compliance reports
- **non_compliant_resources**: Non-compliant resources tracking
- **marketplace_usage**: Marketplace product usage
- **trusted_advisor_checks**: Trusted Advisor recommendations

**Monitoring & Operations**:
- **health_events**: AWS Health events
- **application_signals**: Application performance signals
- **resilience_hub_apps**: Resilience Hub assessments
- **logs**: Processing status and health scores
- **log_messages**: Detailed processing messages

**Enhanced Features**:
- **Multi-tenant Support**: Partner/customer identification
- **Advanced Indexing**: 50+ optimized indexes for analytics queries
- **JSONB Support**: Flexible configuration storage
- **Custom Types**: `period_granularity_type` enum
- **Referential Integrity**: Comprehensive foreign key relationships

## core-view-schema.sql
**Purpose**: Creates 25+ optimized views for analytics and reporting with standardized columns and pre-calculated metrics.

**Standard View Columns** (All Views Include):
- `account`: Account ID for filtering
- `account_full`: Account ID + Account Name for display
- `project_product_name`: Associated product name from junction table

**Executive Summary Views**:
- **view_summary**: Comprehensive account summary with KPIs
- **view_acct_summary**: Account-level health scores and metrics
- **view_product_summary**: Product-level analytics and performance

**Security Analytics Views**:
- **view_acct_security**: Security Hub summary by service
- **view_acct_security_findings_details**: Detailed findings with remediation
- **view_acct_security_findings_summary**: Comprehensive security posture
- **view_guard_duty_findings**: GuardDuty threat analysis
- **view_kms_keys**: KMS key management and rotation
- **view_waf_rules**: WAF configurations and compliance
- **view_waf_rules_detailed**: Detailed WAF rule compliance analysis
- **view_cloudtrail_logs**: CloudTrail logging status
- **view_secrets_manager_secrets**: Secrets management
- **view_certificates**: Certificate lifecycle management
- **view_inspector_findings**: Vulnerability assessment

**Financial Analytics Views**:
- **view_acct_cost_rep**: Cost reports with period analysis
- **view_acct_serv_cost**: Service costs with time periods
- **view_acct_cost_rep_forecast**: Cost forecasting with confidence intervals
- **view_acct_serv**: Service usage and costs by account

**Infrastructure & Operations Views**:
- **view_inventory_instances**: EC2 instance inventory
- **view_inventory_applications**: Application inventory
- **view_inventory_patches**: Patch compliance tracking
- **view_service_resources**: Multi-service resource inventory
- **view_config_reports**: Configuration compliance
- **view_non_compliant_resources**: Non-compliant resource tracking
- **view_marketplace_usage**: Marketplace product usage
- **view_trusted_advisor_checks**: Optimization recommendations
- **view_health_events**: AWS Health monitoring
- **view_application_signals**: Application performance
- **view_resilience_hub_apps**: Disaster recovery assessments

**Advanced Analytics Features**:
- **Pre-calculated Metrics**: Resolution rates, health scores, compliance percentages
- **Aggregated KPIs**: Cost trends, security posture, performance metrics
- **Multi-dimensional Analysis**: Account, product, service, time-based filtering
- **Executive Dashboards**: Summary views for leadership reporting

### core-utility.sql
**Purpose**: Utility script for dropping all views in correct dependency order.

**Usage**: Run this script when you need to:
- Recreate views with schema changes
- Clean up the database
- Troubleshoot view dependencies

## Execution Order

1. **core-schema.sql** - Creates all tables, indexes, and constraints
2. **core-view-schema.sql** - Creates all analytics views
3. **core-utility.sql** - (Optional) Drops views when needed

## Setup Instructions

### Using Aurora Query Editor (Recommended)

1. Navigate to **RDS > Query Editor** in AWS Console
2. Select your Aurora cluster
3. Connect using **Secrets Manager** credentials
4. Execute files in order:
   ```sql
   -- Copy and paste contents of core-schema.sql
   -- Copy and paste contents of core-view-schema.sql
   ```

### Key Database Features

**Advanced Data Types**:
- **JSONB**: Flexible configuration storage for complex AWS metadata
- **TIMESTAMP WITH TIME ZONE**: Accurate time tracking across regions
- **NUMERIC(20,10)**: Precise cost calculations with high precision
- **Custom Enums**: `period_granularity_type` for standardized values
- **TEXT Arrays**: Efficient storage of lists (usage types, blocked countries)
- **BOOLEAN**: Feature flags and compliance status

**Performance Optimizations**:
- **Strategic Indexing**: 50+ indexes on frequently queried columns
- **Composite Indexes**: Multi-column indexes for complex queries
- **Unique Constraints**: Prevent duplicates while enabling fast lookups
- **Optimized Views**: Pre-calculated metrics and efficient JOINs
- **Partitioning Ready**: Schema designed for future time-based partitioning

**Data Integrity & Relationships**:
- **Foreign Key Constraints**: Comprehensive referential integrity
- **Cascade Deletes**: Proper parent-child relationship management
- **Check Constraints**: Data validation (date ranges, positive costs)
- **Unique Constraints**: Business rule enforcement
- **Multi-tenant Support**: Account isolation and product relationships

## Common Queries

### Executive Dashboard
```sql
-- Comprehensive account overview with KPIs
SELECT account_name, current_period_cost, security_resolution_rate,
       critical_findings, number_of_products, account_age_days
FROM view_summary 
WHERE account = '123456789012';
```

### Security Posture Analysis
```sql
-- Security compliance across all services
SELECT service, total_findings, critical_count, high_count,
       resolution_rate_percent, risk_level
FROM view_acct_security_findings_summary 
WHERE critical_count > 0 OR high_count > 5
ORDER BY critical_count DESC, high_count DESC;
```

### Cost Optimization Insights
```sql
-- Cost trends with forecasting
SELECT account_name, current_period_cost, cost_difference_percentage,
       potential_savings, service_count, total_service_cost
FROM view_acct_cost_rep 
WHERE period_granularity = 'MONTHLY'
ORDER BY cost_difference_percentage DESC;
```

### WAF Security Compliance
```sql
-- WAF rule compliance analysis
SELECT web_acl_name, COUNT(*) as total_rules,
       SUM(CASE WHEN is_compliant THEN 1 ELSE 0 END) as compliant_rules,
       ROUND(AVG(CASE WHEN is_compliant THEN 100.0 ELSE 0.0 END), 2) as compliance_percentage
FROM view_waf_rules_detailed
GROUP BY web_acl_name
ORDER BY compliance_percentage ASC;
```

### Multi-Product Analytics
```sql
-- Product-level performance metrics
SELECT project_product_name, COUNT(DISTINCT account) as account_count,
       SUM(current_period_cost) as total_cost,
       AVG(security_resolution_rate) as avg_security_score
FROM view_product_summary
GROUP BY project_product_name
ORDER BY total_cost DESC;
```

## Maintenance

**Schema Evolution**:
- Use `core-utility.sql` to drop views before schema modifications
- Views automatically refresh when underlying data changes
- Schema supports backward compatibility for gradual migrations

**Performance Monitoring**:
- Monitor query performance with PostgreSQL's query planner
- Add indexes based on actual query patterns
- Regular VACUUM and ANALYZE for optimal performance
- Consider partitioning for large datasets (time-based)

**Multi-tenant Considerations**:
- Account-level data isolation enforced by foreign keys
- Product-account relationships support complex organizational structures
- Partner/customer fields enable multi-tenant SaaS deployments

**Analytics Best Practices**:
- Use summary views for executive dashboards
- Use detailed views for operational analysis
- Leverage pre-calculated metrics for performance
- Filter by account/product for tenant isolation