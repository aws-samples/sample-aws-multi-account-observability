# Migration Script: Upgrade v2.9.21 → v2.9.3

- Run these scripts on a test environment first.
- No existing data is destroyed, except **11 identical-content duplicate rows** in `log_messages` (see [Step 26](#step-26-deduplicate-log_messages-one-way)) — verified read-only that every duplicate pair has identical text.
- The RDS Data API accepts **one statement per call**. Pasting the whole `APPLY-ORDERED.sql` file into the query editor fails with `Multistatements aren't supported`. Run statements one at a time, or use the batch tool at [migrations/apply-sql.py](../apply-sql.py) which splits the file automatically.
- Every table and index is `IF NOT EXISTS`; every view is `CREATE OR REPLACE`. The 12 `ADD CONSTRAINT` statements are NOT `IF NOT EXISTS`-safe (Postgres doesn't support that clause on constraints). Re-runs on a partially-applied cluster need the rollback first.
- Rollback available at [APPLY-ORDERED-ROLLBACK.sql](APPLY-ORDERED-ROLLBACK.sql). Everything except the log_messages dedupe is reversible.

---

**Table of Contents**

- [1. What Changed](#1-what-changed)
- [2. Migrate the Tables](#2-migrate-the-tables)
    - [New tables — Security Hub V2 (OCSF)](#21-new-tables---security-hub-v2-ocsf)
        - [Step 1: Create exposure_findings](#step-1-create-exposure_findings)
        - [Step 7: Create exposure_contributed_finding](#step-7-create-exposure_contributed_finding)
        - [Step 12: Create exposure_finding_trait](#step-12-create-exposure_finding_trait)
        - [Step 16: Create threat_findings](#step-16-create-threat_findings)
        - [Step 22: Create security_standards](#step-22-create-security_standards)
    - [Deduplication before adding UNIQUE](#22-deduplication-before-adding-unique)
        - [Step 26: Deduplicate log_messages (ONE-WAY)](#step-26-deduplicate-log_messages-one-way)
    - [Add UNIQUE constraints on existing tables](#23-add-unique-constraints-on-existing-tables)
        - [Step 27: inventory_applications (widened key)](#step-27-inventory_applications-widened-key)
        - [Step 28: service_resources (widened key)](#step-28-service_resources-widened-key)
        - [Steps 29–38: 10 more UNIQUE constraints](#steps-2938-10-more-unique-constraints)
- [3. Migrate the Views](#3-migrate-the-views)
    - [Step 39: view_exposure_findings](#step-39-view_exposure_findings)
    - [Step 40: view_exposure_contributed_finding](#step-40-view_exposure_contributed_finding)
    - [Step 41: view_exposure_finding_trait](#step-41-view_exposure_finding_trait)
    - [Step 42: view_threat_findings](#step-42-view_threat_findings)
    - [Step 43: view_security_standards](#step-43-view_security_standards)
- [4. Update Lambda Scripts](#4-update-lambda-scripts)
    - [Step 1: Replace sender.py](#step-1-replace-senderpy)
    - [Step 2: Replace receiver.py](#step-2-replace-receiverpy)
- [5. Update CloudFormation Stacks](#5-update-cloudformation-stacks)
    - [Step 1: Update Analytics stack](#step-1-update-analytics-stack)
    - [Step 2: Update Sender stacks](#step-2-update-sender-stacks)
- [6. Refresh QuickSight Datasets](#6-refresh-quicksight-datasets)
- [7. Post-Migration Validation](#7-post-migration-validation)
- [Migration Checklist](#migration-checklist)
- [Rollback Plan](#rollback-plan)
- [Support](#support)

---

## 1. What Changed

**Schema (v2.9.21 → v2.9.3):**

| Category | Details |
|---|---|
| **6 new tables** | Security Hub V2 (OCSF) data: `exposure_findings` (parent), `exposure_contributed_finding`, `exposure_finding_trait`, `threat_findings`, `security_standards`, plus `ai_inventory` (self-hosted AI/ML resources from `GetResourcesV2`, with `status` ACTIVE/INACTIVE lifecycle matching exposures/threats — rows present in the payload are ACTIVE, absent rows flip to INACTIVE via `NOT IN` sweep, `updated_at` refreshes on every state change) |
| **23 new indexes** | Covering the 6 new tables |
| **12 new UNIQUE constraints** | `inventory_applications` (widened to `account_id, instance_id, name, version`), `service_resources` (widened to include `service_name`), `products`, `non_compliant_resources`, `service_costs`, `cost_forecasts`, `guard_duty_findings`, `kms_keys`, `waf_rules`, `inventory_patches`, `compute_optimizer`, `log_messages` |
| **1 data cleanup** | 11 exact-duplicate rows removed from `log_messages` before its UNIQUE constraint can apply |
| **6 new views** | One per new table |

**Sender/Receiver (Python):**

- Sender emits new top-level `security.exposures[]`, `security.threats[]`, `security.standards[]`, plus `ai_inventory[]` from Security Hub V2.
- Sender adds CVSS scoring to Inspector findings (`cve_id`, `cvss_score`, `cvss_severity`, `cvss_version`, `cvss_vector`, `epss_score`, `cve_count`) — moved off the legacy ASFF Security Hub path.
- Contributor entries under exposures carry `status: 'NEW'` and `workflow_state: 'NEW'` so a re-appearing contributor is correctly re-opened.
- Receiver rewrite: `INSERT ... ON CONFLICT ... RETURNING xmax = 0` collapses the 2-call SELECT+INSERT/UPDATE pattern to 1 call. Batched writes on 8 high-volume loaders. **Runtime dropped from 733s to 21s** (~35×).
- New resolve-close logic: any exposure/threat/contributor missing from the current payload flips to `status='RESOLVED'`. Cross-exposure `NOT EXISTS` guard protects a contributor that still ties to another active exposure.

**CloudFormation:**

- `securityhub:GetResources` + `securityhub:GetResourcesV2` added for AI/ML inventory (`_get_ai_inventory` via `GetResourcesV2`).
- `kms:ListKeys` split into its own statement with `Resource: "*"` (KMS doesn't support resource-level scoping on ListKeys).
- `kms:DescribeKey` + `kms:GetKeyRotationStatus` now cover both `${AWS::Region}` and `us-east-1` (global-service KMS keys live in us-east-1).

---

>**`ATTENTION: RUN THE BELOW COMMANDS IN ORDER`**

## 2. Migrate the Tables

### 2.1 New tables — Security Hub V2 (OCSF)

Create the 3-level exposure chain top-down, then the two flat tables. Every `CREATE TABLE` uses `IF NOT EXISTS` and is safe to re-run.

#### Step 1. Create exposure_findings

Parent of the exposure chain. One row per exposure.

```sql
CREATE TABLE IF NOT EXISTS exposure_findings (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    finding_id          VARCHAR(255) NOT NULL,
    finding_arn         VARCHAR(512),
    service             VARCHAR(255),
    title               TEXT,
    description         TEXT,
    severity            VARCHAR(50),
    status              VARCHAR(50),
    resource_type       VARCHAR(255),
    resource_id         VARCHAR(255),
    created_at          TIMESTAMP WITH TIME ZONE,
    updated_at          TIMESTAMP WITH TIME ZONE,
    recommendation      TEXT,
    compliance_status   VARCHAR(50),
    region              VARCHAR(50),
    workflow_state      VARCHAR(50),
    record_state        VARCHAR(50),
    product_name        VARCHAR(255),
    company_name        VARCHAR(255),
    product_arn         VARCHAR(512),
    generator_id        VARCHAR(512),
    generator           VARCHAR(255),
    cve_id              VARCHAR(50),
    cvss_score          NUMERIC(4,1),
    cvss_severity       VARCHAR(20),
    cvss_version        VARCHAR(10),
    cvss_vector         VARCHAR(255),
    epss_score          NUMERIC(8,6),
    cve_count           INTEGER NOT NULL DEFAULT 0,
    UNIQUE (finding_id)
);
```

#### Steps 2–6. exposure_findings indexes

```sql
CREATE INDEX IF NOT EXISTS idx_exposure_findings_account_id ON exposure_findings(account_id);
CREATE INDEX IF NOT EXISTS idx_exposure_findings_severity   ON exposure_findings(severity);
CREATE INDEX IF NOT EXISTS idx_exposure_findings_status     ON exposure_findings(status);
CREATE INDEX IF NOT EXISTS idx_exposure_findings_resource_id ON exposure_findings(resource_id);
CREATE INDEX IF NOT EXISTS idx_exposure_findings_cve_id     ON exposure_findings(cve_id);
```

#### Step 7. Create exposure_contributed_finding

Child of exposure_findings. `status` / `workflow_state` are **nullable** because Security Hub doesn't emit a per-contributor status — the sender stamps `'NEW'` at emission time and the receiver's resolve-close treats `NULL` as still-active via `IS DISTINCT FROM 'RESOLVED'`.

```sql
CREATE TABLE IF NOT EXISTS exposure_contributed_finding (
    id                      SERIAL PRIMARY KEY,
    account_id              INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    exposure_finding_id     INTEGER NOT NULL REFERENCES exposure_findings(id) ON DELETE CASCADE,
    finding_id              VARCHAR(255) NOT NULL,
    finding_arn             VARCHAR(512),
    source                  VARCHAR(255),
    title                   TEXT,
    is_finding              BOOLEAN NOT NULL DEFAULT FALSE,
    resource_uid            VARCHAR(512),
    status                  VARCHAR(50),
    workflow_state          VARCHAR(50),
    cve_id                  VARCHAR(50),
    cvss_score              NUMERIC(4,1),
    cvss_severity           VARCHAR(20),
    cvss_version            VARCHAR(10),
    cvss_vector             VARCHAR(255),
    epss_score              NUMERIC(8,6),
    cve_count               INTEGER NOT NULL DEFAULT 0,
    trait_count             INTEGER NOT NULL DEFAULT 0,
    trait_categories        VARCHAR(255),
    trait_names             TEXT,
    UNIQUE (exposure_finding_id, finding_id)
);
```

#### Steps 8–11. exposure_contributed_finding indexes

```sql
CREATE INDEX IF NOT EXISTS idx_ecf_account_id           ON exposure_contributed_finding(account_id);
CREATE INDEX IF NOT EXISTS idx_ecf_exposure_finding_id  ON exposure_contributed_finding(exposure_finding_id);
CREATE INDEX IF NOT EXISTS idx_ecf_cve_id               ON exposure_contributed_finding(cve_id);
CREATE INDEX IF NOT EXISTS idx_ecf_status               ON exposure_contributed_finding(status);
```

#### Step 12. Create exposure_finding_trait

`UNIQUE NULLS NOT DISTINCT` is a PG15+ feature that treats NULL as equal to itself, so idempotent re-runs of the same trait set work regardless of whether `category` is NULL.

```sql
CREATE TABLE IF NOT EXISTS exposure_finding_trait (
    id                      SERIAL PRIMARY KEY,
    account_id              INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    contributed_finding_id  INTEGER NOT NULL REFERENCES exposure_contributed_finding(id) ON DELETE CASCADE,
    category                VARCHAR(64),
    name                    VARCHAR(512) NOT NULL,
    type                    VARCHAR(64) NOT NULL,
    UNIQUE NULLS NOT DISTINCT (contributed_finding_id, name, type)
);
```

#### Steps 13–15. exposure_finding_trait indexes

```sql
CREATE INDEX IF NOT EXISTS idx_eft_account_id            ON exposure_finding_trait(account_id);
CREATE INDEX IF NOT EXISTS idx_eft_contributed_finding_id ON exposure_finding_trait(contributed_finding_id);
CREATE INDEX IF NOT EXISTS idx_eft_category              ON exposure_finding_trait(category);
```

#### Step 16. Create threat_findings

Flat table (no children in the current sender output). `occurrence_count` is named to avoid collision with SQL `COUNT()` — the sender's payload key is still `count`, and the receiver maps it during upsert.

```sql
CREATE TABLE IF NOT EXISTS threat_findings (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    finding_id          VARCHAR(255) NOT NULL,
    finding_arn         VARCHAR(512),
    service             VARCHAR(255),
    title               TEXT,
    description         TEXT,
    severity            VARCHAR(50),
    status              VARCHAR(50),
    resource_type       VARCHAR(255),
    resource_id         VARCHAR(255),
    created_at          TIMESTAMP WITH TIME ZONE,
    updated_at          TIMESTAMP WITH TIME ZONE,
    recommendation      TEXT,
    region              VARCHAR(50),
    workflow_state      VARCHAR(50),
    record_state        VARCHAR(50),
    product_name        VARCHAR(255),
    company_name        VARCHAR(255),
    product_arn         VARCHAR(512),
    generator_id        VARCHAR(512),
    generator           VARCHAR(255),
    finding_type        VARCHAR(255),
    analytic_type       VARCHAR(50),
    actor_name          VARCHAR(255),
    actor_uid           VARCHAR(255),
    api_operation       VARCHAR(255),
    api_service         VARCHAR(255),
    source_ip           VARCHAR(45),
    source_country      VARCHAR(100),
    occurrence_count    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (finding_id)
);
```

#### Steps 17–21. threat_findings indexes

```sql
CREATE INDEX IF NOT EXISTS idx_threat_findings_account_id  ON threat_findings(account_id);
CREATE INDEX IF NOT EXISTS idx_threat_findings_severity    ON threat_findings(severity);
CREATE INDEX IF NOT EXISTS idx_threat_findings_status      ON threat_findings(status);
CREATE INDEX IF NOT EXISTS idx_threat_findings_finding_type ON threat_findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_threat_findings_actor_uid   ON threat_findings(actor_uid);
```

#### Step 22. Create security_standards

`date_from` is part of the unique key so the same standard writes a new row every day. Score history over `date_from` gives the trend chart.

```sql
CREATE TABLE IF NOT EXISTS security_standards (
    id                  SERIAL PRIMARY KEY,
    account_id          INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    standard_name       VARCHAR(255) NOT NULL,
    standard_arn        VARCHAR(512) NOT NULL,
    subscription_arn    VARCHAR(512),
    status              VARCHAR(50),
    passed              INTEGER NOT NULL DEFAULT 0,
    failed              INTEGER NOT NULL DEFAULT 0,
    score               INTEGER NOT NULL DEFAULT 0,
    date_from           DATE NOT NULL,
    date_to             DATE NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, standard_arn, date_from)
);
```

#### Steps 23–25. security_standards indexes

```sql
CREATE INDEX IF NOT EXISTS idx_security_standards_account_id ON security_standards(account_id);
CREATE INDEX IF NOT EXISTS idx_security_standards_name       ON security_standards(standard_name);
CREATE INDEX IF NOT EXISTS idx_security_standards_date_from  ON security_standards(date_from);
```

---

### 2.2 Deduplication before adding UNIQUE

#### Step 26. Deduplicate log_messages (ONE-WAY)

`log_messages` had 11 identical-content duplicate rows from three specific 2026-01-27 log runs — verified read-only that every duplicate pair has identical `message` text as well. Keep the oldest of each group and delete the rest so the UNIQUE constraint below can apply. **Not reversible from the rollback file.**

```sql
DELETE FROM log_messages
WHERE id NOT IN (
    SELECT MIN(id) FROM log_messages GROUP BY log_id, message_type
);
```

---

### 2.3 Add UNIQUE constraints on existing tables

Every constraint below matches the composite key the receiver's `upsert` already used at runtime. Without them, `upsert` falls back to a per-row SELECT that scans the whole table — the direct cause of the 733s→21s speedup you'll see after applying this migration.

#### Step 27. inventory_applications (widened key)

Old caller keyed on `(instance_id, name)` — that overwrote the old row when a package upgraded to a new version. New key includes `account_id` and `version` so version history is preserved.

```sql
ALTER TABLE inventory_applications
    ADD CONSTRAINT inventory_applications_unique
    UNIQUE (account_id, instance_id, name, version);
```

#### Step 28. service_resources (widened key)

Old caller keyed on `(account_id, resource_id)` — an ARN appearing under two services (rare, e.g. EBS attached to EC2) would collide. New key includes `service_name`.

```sql
ALTER TABLE service_resources
    ADD CONSTRAINT service_resources_unique
    UNIQUE (account_id, service_name, resource_id);
```

#### Steps 29–38. 10 more UNIQUE constraints

```sql
-- [29]
ALTER TABLE products
    ADD CONSTRAINT products_name_unique
    UNIQUE (name);

-- [30]
ALTER TABLE non_compliant_resources
    ADD CONSTRAINT non_compliant_resources_unique
    UNIQUE (config_report_id, resource_id, rule_name);

-- [31]
ALTER TABLE service_costs
    ADD CONSTRAINT service_costs_unique
    UNIQUE (cost_report_id, service_name, region);

-- [32]
ALTER TABLE cost_forecasts
    ADD CONSTRAINT cost_forecasts_unique
    UNIQUE (cost_report_id, period_start, region);

-- [33]
ALTER TABLE guard_duty_findings
    ADD CONSTRAINT guard_duty_findings_unique
    UNIQUE (account_id, detector_id);

-- [34]
ALTER TABLE kms_keys
    ADD CONSTRAINT kms_keys_key_id_unique
    UNIQUE (key_id);

-- [35]
ALTER TABLE waf_rules
    ADD CONSTRAINT waf_rules_waf_id_unique
    UNIQUE (waf_id);

-- [36]
ALTER TABLE inventory_patches
    ADD CONSTRAINT inventory_patches_unique
    UNIQUE (instance_id, title);

-- [37]
ALTER TABLE compute_optimizer
    ADD CONSTRAINT compute_optimizer_resource_arn_unique
    UNIQUE (resource_arn);

-- [38]
ALTER TABLE log_messages
    ADD CONSTRAINT log_messages_unique
    UNIQUE (log_id, message_type);
```

**Pre-check confirmation**: read-only queries against the live cluster before writing this migration confirmed **0 duplicate rows** on all 12 constraint keys (except `log_messages`, deduped in Step 26). Every `ADD CONSTRAINT` above applies cleanly on live data.

---

## 3. Migrate the Views

Every view uses `CREATE OR REPLACE` — no drops needed. All 5 follow the same account-attribution convention as every other view in `core-view.sql`:

- `<table>.*` first
- Then the account columns: `account`, `account_region`, `account_name`, `account_type`, `account_category`, `account_status`, `account_partner`, `account_customer`, `account_full`
- Then a `DISTINCT ON (account_id)` `product_accounts` subquery LEFT JOINed to `products` for `project_product_name`

#### Step 39. view_exposure_findings

```sql
CREATE OR REPLACE VIEW view_exposure_findings AS
SELECT ef.*,
       a.account_id as account, a.region as account_region, a.account_name, a.account_type,
       a.category as account_category, a.account_status as account_status,
       a.partner_name as account_partner, a.customer_name as account_customer,
       CONCAT(a.account_id, '-', a.account_name) as account_full,
       p.name as project_product_name
FROM exposure_findings ef
JOIN accounts a ON ef.account_id = a.id
LEFT JOIN (SELECT DISTINCT ON (account_id) account_id, product_id
           FROM product_accounts ORDER BY account_id, id) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id;
```

#### Step 40. view_exposure_contributed_finding

Exposes parent `finding_id` as `exposure_finding_uid` and the parent's `title`/`severity` for report-friendly joins.

```sql
CREATE OR REPLACE VIEW view_exposure_contributed_finding AS
SELECT ecf.*,
       ef.finding_id as exposure_finding_uid,
       ef.title as exposure_title,
       ef.severity as exposure_severity,
       a.account_id as account, a.region as account_region, a.account_name, a.account_type,
       a.category as account_category, a.account_status as account_status,
       a.partner_name as account_partner, a.customer_name as account_customer,
       CONCAT(a.account_id, '-', a.account_name) as account_full,
       p.name as project_product_name
FROM exposure_contributed_finding ecf
JOIN accounts a ON ecf.account_id = a.id
JOIN exposure_findings ef ON ecf.exposure_finding_id = ef.id
LEFT JOIN (SELECT DISTINCT ON (account_id) account_id, product_id
           FROM product_accounts ORDER BY account_id, id) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id;
```

#### Step 41. view_exposure_finding_trait

```sql
CREATE OR REPLACE VIEW view_exposure_finding_trait AS
SELECT eft.*,
       ecf.finding_id as contributed_finding_uid,
       ecf.title as contributed_title,
       a.account_id as account, a.region as account_region, a.account_name, a.account_type,
       a.category as account_category, a.account_status as account_status,
       a.partner_name as account_partner, a.customer_name as account_customer,
       CONCAT(a.account_id, '-', a.account_name) as account_full,
       p.name as project_product_name
FROM exposure_finding_trait eft
JOIN accounts a ON eft.account_id = a.id
JOIN exposure_contributed_finding ecf ON eft.contributed_finding_id = ecf.id
LEFT JOIN (SELECT DISTINCT ON (account_id) account_id, product_id
           FROM product_accounts ORDER BY account_id, id) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id;
```

#### Step 42. view_threat_findings

```sql
CREATE OR REPLACE VIEW view_threat_findings AS
SELECT tf.*,
       a.account_id as account, a.region as account_region, a.account_name, a.account_type,
       a.category as account_category, a.account_status as account_status,
       a.partner_name as account_partner, a.customer_name as account_customer,
       CONCAT(a.account_id, '-', a.account_name) as account_full,
       p.name as project_product_name
FROM threat_findings tf
JOIN accounts a ON tf.account_id = a.id
LEFT JOIN (SELECT DISTINCT ON (account_id) account_id, product_id
           FROM product_accounts ORDER BY account_id, id) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id;
```

#### Step 43. view_security_standards

```sql
CREATE OR REPLACE VIEW view_security_standards AS
SELECT ss.*,
       a.account_id as account, a.region as account_region, a.account_name, a.account_type,
       a.category as account_category, a.account_status as account_status,
       a.partner_name as account_partner, a.customer_name as account_customer,
       CONCAT(a.account_id, '-', a.account_name) as account_full,
       p.name as project_product_name
FROM security_standards ss
JOIN accounts a ON ss.account_id = a.id
LEFT JOIN (SELECT DISTINCT ON (account_id) account_id, product_id
           FROM product_accounts ORDER BY account_id, id) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id;
```

---

## 4. Update Lambda Scripts

### Step 1. Replace sender.py

The new sender adds Security Hub V2 collection (`get_security_hub_v2`), AI/ML resource inventory (`_get_ai_inventory` via `GetResourcesV2`), CVSS on Inspector findings (`_extract_cvss_inspector`), the `status/workflow_state` fields on contributor entries, and the `NEW` fix on legacy Security Hub queries. Payload structure change is documented in [docs/data_format.md](../../docs/data_format.md).

1. Navigate to your Analytics S3 bucket: `s3://<analytics-bucket>/scripts/`
2. Upload the new `sender.py` (from [scripts/sender.py](../../scripts/sender.py))
3. Verify the file is uploaded successfully
4. Both the Analytics account's Sender Lambda and every remote Sender Lambda across all sender accounts read the same script from S3, so this one upload propagates to every account on the next scheduled run.

### Step 2. Replace receiver.py

The new receiver is the biggest change on the ingest side:

- **Runtime went from 733s to 21s** (~35× faster) via the rewrite from SELECT-then-INSERT/UPDATE (2 API calls per row) to `INSERT ... ON CONFLICT ... DO UPDATE ... RETURNING xmax = 0` (1 call per row).
- 8 high-volume loaders now use `batch_upsert` — one Data API call per table instead of N per-row calls.
- New `load_security_hub_v2_data` handles the exposure/contributor/trait/threat/standards chain with cross-exposure `NOT EXISTS` protection for shared contributors.
- New `DEBUG=true` environment variable enables per-loader and per-security-sub-block timing lines.

1. Navigate to your Analytics S3 bucket: `s3://<analytics-bucket>/scripts/`
2. Upload the new `receiver.py` (from [scripts/receiver.py](../../scripts/receiver.py))
3. The Receiver Lambda in the Analytics account picks up the new script on its next invocation.

---

## 5. Update CloudFormation Stacks

Three template files updated ([A360-Analytics.yaml](../../cloudformation/A360-Analytics.yaml), [A360-Analytics-Custom-VPC.yaml](../../cloudformation/A360-Analytics-Custom-VPC.yaml), [A360-Sender.yaml](../../cloudformation/A360-Sender.yaml)).

**Changes:**
1. **`securityhub:GetResources` + `securityhub:GetResourcesV2`** added — required for the AI/ML inventory feed (`_get_ai_inventory` via Security Hub V2's `GetResourcesV2` API).
2. **`kms:ListKeys` split into its own statement** with `Resource: "*"` — KMS's `ListKeys` action does NOT support resource-level scoping, so bundling it with the key-scoped actions was causing an `AccessDeniedException`.
3. **`kms:DescribeKey` + `kms:GetKeyRotationStatus` now cover both `${AWS::Region}` and `us-east-1`** — the sender fans out to both regions to pick up global-service KMS keys (CloudFront's live in us-east-1).

### Step 1. Update Analytics stack

1. Open AWS CloudFormation in your Analytics account
2. Select your existing Analytics stack (e.g. `A360-Analytics-Stack`)
3. Click **Create change set** → **Replace current template**
4. Upload the new [A360-Analytics.yaml](../../cloudformation/A360-Analytics.yaml) or [A360-Analytics-Custom-VPC.yaml](../../cloudformation/A360-Analytics-Custom-VPC.yaml)
5. Keep existing parameter values
6. Review and **Execute change set**
7. Wait for `UPDATE_COMPLETE`

### Step 2. Update Sender stacks

Repeat for every sender account:

1. Open CloudFormation in the sender account
2. Select the existing Sender stack (e.g. `A360-Sender-Stack`)
3. **Create change set** → **Replace current template**
4. Upload the new [A360-Sender.yaml](../../cloudformation/A360-Sender.yaml)
5. Keep existing parameters
6. **Execute change set**
7. Wait for `UPDATE_COMPLETE`
8. Repeat for all sender accounts

---

## 6. Refresh QuickSight Datasets

For each new/updated dataset:

1. Open QuickSight → **Datasets**
2. Select the dataset (e.g. `view_exposure_findings`, `view_threat_findings`, `view_security_standards`)
3. Click **Edit dataset** → wait for the preview to load → **Save & publish**

**New datasets to create:**
- `view_exposure_findings` (V2 exposures with CVSS scoring)
- `view_exposure_contributed_finding` (contributors, joined with parent title/severity)
- `view_exposure_finding_trait` (individual traits under each contributor)
- `view_threat_findings` (GuardDuty threats with actor/API metadata)
- `view_security_standards` (daily standard scores for trend charts — key axis is `date_from`)

**Existing datasets to refresh** (their tables gained a UNIQUE constraint, no columns changed):
- `view_inventory_applications`, `view_service_resources`, `view_config_reports`, `view_non_compliant_resources`, `view_kms_keys`, `view_waf_rules`, `view_compute_optimizer`, `view_guard_duty_findings`, `view_inventory_patches`, `view_acct_serv_cost`, `view_acct_cost_rep_forecast`, `view_acct_log_messages`, `view_products`

---

## 7. Post-Migration Validation

### Step 1. Verify Data Collection

```bash
# Sender log tail
aws logs tail /aws/lambda/A360SenderFunction --follow

# Receiver log tail — with DEBUG=true you'll see per-loader timings
aws logs tail /aws/lambda/A360ReceiverFunction --follow
```

Expected output — receiver should complete in **~20 seconds**:

```
⏱️ loader security: 18.03s
🟢 Data Loaded & File moved to loaded/ folder in 21.1s
```

### Step 2. Verify Database

```sql
-- 5 new tables present
SELECT tablename FROM pg_tables
WHERE schemaname='public'
  AND tablename IN ('exposure_findings','exposure_contributed_finding',
                    'exposure_finding_trait','threat_findings','security_standards')
ORDER BY 1;
-- Expect: 5 rows

-- 5 new views present
SELECT viewname FROM pg_views
WHERE schemaname='public'
  AND viewname LIKE 'view_exposure%' OR viewname IN ('view_threat_findings','view_security_standards')
ORDER BY 1;
-- Expect: 5 rows

-- 12 new UNIQUE constraints present
SELECT conname FROM pg_constraint
WHERE conname IN (
    'inventory_applications_unique','service_resources_unique',
    'products_name_unique','non_compliant_resources_unique',
    'service_costs_unique','cost_forecasts_unique',
    'guard_duty_findings_unique','kms_keys_key_id_unique',
    'waf_rules_waf_id_unique','inventory_patches_unique',
    'compute_optimizer_resource_arn_unique','log_messages_unique'
)
ORDER BY 1;
-- Expect: 12 rows

-- Sanity check on new data — after the next sender/receiver cycle
SELECT count(*) AS exposures     FROM exposure_findings;
SELECT count(*) AS contributors  FROM exposure_contributed_finding;
SELECT count(*) AS traits        FROM exposure_finding_trait;
SELECT count(*) AS threats       FROM threat_findings;
SELECT count(*) AS standards     FROM security_standards;
SELECT count(*) AS ai_resources  FROM ai_inventory;  -- if that table exists in your setup
```

### Step 3. Test the resolve-close lifecycle

Delete an exposure from the sender payload (or wait for AWS Security Hub to naturally close one) and re-run. Confirm:

```sql
-- Removed exposure flipped to RESOLVED (row preserved, not deleted)
SELECT finding_id, status, workflow_state, record_state, updated_at
FROM exposure_findings
WHERE status = 'RESOLVED'
ORDER BY updated_at DESC LIMIT 5;

-- Its unique contributors flipped too
SELECT ecf.finding_id, ecf.status, ef.status AS parent_status
FROM exposure_contributed_finding ecf
JOIN exposure_findings ef ON ecf.exposure_finding_id = ef.id
WHERE ecf.status = 'RESOLVED' AND ef.status = 'RESOLVED'
LIMIT 10;

-- Shared contributors (same finding_id under multiple parents) stayed active
-- if at least one parent is still open — this is the NOT EXISTS guard working
SELECT finding_id, count(*) AS total_rows,
       count(*) FILTER (WHERE status = 'RESOLVED') AS resolved_rows,
       count(*) FILTER (WHERE status IS DISTINCT FROM 'RESOLVED') AS active_rows
FROM exposure_contributed_finding
GROUP BY finding_id
HAVING count(*) > 1
LIMIT 10;
```

### Step 4. Test QuickSight Dashboards

1. Open dashboards that consume the 5 new views
2. Verify V2 exposure/threat data appears
3. Confirm security standards trend chart plots `score` over `date_from`
4. Check that pre-existing dashboards still render (no column changes on old tables)

---

## Migration Checklist

- [ ] Database tables migrated (Section 2.1 — 29 statements, including ai_inventory)
- [ ] log_messages deduped (Section 2.2 — one DELETE statement)
- [ ] UNIQUE constraints added (Section 2.3 — 12 statements)
- [ ] Database views created (Section 3 — 6 statements, including view_ai_inventory)
- [ ] sender.py replaced in S3 (Section 4.1)
- [ ] receiver.py replaced in S3 (Section 4.2)
- [ ] Analytics CloudFormation stack updated (Section 5.1)
- [ ] All Sender CloudFormation stacks updated (Section 5.2)
- [ ] QuickSight datasets refreshed / new datasets created (Section 6)
- [ ] Data collection verified (Section 7.1)
- [ ] Database validation completed (Section 7.2)
- [ ] Resolve-close lifecycle tested (Section 7.3)
- [ ] QuickSight dashboards tested (Section 7.4)

---

## Rollback Plan

If issues occur:

1. **Database**: Run [APPLY-ORDERED-ROLLBACK.sql](APPLY-ORDERED-ROLLBACK.sql). It drops the 5 new views, drops the 12 UNIQUE constraints, and drops the 5 new tables in reverse FK order. `CASCADE` is deliberately NOT used — an object outside this migration's list that depends on one of these tables will fail the DROP loudly rather than take that dependency down silently.
2. **Log messages dedupe**: NOT reversible from the rollback file. Restore from an Aurora snapshot taken before the migration if you need those 11 duplicate rows back.
3. **Lambda scripts**: Revert to the previous `sender.py` / `receiver.py` in S3. The rewrites are backward-incompatible with the old schema only via the resolve-close UPDATEs — which fail silently if the tables don't exist — so the old scripts still work against the new schema.
4. **CloudFormation**: Use stack rollback or upload the previous template version.
5. **QuickSight**: New datasets can be deleted; existing datasets need no rollback.

**One-way changes** (cannot be rolled back from files):
- `log_messages` deduplication (Step 26) — 11 rows gone, restore from snapshot only.

---

## Support

For migration issues:
- Check CloudWatch Logs for Lambda errors — `DEBUG=true` in Lambda env gives per-loader timings
- Review CloudFormation change set before executing
- Test in a non-production environment first
- Verify IAM permissions for new features (Security Hub V2 → `securityhub:GetResources` + `securityhub:GetResourcesV2`, KMS list → `kms:ListKeys` with Resource `*`, KMS key ops covering both `${AWS::Region}` and `us-east-1`)
