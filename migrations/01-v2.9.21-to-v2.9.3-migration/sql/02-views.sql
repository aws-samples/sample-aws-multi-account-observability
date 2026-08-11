-- =============================================================================
-- Migration: v2.9.21 -> v2.9.3 - Views
-- =============================================================================
-- Must run AFTER 01-schema.sql, every table below has to exist first.
--
-- Same account-columns convention as every other view in core-view.sql:
--
--     <table>.*, then
--     a.account_id  AS account,
--     a.region      AS account_region,
--     a.account_name, a.account_type,
--     a.category    AS account_category,
--     a.account_status,
--     a.partner_name AS account_partner,
--     a.customer_name AS account_customer,
--     CONCAT(a.account_id, '-', a.account_name) AS account_full,
--     p.name        AS project_product_name
--
-- Then the same DISTINCT ON (account_id) product_accounts subquery LEFT JOINed
-- to products.
--
-- exposure_contributed_finding and exposure_finding_trait are child tables one
-- level down, so their views expose parent identifiers via extra columns
-- (exposure_finding_uid, contributed_finding_uid) rather than a raw pk id, to
-- make joins upward from a report readable
--
-- All views use CREATE OR REPLACE so a re-run picks up any change to the SELECT
-- list without needing DROP VIEW first
-- =============================================================================


-- [1]
CREATE OR REPLACE VIEW view_exposure_findings AS
SELECT
    ef.*,
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
FROM
    exposure_findings ef
    JOIN accounts a ON ef.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- [2]
CREATE OR REPLACE VIEW view_exposure_contributed_finding AS
SELECT
    ecf.*,
    ef.finding_id as exposure_finding_uid,
    ef.title as exposure_title,
    ef.severity as exposure_severity,
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
FROM
    exposure_contributed_finding ecf
    JOIN accounts a ON ecf.account_id = a.id
    JOIN exposure_findings ef ON ecf.exposure_finding_id = ef.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- [3]
CREATE OR REPLACE VIEW view_exposure_finding_trait AS
SELECT
    eft.*,
    ecf.finding_id as contributed_finding_uid,
    ecf.title as contributed_title,
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
FROM
    exposure_finding_trait eft
    JOIN accounts a ON eft.account_id = a.id
    JOIN exposure_contributed_finding ecf ON eft.contributed_finding_id = ecf.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- [4]
CREATE OR REPLACE VIEW view_threat_findings AS
SELECT
    tf.*,
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
FROM
    threat_findings tf
    JOIN accounts a ON tf.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- [5]
CREATE OR REPLACE VIEW view_security_standards AS
SELECT
    ss.*,
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
FROM
    security_standards ss
    JOIN accounts a ON ss.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- [6] Drop-then-create because view_ai_inventory may already exist from an earlier
--     partial run of this migration. Postgres CREATE OR REPLACE VIEW cannot change
--     the column order of an existing view, and the addition of the `status` column
--     to ai_inventory shifts the position of every column emitted via `ai.*` -
--     including `account`, which fails with "cannot change name of view column"
DROP VIEW IF EXISTS view_ai_inventory;

-- [7]
CREATE OR REPLACE VIEW view_ai_inventory AS
SELECT
    ai.*,
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
FROM
    ai_inventory ai
    JOIN accounts a ON ai.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;
