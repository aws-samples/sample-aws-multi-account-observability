-- Views for all tables with additional columns
-- account: account_id from accounts table
-- account_full: account_id + "-" + account_name
-- project_product_name: product name from products table via product_accounts junction

-- Accounts view
CREATE OR REPLACE VIEW view_accounts AS
SELECT
    a.*,
    a.account_id as account,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    accounts a
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Contact info view
CREATE OR REPLACE VIEW view_contact_info AS
SELECT
    ci.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    contact_info ci
    JOIN accounts a ON ci.account_id = a.account_id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Alternate contacts view
CREATE OR REPLACE VIEW view_alternate_contacts AS
SELECT
    ac.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    alternate_contacts ac
    JOIN accounts a ON ac.account_id = a.account_id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Services view
CREATE OR REPLACE VIEW view_acct_serv AS
SELECT
    s.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    services s
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Cost reports view
CREATE OR REPLACE VIEW view_acct_cost_rep AS
SELECT
    cr.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    cr.period_start as date_from,
    cr.period_end as date_to
FROM
    cost_reports cr
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Service costs view
CREATE OR REPLACE VIEW view_acct_serv_cost AS
SELECT
    sc.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    cr.period_start as date_from,
    cr.period_end as date_to
FROM
    service_costs sc
    JOIN cost_reports cr ON sc.cost_report_id = cr.id
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Cost forecasts view
CREATE OR REPLACE VIEW view_acct_cost_rep_forecast AS
SELECT
    cf.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    cr.period_start as date_from,
    cr.period_end as date_to
FROM
    cost_forecasts cf
    JOIN cost_reports cr ON cf.cost_report_id = cr.id
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Security view
CREATE OR REPLACE VIEW view_acct_security AS
SELECT
    s.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    security s
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Findings view
CREATE OR REPLACE VIEW view_acct_security_findings_details AS
SELECT
    f.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    findings f
    JOIN security s ON f.security_id = s.id
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Products view
CREATE OR REPLACE VIEW view_products AS
SELECT
    pr.*,
    NULL as account,
    NULL as account_name,
    NULL as account_full,
    pr.name as project_product_name
FROM
    products pr;

-- Product accounts view
CREATE OR REPLACE VIEW view_product_acct AS
SELECT
    pa.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    product_accounts pa
    JOIN accounts a ON pa.account_id = a.id
    JOIN products p ON pa.product_id = p.id;

-- Products view with account relationships (CORRECTED)
CREATE OR REPLACE VIEW view_acct_products AS
SELECT
    p.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    pr.name as project_product_name
FROM
    products p
    JOIN product_accounts pa ON p.id = pa.product_id
    JOIN accounts a ON pa.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa2 ON a.id = pa2.account_id
    LEFT JOIN products pr ON pa2.product_id = pr.id;

-- Logs view
CREATE OR REPLACE VIEW view_acct_logs AS
SELECT
    l.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    logs l
    JOIN accounts a ON l.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Log messages view
CREATE OR REPLACE VIEW view_acct_log_messages AS
SELECT
    lm.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    log_messages lm
    JOIN logs l ON lm.log_id = l.id
    JOIN accounts a ON l.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Config reports view
CREATE OR REPLACE VIEW view_config_reports AS
SELECT
    cr.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    config_reports cr
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Non compliant resources view
CREATE OR REPLACE VIEW view_non_compliant_resources AS
SELECT
    ncr.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    non_compliant_resources ncr
    JOIN config_reports cr ON ncr.config_report_id = cr.id
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Service resources view
CREATE OR REPLACE VIEW view_service_resources AS
SELECT
    sr.*,
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    service_resources sr
    JOIN accounts a ON sr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;


-- Create summary view
CREATE OR REPLACE VIEW view_service_resources_summary AS
SELECT 
    a.account_id,
    a.account_name,
    sr.service_name,
    sr.resource_type,
    sr.region,
    sr.availability_zone,
    COUNT(*) as resource_count,
    COUNT(CASE WHEN sr.state IN ('running', 'available', 'Active') THEN 1 END) as active_resources,
    COUNT(CASE WHEN sr.state IN ('stopped', 'Inactive') THEN 1 END) as inactive_resources
FROM service_resources sr
LEFT JOIN accounts a ON sr.account_id = a.id
GROUP BY a.account_id, a.account_name, sr.service_name, sr.resource_type, sr.region, sr.availability_zone;

-- Compute optimizers view
CREATE OR REPLACE VIEW view_compute_optimizer AS
SELECT
    co.*,
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    compute_optimizer co
    LEFT JOIN accounts a ON co.account_id = a.account_id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Create summary view
CREATE OR REPLACE VIEW view_compute_optimizer_summary AS
SELECT 
    a.account_id,
    a.account_name,
    co.resource_type,
    co.finding,
    COUNT(*) as total_recommendations,
    SUM(co.estimated_monthly_savings_usd) as total_monthly_savings,
    AVG(co.savings_opportunity_percentage) as avg_savings_percentage,
    AVG(co.performance_risk) as avg_performance_risk,
    COUNT(CASE WHEN co.finding = 'NotOptimized' THEN 1 END) as not_optimized_count,
    COUNT(CASE WHEN co.estimated_monthly_savings_usd > 0 THEN 1 END) as savings_opportunities
FROM compute_optimizer co
LEFT JOIN accounts a ON co.account_id = a.account_id
GROUP BY a.account_id, a.account_name, co.resource_type, co.finding;


-- Guard duty findings view
CREATE OR REPLACE VIEW view_guard_duty_findings AS
SELECT
    gdf.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    guard_duty_findings gdf
    JOIN accounts a ON gdf.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- KMS keys view
CREATE OR REPLACE VIEW view_kms_keys AS
SELECT
    kk.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    kms_keys kk
    JOIN accounts a ON kk.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- WAF rules view
CREATE OR REPLACE VIEW view_waf_rules AS
SELECT
    wr.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    waf_rules wr
    JOIN accounts a ON wr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- WAF Rules detailed view
CREATE OR REPLACE VIEW view_waf_rules_detailed AS
SELECT
    wrd.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    waf_rules_detailed wrd
    JOIN accounts a ON wrd.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- CloudTrail logs view
CREATE OR REPLACE VIEW view_cloudtrail_logs AS
SELECT
    ctl.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    cloudtrail_logs ctl
    JOIN accounts a ON ctl.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Secrets manager secrets view
CREATE OR REPLACE VIEW view_secrets_manager_secrets AS
SELECT
    sms.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    secrets_manager_secrets sms
    JOIN accounts a ON sms.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Certificates view
CREATE OR REPLACE VIEW view_certificates AS
SELECT
    c.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    certificates c
    JOIN accounts a ON c.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Inspector findings view
CREATE OR REPLACE VIEW view_inspector_findings AS
SELECT
    if.*,
    a.account_id as account,
    a.account_name,
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

-- Inventory instances view
CREATE OR REPLACE VIEW view_inventory_instances AS
SELECT
    ii.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    inventory_instances ii
    JOIN accounts a ON ii.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Inventory applications view
CREATE OR REPLACE VIEW view_inventory_applications AS
SELECT
    ia.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    inventory_applications ia
    JOIN inventory_instances ii ON ia.instance_id = ii.id
    JOIN accounts a ON ia.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Inventory patches view
CREATE OR REPLACE VIEW view_inventory_patches AS
SELECT
    ip.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    inventory_patches ip
    JOIN inventory_instances ii ON ip.instance_id = ii.id
    JOIN accounts a ON ip.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Marketplace usage view
CREATE OR REPLACE VIEW view_marketplace_usage AS
SELECT
    mu.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    marketplace_usage mu
    JOIN accounts a ON mu.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Trusted advisor checks view
CREATE OR REPLACE VIEW view_trusted_advisor_checks AS
SELECT
    tac.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    trusted_advisor_checks tac
    JOIN accounts a ON tac.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Health events view
CREATE OR REPLACE VIEW view_health_events AS
SELECT
    he.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    health_events he
    JOIN accounts a ON he.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Application signals view
CREATE OR REPLACE VIEW view_application_signals AS
SELECT
    as_.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    application_signals as_
    JOIN accounts a ON as_.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Resilience hub apps view
CREATE OR REPLACE VIEW view_resilience_hub_apps AS
SELECT
    rha.*,
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    resilience_hub_apps rha
    JOIN accounts a ON rha.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Summary view with product count only
CREATE OR REPLACE VIEW view_summary AS
SELECT
    -- Account Identifiers
    a.id as account_id,
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    a.csp as account_csp,
    a.account_type as account_type,
    a.account_status,

    -- Product Count
    COALESCE(pc.number_of_products, 0) as number_of_products,

    -- Cost Metrics
    cr.period_granularity,
    cr.period_start as date_from,
    cr.period_end as date_to,
    ROUND(cr.current_period_cost, 2) as current_period_cost,
    ROUND(cr.previous_period_cost, 2) as previous_period_cost,
    ROUND(cr.cost_difference, 2) as cost_difference,
    ROUND(cr.cost_difference_percentage, 4) as cost_difference_percentage,
    ROUND(cr.potential_monthly_savings, 2) as potential_savings,

    -- Service Metrics
    sm.service_count,
    sm.unique_services,
    ROUND(sm.total_service_cost, 2) as total_service_cost,
    sm.services_used,

    -- Security Metrics
    sec.total_findings,
    sec.open_findings,
    sec.resolved_findings,
    sec.critical_findings,
    sec.high_findings,
    sec.medium_findings,
    sec.low_findings,

    -- Calculated Security Metrics
    ROUND(sec.resolved_findings::DECIMAL / NULLIF(sec.total_findings, 0), 4) as security_resolution_rate,

    -- Account Information
    a.account_email,
    a.joined_method,
    a.joined_timestamp,
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, a.joined_timestamp)) as account_age_days

FROM accounts a
LEFT JOIN (
    SELECT DISTINCT ON (account_id, period_granularity)
        account_id, period_granularity, period_start, period_end,
        current_period_cost, previous_period_cost, cost_difference,
        cost_difference_percentage, potential_monthly_savings
    FROM cost_reports
    ORDER BY account_id, period_granularity, period_end DESC
) cr ON cr.account_id = a.id
LEFT JOIN (
    SELECT
        account_id,
        COUNT(DISTINCT id) as service_count,
        COUNT(DISTINCT service) as unique_services,
        SUM(cost) as total_service_cost,
        STRING_AGG(DISTINCT service, ', ') as services_used
    FROM services
    GROUP BY account_id
) sm ON sm.account_id = a.id
LEFT JOIN (
    SELECT
        account_id,
        SUM(total_findings) as total_findings,
        SUM(open_findings) as open_findings,
        SUM(resolved_findings) as resolved_findings,
        SUM(critical_count) as critical_findings,
        SUM(high_count) as high_findings,
        SUM(medium_count) as medium_findings,
        SUM(low_count) as low_findings
    FROM security
    GROUP BY account_id
) sec ON sec.account_id = a.id
LEFT JOIN (
    SELECT
        account_id,
        COUNT(DISTINCT product_id) as number_of_products
    FROM product_accounts
    GROUP BY account_id
) pc ON pc.account_id = a.id

WHERE
    (cr.period_granularity IS NULL OR
     cr.period_granularity::text IN ('MONTHLY', 'WEEKLY', 'DAILY'))

ORDER BY
    a.account_name,
    cr.period_start DESC;

-- Account summary view (CORRECTED - single version)
CREATE OR REPLACE VIEW view_acct_summary AS
SELECT
    a.*,
    a.account_id as account,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    -- Cost metrics
    COALESCE(cr.current_period_cost, 0) as latest_cost,
    COALESCE(cr.cost_difference_percentage, 0) as cost_trend_percentage,
    COALESCE(cr.potential_monthly_savings, 0) as savings_opportunity,
    -- Security metrics
    COALESCE(s.total_findings, 0) as security_findings,
    COALESCE(s.critical_count, 0) as critical_findings,
    COALESCE(s.high_count, 0) as high_findings,
    -- Inventory metrics
    COALESCE(i.instance_count, 0) as instance_count,
    COALESCE(i.running_instances, 0) as running_instances,
    -- Health score calculation
    CASE
        WHEN s.critical_count > 0 THEN 1
        WHEN s.high_count > 0 THEN 2
        WHEN s.medium_count > 0 THEN 3
        WHEN s.low_count > 0 THEN 4
        ELSE 5
    END as security_health_score
FROM
    accounts a
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id
    LEFT JOIN (
        SELECT account_id, current_period_cost, cost_difference_percentage, potential_monthly_savings
        FROM cost_reports
        WHERE period_granularity = 'MONTHLY'
        ORDER BY period_end DESC
        LIMIT 1
    ) cr ON cr.account_id = a.id
    LEFT JOIN (
        SELECT account_id, total_findings, critical_count, high_count, medium_count, low_count
        FROM security
        ORDER BY created_at DESC
        LIMIT 1
    ) s ON s.account_id = a.id
    LEFT JOIN (
        SELECT 
            account_id, 
            COUNT(*) as instance_count,
            COUNT(CASE WHEN ping_status = 'Online' THEN 1 END) as running_instances
        FROM inventory_instances
        GROUP BY account_id
    ) i ON i.account_id = a.id;

-- Product summary view with individual products
CREATE OR REPLACE VIEW view_product_summary AS
SELECT
    -- Account Identifiers
    a.id as account_id,
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    a.csp as account_csp,
    a.account_type as account_type,
    a.account_status,

    -- Product Details
    p.id as product_id,
    p.owner as product_owner,
    p.position as product_position,
    p.description as product_description,

    -- Cost Metrics
    cr.period_granularity,
    cr.period_start as date_from,
    cr.period_end as date_to,
    ROUND(cr.current_period_cost, 2) as current_period_cost,
    ROUND(cr.previous_period_cost, 2) as previous_period_cost,
    ROUND(cr.cost_difference, 2) as cost_difference,
    ROUND(cr.cost_difference_percentage, 4) as cost_difference_percentage,
    ROUND(cr.potential_monthly_savings, 2) as potential_savings,

    -- Service Metrics
    sm.service_count,
    sm.unique_services,
    ROUND(sm.total_service_cost, 2) as total_service_cost,
    sm.services_used,

    -- Security Metrics
    sec.total_findings,
    sec.open_findings,
    sec.resolved_findings,
    sec.critical_findings,
    sec.high_findings,
    sec.medium_findings,
    sec.low_findings,

    -- Calculated Security Metrics
    ROUND(sec.resolved_findings::DECIMAL / NULLIF(sec.total_findings, 0), 4) as security_resolution_rate,

    -- Account Information
    a.account_email,
    a.joined_method,
    a.joined_timestamp,
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, a.joined_timestamp)) as account_age_days

FROM accounts a
LEFT JOIN product_accounts pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id
LEFT JOIN (
    SELECT DISTINCT ON (account_id, period_granularity)
        account_id, period_granularity, period_start, period_end,
        current_period_cost, previous_period_cost, cost_difference,
        cost_difference_percentage, potential_monthly_savings
    FROM cost_reports
    ORDER BY account_id, period_granularity, period_end DESC
) cr ON cr.account_id = a.id
LEFT JOIN (
    SELECT
        account_id,
        COUNT(DISTINCT id) as service_count,
        COUNT(DISTINCT service) as unique_services,
        SUM(cost) as total_service_cost,
        STRING_AGG(DISTINCT service, ', ') as services_used
    FROM services
    GROUP BY account_id
) sm ON sm.account_id = a.id
LEFT JOIN (
    SELECT
        account_id,
        SUM(total_findings) as total_findings,
        SUM(open_findings) as open_findings,
        SUM(resolved_findings) as resolved_findings,
        SUM(critical_count) as critical_findings,
        SUM(high_count) as high_findings,
        SUM(medium_count) as medium_findings,
        SUM(low_count) as low_findings
    FROM security
    GROUP BY account_id
) sec ON sec.account_id = a.id

WHERE
    (cr.period_granularity IS NULL OR
     cr.period_granularity::text IN ('MONTHLY', 'WEEKLY', 'DAILY'))

ORDER BY
    a.account_name,
    p.name,
    cr.period_start DESC;

-- Security findings summary view
CREATE OR REPLACE VIEW view_acct_security_findings_summary AS
SELECT
    a.account_id as account,
    a.account_name,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    s.service,
    s.total_findings,
    s.critical_count,
    s.high_count,
    s.medium_count,
    s.low_count,
    s.informational_count,
    s.open_findings,
    s.resolved_findings,
    -- Calculated fields using available data
    0 as suppressed_count,
    0 as in_progress_count,
    s.open_findings as active_issues,
    'N/A' as region,
    s.resolved_findings as resolved_count,
    CASE
        WHEN s.critical_count > 0 THEN 'CRITICAL'
        WHEN s.high_count > 0 THEN 'HIGH'
        WHEN s.medium_count > 0 THEN 'MEDIUM'
        WHEN s.low_count > 0 THEN 'LOW'
        WHEN s.informational_count > 0 THEN 'INFORMATIONAL'
        ELSE 'CLEAN'
    END as severity,
    -- Calculated metrics
    ROUND(s.resolved_findings::DECIMAL / NULLIF(s.total_findings, 0) * 100, 2) as resolution_rate_percent,
    CASE
        WHEN s.critical_count > 0 THEN 'Critical'
        WHEN s.high_count > 0 THEN 'High'
        WHEN s.medium_count > 0 THEN 'Medium'
        WHEN s.low_count > 0 THEN 'Low'
        ELSE 'Clean'
    END as risk_level,
    s.created_at,
    s.updated_at
FROM
    security s
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Compute Optimizer View
CREATE OR REPLACE VIEW view_compute_optimizer_summary AS
SELECT 
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    cor.resource_type,
    cor.finding,
    COUNT(*) as resource_count,
    SUM(cor.estimated_monthly_savings_usd) as total_monthly_savings,
    AVG(cor.savings_opportunity_percentage) as avg_savings_percentage,
    AVG(cor.performance_risk) as avg_performance_risk,
    COUNT(CASE WHEN cor.finding = 'NotOptimized' THEN 1 END) as not_optimized_count,
    COUNT(CASE WHEN cor.estimated_monthly_savings_usd > 0 THEN 1 END) as savings_opportunities
FROM compute_optimizer_recommendations cor
LEFT JOIN accounts a ON cor.account_id = a.account_id
LEFT JOIN (
    SELECT DISTINCT ON (account_id) account_id, product_id
    FROM product_accounts
    ORDER BY account_id, id
) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id
GROUP BY a.account_id, a.account_name, p.name, cor.resource_type, cor.finding;


-- Create main view
CREATE OR REPLACE VIEW view_config_inventory AS
SELECT
    ci.*,
    a.account_id as account,
    a.account_name,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name
FROM
    config_inventory ci
    JOIN accounts a ON ci.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- Create summary view by resource type
CREATE OR REPLACE VIEW view_config_inventory_summary AS
SELECT 
    a.account_id,
    a.account_name,
    ci.resource_type,
    ci.resource_subtype,
    ci.region,
    ci.availability_zone,
    COUNT(*) as resource_count,
    COUNT(CASE WHEN ci.state IN ('running', 'available', 'Active', 'in-use') THEN 1 END) as active_resources,
    COUNT(CASE WHEN ci.state IN ('stopped', 'Inactive', 'terminated') THEN 1 END) as inactive_resources,
    SUM(CASE WHEN ci.size_gb IS NOT NULL THEN ci.size_gb ELSE 0 END) as total_storage_gb,
    COUNT(CASE WHEN ci.creation_date IS NOT NULL THEN 1 END) as resources_with_creation_date
FROM config_inventory ci
JOIN accounts a ON ci.account_id = a.id
GROUP BY a.account_id, a.account_name, ci.resource_type, ci.resource_subtype, ci.region, ci.availability_zone;

-- Create account-level summary view
CREATE OR REPLACE VIEW view_config_inventory_account_summary AS
SELECT 
    a.account_id,
    a.account_name,
    COUNT(*) as total_resources,
    COUNT(DISTINCT ci.resource_type) as unique_resource_types,
    COUNT(DISTINCT ci.region) as regions_used,
    COUNT(DISTINCT ci.availability_zone) as availability_zones_used,
    COUNT(CASE WHEN ci.state IN ('running', 'available', 'Active', 'in-use') THEN 1 END) as active_resources,
    SUM(CASE WHEN ci.size_gb IS NOT NULL THEN ci.size_gb ELSE 0 END) as total_storage_gb,
    COUNT(CASE WHEN ci.resource_type = 'EC2' THEN 1 END) as ec2_instances,
    COUNT(CASE WHEN ci.resource_type = 'RDS' THEN 1 END) as rds_instances,
    COUNT(CASE WHEN ci.resource_type = 'S3' THEN 1 END) as s3_buckets,
    COUNT(CASE WHEN ci.resource_type = 'EBS' THEN 1 END) as ebs_volumes,
    COUNT(CASE WHEN ci.resource_type = 'VPC' THEN 1 END) as vpc_resources
FROM config_inventory ci
JOIN accounts a ON ci.account_id = a.id
GROUP BY a.account_id, a.account_name;