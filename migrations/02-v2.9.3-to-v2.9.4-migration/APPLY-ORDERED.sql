-- Upgrade v2.9.3 -> v2.9.4: Inspector CVE detail
-- The RDS Data API runs one statement per call: run each statement below on its own.

-- Step 1: add CVE, resource and package columns to inspector_findings
ALTER TABLE inspector_findings
    ADD COLUMN IF NOT EXISTS last_observed_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS fix_available VARCHAR(20),
    ADD COLUMN IF NOT EXISTS exploit_available VARCHAR(20),
    ADD COLUMN IF NOT EXISTS resource_type VARCHAR(100),
    ADD COLUMN IF NOT EXISTS resource_id VARCHAR(512),
    ADD COLUMN IF NOT EXISTS resource_name VARCHAR(512),
    ADD COLUMN IF NOT EXISTS resource_region VARCHAR(50),
    ADD COLUMN IF NOT EXISTS package_name TEXT,
    ADD COLUMN IF NOT EXISTS package_version VARCHAR(255),
    ADD COLUMN IF NOT EXISTS package_manager VARCHAR(50),
    ADD COLUMN IF NOT EXISTS fixed_in_version VARCHAR(255),
    ADD COLUMN IF NOT EXISTS remediation TEXT,
    ADD COLUMN IF NOT EXISTS source_url TEXT,
    ADD COLUMN IF NOT EXISTS cve_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS cvss_score NUMERIC(4,1),
    ADD COLUMN IF NOT EXISTS cvss_severity VARCHAR(20),
    ADD COLUMN IF NOT EXISTS cvss_version VARCHAR(10),
    ADD COLUMN IF NOT EXISTS cvss_vector VARCHAR(255),
    ADD COLUMN IF NOT EXISTS epss_score NUMERIC(8,6),
    ADD COLUMN IF NOT EXISTS cve_count INTEGER NOT NULL DEFAULT 0;

-- Steps 2-5: indexes for CVE lookups
CREATE INDEX IF NOT EXISTS idx_inspector_findings_account_id ON inspector_findings(account_id);
CREATE INDEX IF NOT EXISTS idx_inspector_findings_status ON inspector_findings(status);
CREATE INDEX IF NOT EXISTS idx_inspector_findings_cve_id ON inspector_findings(cve_id);
CREATE INDEX IF NOT EXISTS idx_inspector_findings_resource_id ON inspector_findings(resource_id);

-- Step 6: drop view_inspector_findings. Its "if.*" now expands to the new columns in the
-- middle of the column list, which CREATE OR REPLACE VIEW refuses, so it is dropped first
DROP VIEW IF EXISTS view_inspector_findings;

-- Step 7: recreate view_inspector_findings with the new columns
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

-- Step 8: create view_inspector_cves - one row per CVE per account and region, ACTIVE findings only
CREATE OR REPLACE VIEW view_inspector_cves AS
SELECT
    c.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM (
    SELECT
        account_id,
        cve_id,
        (ARRAY['CRITICAL','HIGH','MEDIUM','LOW','INFORMATIONAL','UNTRIAGED'])[
            MIN(CASE severity
                    WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4 WHEN 'INFORMATIONAL' THEN 5 ELSE 6 END)
        ] AS severity,
        MAX(cvss_score) AS cvss_score,
        MAX(epss_score) AS epss_score,
        COUNT(*) AS finding_count,
        COUNT(DISTINCT resource_id) AS affected_resources,
        STRING_AGG(DISTINCT resource_type, ', ') AS resource_types,
        STRING_AGG(DISTINCT resource_name, ', ') AS resource_names,
        STRING_AGG(DISTINCT package_name, ', ') AS packages,
        CASE WHEN BOOL_OR(fix_available IN ('YES', 'PARTIAL')) THEN 'YES' ELSE 'NO' END AS fix_available,
        CASE WHEN BOOL_OR(exploit_available = 'YES') THEN 'YES' ELSE 'NO' END AS exploit_available,
        MIN(first_observed_at) AS first_observed_at,
        MAX(last_observed_at) AS last_observed_at,
        MAX(source_url) AS source_url
    FROM inspector_findings
    WHERE status = 'ACTIVE'
      AND cve_id IS NOT NULL AND cve_id <> ''
    GROUP BY account_id, cve_id
) c
    JOIN accounts a ON c.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;
