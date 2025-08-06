# SQL Schema Documentation

This folder contains the SQL files for setting up the Aurora PostgreSQL database schema for the AWS Multi-Account Observability Platform.

## core-schema.sql
**Purpose**: Creates the complete database schema with 25+ tables for storing AWS observability data.

**Key Components**:
- **Account Tables**: `accounts`, `contact_info`, `alternate_contacts`
- **Cost Tables**: `cost_reports`, `service_costs`, `cost_forecasts`
- **Security Tables**: `security`, `findings`, `guard_duty_findings`, `kms_keys`, `waf_rules`, etc.
- **Inventory Tables**: `inventory_instances`, `inventory_applications`, `inventory_patches`
- **Service Tables**: `services`, `service_resources`
- **Compliance Tables**: `config_reports`, `non_compliant_resources`
- **Monitoring Tables**: `logs`, `log_messages`
- **Additional Tables**: `marketplace_usage`, `trusted_advisor_checks`, `health_events`, etc.

**Features**:
- Foreign key relationships for data integrity
- Indexes for query performance
- Custom enum types (e.g., `period_granularity_type`)
- Timestamp tracking with `created_at`/`updated_at`
- Unique constraints to prevent duplicates

## core-view-schema.sql
**Purpose**: Creates optimized views for analytics and reporting with standardized columns.

**Standard View Columns**:
- `account`: Account ID for filtering
- `account_full`: Account ID + Account Name for display
- `project_product_name`: Associated product name from junction table

**Key Views**:
- **Account Views**: `view_accounts`, `view_contact_info`, `view_alternate_contacts`
- **Cost Views**: `view_acct_cost_rep`, `view_acct_serv_cost`, `view_acct_cost_rep_forecast`
- **Security Views**: `view_acct_security`, `view_acct_security_findings_details`
- **Service Views**: `view_acct_serv`, `view_service_resources`
- **Inventory Views**: `view_inventory_instances`, `view_inventory_applications`, `view_inventory_patches`
- **Summary Views**: `view_summary`, `view_acct_summary`, `view_product_summary`

**Analytics Features**:
- Pre-calculated metrics (resolution rates, health scores)
- Aggregated data for dashboards
- Product-account relationships
- Time-based filtering capabilities

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

**Data Types**:
- `JSONB` for flexible configuration storage
- `TIMESTAMP WITH TIME ZONE` for accurate time tracking
- `NUMERIC` for precise cost calculations
- Custom enums for standardized values

**Performance Optimizations**:
- Strategic indexes on frequently queried columns
- Composite unique constraints
- Optimized view queries with proper JOINs

**Data Integrity**:
- Foreign key relationships
- Unique constraints prevent duplicates
- Check constraints for data validation
- Cascade deletes for parent-child relationships

## Common Queries

### Account Summary
```sql
SELECT * FROM view_summary 
WHERE account = '123456789012';
```

### Security Overview
```sql
SELECT * FROM view_acct_security 
WHERE critical_count > 0;
```

### Cost Analysis
```sql
SELECT * FROM view_acct_cost_rep 
WHERE period_granularity = 'MONTHLY';
```

## Maintenance

- Views automatically refresh when underlying data changes
- Use `core-utility.sql` to drop views before schema modifications
- Monitor query performance and add indexes as needed
- Regular VACUUM and ANALYZE for optimal performance