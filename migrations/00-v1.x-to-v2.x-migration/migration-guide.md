# Migration Script: Upgrade to Latest Schema Version 2.x

- Run these scripts in a transaction or test environment first
- The foreign key updates for contact_info and alternate_contacts assume your current schema uses VARCHAR(12) references to account_id
- All existing data will be preserved during the migration
- The IF NOT EXISTS and IF EXISTS clauses prevent errors if some changes were already applied
- Please execute the commands sequentially as they are dependent to one another.
- Create teh tables first before running the views.


---

**Table of Contents**

*   [1. Migrate the Tables](#1-migrate-the-tables)
    *   [Step 1: Add region column to accounts table](#step-1-add-region-column-to-accounts-table-and-update-unique-constraint)
    *   [Step 2: Update contact_info foreign key reference](#step-2-update-contact_info-foreign-key-reference)
    *   [Step 3: Update alternate_contacts foreign key reference](#step-3-update-alternate_contacts-foreign-key-reference)
    *   [Step 4: Update services table constraint](#step-4-update-services-table-constraint)
    *   [Step 5: Add missing columns to non_compliant_resources](#step-5-add-missing-columns-to-non_compliant_resources)
    *   [Step 6: Add missing columns to inventory_instances](#step-6-add-missing-columns-to-inventory_instances)
    *   [Step 7: Create support_tickets table](#step-7-create-support_tickets-table-if-not-exists)
    *   [Step 8: Create missing indexes](#step-8-create-missing-indexes)
*   [2. Migrate the Views](#2-migrate-the-views)
    *   [Step 1: Drop all old views](#step-1-drop-all-the-old-views)
    *   [Step 2: Re-Create the views](#step-2-re-create-the-views)
*   [3. Update Lambda Scripts](#3-update-lambda-scripts)
    *   [Step 1: Replace sender.py](#step-1-replace-senderpy)
    *   [Step 2: Replace receiver.py](#step-2-replace-receiverpy)
*   [4. Update CloudFormation Stacks](#4-update-cloudformation-stacks)
    *   [Step 1: Update Analytics Account Stack](#step-1-update-analytics-account-stack)
    *   [Step 2: Update All Sender Account Stacks](#step-2-update-all-sender-account-stacks)
*   [5. Refresh QuickSight Datasets](#5-refresh-quicksight-datasets)
*   [6. Post-Migration Validation](#6-post-migration-validation)
    *   [Step 1: Verify Data Collection](#step-1-verify-data-collection)
    *   [Step 2: Verify Database](#step-2-verify-database)
    *   [Step 3: Test QuickSight Dashboards](#step-3-test-quicksight-dashboards)
*   [Migration Checklist](#migration-checklist)
*   [Rollback Plan](#rollback-plan)
*   [Support](#support)

---

>**`ATTENTION: RUN THE BELOW COMMANDS IN ORDER`**

## 1. Migrate the Tables

### Step 1. Add region column to accounts table and update unique constraint

```
ALTER TABLE accounts 
ADD COLUMN IF NOT EXISTS region TEXT DEFAULT 'Global';
```

#### Drop existing unique constraint and add new one

```
ALTER TABLE accounts 
DROP CONSTRAINT IF EXISTS accounts_account_id_key CASCADE,
ADD CONSTRAINT accounts_account_id_region_key UNIQUE (account_id, region);
```

### Step 2. Update contact_info foreign key reference

#### Add new column

```
ALTER TABLE contact_info 
ADD COLUMN IF NOT EXISTS account_ref_id INTEGER;
```

#### Update the new column with proper references

```
UPDATE contact_info 
SET account_ref_id = a.id 
FROM accounts a 
WHERE contact_info.account_id = a.account_id;
```

#### Drop old constraint and column

```
ALTER TABLE contact_info 
DROP CONSTRAINT IF EXISTS contact_info_account_id_fkey CASCADE;

ALTER TABLE contact_info 
DROP COLUMN account_id CASCADE;

ALTER TABLE contact_info 
RENAME COLUMN account_ref_id TO account_id;
```

#### Add the new constraint
```
ALTER TABLE contact_info 
ADD CONSTRAINT contact_info_account_id_fkey 
FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;
```

### Step 3. Update alternate_contacts foreign key reference


```
ALTER TABLE alternate_contacts 
ADD COLUMN IF NOT EXISTS account_ref_id INTEGER;
```

```
UPDATE alternate_contacts 
SET account_ref_id = a.id 
FROM accounts a 
WHERE alternate_contacts.account_id = a.account_id;
```

```
ALTER TABLE alternate_contacts 
DROP CONSTRAINT IF EXISTS alternate_contacts_account_id_fkey CASCADE;

ALTER TABLE alternate_contacts 
DROP COLUMN account_id CASCADE;

ALTER TABLE alternate_contacts 
RENAME COLUMN account_ref_id TO account_id;
```

```
ALTER TABLE alternate_contacts 
ADD CONSTRAINT alternate_contacts_account_id_fkey 
FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;
```
### Step 4. Update services table constraint

```
ALTER TABLE services 
DROP CONSTRAINT IF EXISTS services_account_id_service_date_from_key,
ADD CONSTRAINT services_account_id_service_usage_types_date_from_key 
UNIQUE (account_id, service, usage_types, date_from);
```

### Step 5. Add missing columns to non_compliant_resources

```
ALTER TABLE non_compliant_resources
ADD COLUMN IF NOT EXISTS annotation TEXT,
ADD COLUMN IF NOT EXISTS evaluation_mode TEXT,
ADD COLUMN IF NOT EXISTS conformance_pack TEXT,
ADD COLUMN IF NOT EXISTS status VARCHAR(255) DEFAULT 'OPEN',
ADD COLUMN IF NOT EXISTS config_rule_invoked_time TIMESTAMP WITH TIME ZONE;
```

### Step 6. Add missing columns to inventory_instances

```
ALTER TABLE inventory_instances
ADD COLUMN IF NOT EXISTS platform_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS platform_version VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_latest_version BOOLEAN,
ADD COLUMN IF NOT EXISTS association_status VARCHAR(255),
ADD COLUMN IF NOT EXISTS association_execution_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS association_success_date TIMESTAMP WITH TIME ZONE;
```

### Step 7. Create support_tickets table if not exists

```
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    case_id VARCHAR(255) NOT NULL,
    display_id VARCHAR(50) NOT NULL,
    subject TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    severity_code VARCHAR(50) NOT NULL,
    service_code VARCHAR(255),
    category_code VARCHAR(50) NOT NULL,
    time_created TIMESTAMP WITH TIME ZONE NOT NULL,
    submitted_by VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (case_id),
    CONSTRAINT date_check CHECK (date_to >= date_from)
);
```


### Step 8. Create missing indexes

```
CREATE INDEX IF NOT EXISTS idx_support_tickets_account_time ON support_tickets(account_id, time_created);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_severity ON support_tickets(severity_code);
```

## 2. Migrate the Views

### Step 1. Drop all the old views

```
DROP VIEW IF EXISTS view_acct_support_tickets;
DROP VIEW IF EXISTS view_config_inventory;
DROP VIEW IF EXISTS view_compute_optimizer_summary;
DROP VIEW IF EXISTS view_acct_security_findings_summary;
DROP VIEW IF EXISTS view_product_summary;
DROP VIEW IF EXISTS view_acct_summary;
DROP VIEW IF EXISTS view_summary;
DROP VIEW IF EXISTS view_resilience_hub_apps;
DROP VIEW IF EXISTS view_application_signals;
DROP VIEW IF EXISTS view_health_events;
DROP VIEW IF EXISTS view_trusted_advisor_checks;
DROP VIEW IF EXISTS view_marketplace_usage;
DROP VIEW IF EXISTS view_inventory_patches;
DROP VIEW IF EXISTS view_inventory_applications;
DROP VIEW IF EXISTS view_inventory_instances;
DROP VIEW IF EXISTS view_inspector_findings;
DROP VIEW IF EXISTS view_certificates;
DROP VIEW IF EXISTS view_secrets_manager_secrets;
DROP VIEW IF EXISTS view_cloudtrail_logs;
DROP VIEW IF EXISTS view_waf_rules_detailed;
DROP VIEW IF EXISTS view_waf_rules;
DROP VIEW IF EXISTS view_kms_keys;
DROP VIEW IF EXISTS view_guard_duty_findings;
DROP VIEW IF EXISTS view_compute_optimizer;
DROP VIEW IF EXISTS view_service_resources_summary;
DROP VIEW IF EXISTS view_service_resources;
DROP VIEW IF EXISTS view_non_compliant_resources;
DROP VIEW IF EXISTS view_config_reports;
DROP VIEW IF EXISTS view_acct_log_messages;
DROP VIEW IF EXISTS view_acct_logs;
DROP VIEW IF EXISTS view_acct_products;
DROP VIEW IF EXISTS view_product_acct;
DROP VIEW IF EXISTS view_products;
DROP VIEW IF EXISTS view_acct_security_findings_details;
DROP VIEW IF EXISTS view_acct_security;
DROP VIEW IF EXISTS view_acct_cost_rep_forecast;
DROP VIEW IF EXISTS view_acct_serv_cost;
DROP VIEW IF EXISTS view_acct_cost_rep;
DROP VIEW IF EXISTS view_acct_serv;
DROP VIEW IF EXISTS view_alternate_contacts;
DROP VIEW IF EXISTS view_contact_info;
DROP VIEW IF EXISTS view_accounts;
```

### Step 2. Re-Create the Views

- Open the file `sql/schema/core-view.sql` 
- Run all the SQL statements inside your query editor by copy pasting it

---

## 3. Update Lambda Scripts

### Step 1: Replace sender.py

1. Navigate to your Analytics S3 bucket: `s3://your-analytics-bucket/scripts/`
2. Download the latest `sender.py` from the repository
3. Upload and replace the existing `sender.py` file in S3
4. Verify the file is uploaded successfully

### Step 2: Replace receiver.py

1. In the same S3 bucket location: `s3://your-analytics-bucket/scripts/`
2. Download the latest `receiver.py` from the repository
3. Upload and replace the existing `receiver.py` file in S3
4. Verify the file is uploaded successfully

---

## 4. Update CloudFormation Stacks

### Step 1: Update Analytics Account Stack

1. Open AWS CloudFormation console in your Analytics account
2. Select your existing Analytics stack (e.g., `A360-Analytics-Stack`)
3. Click **Create change set** → **Replace current template**
4. Upload the new `A360-Analytics.yaml` or `A360-Analytics-Custom-VPC.yaml`
5. Review parameters (keep existing values unless changes needed)
6. Click **Create change set**
7. Review the changes carefully
8. Click **Execute change set** to apply updates
9. Wait for stack update to complete (Status: UPDATE_COMPLETE)

### Step 2: Update All Sender Account Stacks

Repeat for each sender account:

1. Open AWS CloudFormation console in the sender account
2. Select the existing Sender stack (e.g., `A360-Sender-Stack`)
3. Click **Create change set** → **Replace current template**
4. Upload the new `A360-Sender.yaml`
5. Review parameters (keep existing values)
6. Click **Create change set**
7. Review the changes
8. Click **Execute change set**
9. Wait for UPDATE_COMPLETE status
10. Repeat for all sender accounts

---

## 5. Refresh QuickSight Datasets

### For Each Dataset:

1. Open Amazon QuickSight console
2. Navigate to **Datasets**
3. Select a dataset (e.g., `view_accounts`, `view_acct_cost_rep`, etc.)
4. Click **Edit dataset**
5. Wait for data to load and preview
6. Click **Save & publish**
7. Repeat for all datasets

### Key Datasets to Refresh:

- `view_accounts` (now includes region column)
- `view_acct_support_tickets` (new dataset)
- `view_config_inventory` (enhanced compliance data)
- `view_inventory_instances` (SSM agent compliance)
- All cost and security views

---

## 6. Post-Migration Validation

### Step 1: Verify Data Collection

```bash
# Check sender Lambda logs
aws logs tail /aws/lambda/A360SenderFunction --follow

# Check receiver Lambda logs
aws logs tail /aws/lambda/A360ReceiverFunction --follow
```

### Step 2: Verify Database

```sql
-- Check multi-region accounts
SELECT account_id, region, account_name FROM accounts;

-- Check support tickets
SELECT COUNT(*) FROM support_tickets;

-- Check enhanced compliance data
SELECT COUNT(*) FROM non_compliant_resources WHERE annotation IS NOT NULL;

-- Check SSM agent compliance
SELECT COUNT(*) FROM inventory_instances WHERE association_status IS NOT NULL;
```

### Step 3: Test QuickSight Dashboards

1. Open each dashboard
2. Verify data loads correctly
3. Check for new multi-region data
4. Verify support ticket visualizations
5. Confirm enhanced compliance metrics

---

## Migration Checklist

- [ ] Database tables migrated (Section 1)
- [ ] Database views recreated (Section 2)
- [ ] sender.py replaced in S3 (Section 3.1)
- [ ] receiver.py replaced in S3 (Section 3.2)
- [ ] Analytics CloudFormation stack updated (Section 4.1)
- [ ] All Sender CloudFormation stacks updated (Section 4.2)
- [ ] All QuickSight datasets refreshed (Section 5)
- [ ] Data collection verified (Section 6.1)
- [ ] Database validation completed (Section 6.2)
- [ ] QuickSight dashboards tested (Section 6.3)

---

## Rollback Plan

If issues occur:

1. **Database**: Restore from Aurora snapshot taken before migration
2. **Lambda Scripts**: Revert to previous sender.py/receiver.py versions in S3
3. **CloudFormation**: Use stack rollback or previous template versions
4. **QuickSight**: Datasets will automatically revert with database rollback

---

## Support

For migration issues:
- Check CloudWatch Logs for Lambda errors
- Review CloudFormation change set before execution
- Test in non-production environment first
- Verify IAM permissions for new features (Support API, multi-region access)