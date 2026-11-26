-- Rollback v2.9.4 -> v2.9.3: remove Inspector CVE detail
-- Run each statement on its own (RDS Data API). Deploy the v2.9.3 receiver.py first,
-- or the next load writes columns that no longer exist and the Inspector batch is skipped.
-- The dropped columns' data is lost; it comes back on the next daily run after re-applying.

-- Step 1: drop the CVE summary view
DROP VIEW IF EXISTS view_inspector_cves;

-- Step 2: drop view_inspector_findings so its columns can be removed
DROP VIEW IF EXISTS view_inspector_findings;

-- Steps 3-6: drop the CVE lookup indexes
DROP INDEX IF EXISTS idx_inspector_findings_account_id;
DROP INDEX IF EXISTS idx_inspector_findings_status;
DROP INDEX IF EXISTS idx_inspector_findings_cve_id;
DROP INDEX IF EXISTS idx_inspector_findings_resource_id;

-- Step 7: drop the added columns
ALTER TABLE inspector_findings
    DROP COLUMN IF EXISTS last_observed_at,
    DROP COLUMN IF EXISTS updated_at,
    DROP COLUMN IF EXISTS fix_available,
    DROP COLUMN IF EXISTS exploit_available,
    DROP COLUMN IF EXISTS resource_type,
    DROP COLUMN IF EXISTS resource_id,
    DROP COLUMN IF EXISTS resource_name,
    DROP COLUMN IF EXISTS resource_region,
    DROP COLUMN IF EXISTS package_name,
    DROP COLUMN IF EXISTS package_version,
    DROP COLUMN IF EXISTS package_manager,
    DROP COLUMN IF EXISTS fixed_in_version,
    DROP COLUMN IF EXISTS remediation,
    DROP COLUMN IF EXISTS source_url,
    DROP COLUMN IF EXISTS cve_id,
    DROP COLUMN IF EXISTS cvss_score,
    DROP COLUMN IF EXISTS cvss_severity,
    DROP COLUMN IF EXISTS cvss_version,
    DROP COLUMN IF EXISTS cvss_vector,
    DROP COLUMN IF EXISTS epss_score,
    DROP COLUMN IF EXISTS cve_count;

-- Step 8: recreate the v2.9.3 view_inspector_findings
CREATE VIEW view_inspector_findings AS
SELECT
    if.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    inspector_findings if
    JOIN accounts a ON if.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;
