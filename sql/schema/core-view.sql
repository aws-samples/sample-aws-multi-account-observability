-- Views for all tables with additional columns
-- account: account_id from accounts table
-- account_full: account_id + "-" + account_name
-- project_product_name: product name from products table via product_accounts junction

-- 1. Accounts view
CREATE OR REPLACE VIEW view_accounts AS
SELECT
    a.*,
    a.account_id as account,
    a.category as account_category,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

-- 2. Contact info view
CREATE OR REPLACE VIEW view_contact_info AS
SELECT
    ci.*,
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
    contact_info ci
    JOIN accounts a ON ci.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- 3. Alternate contacts view
CREATE OR REPLACE VIEW view_alternate_contacts AS
SELECT
    ac.*,
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
    alternate_contacts ac
    JOIN accounts a ON ac.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- 4. Services view
CREATE OR REPLACE VIEW view_acct_serv AS
SELECT
    s.*,
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
    services s
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

-- 5. Cost reports view
CREATE OR REPLACE VIEW view_acct_cost_rep AS
SELECT
    cr.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

--6.  Service costs view
CREATE OR REPLACE VIEW view_acct_serv_cost AS
SELECT
    sc.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

--7. Cost forecasts view
CREATE OR REPLACE VIEW view_acct_cost_rep_forecast AS
SELECT
    cf.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

--8. Security view
CREATE OR REPLACE VIEW view_acct_security AS
SELECT
    s.*,
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
    security s
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--9. Findings view
CREATE OR REPLACE VIEW view_acct_security_findings_details AS
SELECT
    f.*,
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
    findings f
    JOIN security s ON f.security_id = s.id
    JOIN accounts a ON s.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--10. Products view
CREATE OR REPLACE VIEW view_products AS
SELECT
    pr.*,
    NULL as account,
    NULL as account_region,
    NULL as account_name,
    NULL as account_type,
    NULL as account_category,
    NULL as account_status,
    NULL as account_partner,
    NULL as account_customer,
    NULL as account_full,
    pr.name as project_product_name
FROM
    products pr;

--11. Product accounts view
CREATE OR REPLACE VIEW view_product_acct AS
SELECT
    pa.*,
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
    product_accounts pa
    JOIN accounts a ON pa.account_id = a.id
    JOIN products p ON pa.product_id = p.id;

--12. Products view with account relationships (CORRECTED)
CREATE OR REPLACE VIEW view_acct_products AS
SELECT
    p.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

--13. Logs view
CREATE OR REPLACE VIEW view_acct_logs AS
SELECT
    l.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as acct_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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

--14. Log messages view
CREATE OR REPLACE VIEW view_acct_log_messages AS
SELECT
    lm.*,
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
    log_messages lm
    JOIN logs l ON lm.log_id = l.id
    JOIN accounts a ON l.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--15. Config reports view
CREATE OR REPLACE VIEW view_config_reports AS
SELECT
    cr.*,
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
    config_reports cr
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--16. Non compliant resources view
CREATE OR REPLACE VIEW view_non_compliant_resources AS
SELECT
    ncr.*,
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
    non_compliant_resources ncr
    JOIN config_reports cr ON ncr.config_report_id = cr.id
    JOIN accounts a ON cr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--17. Service resources view
CREATE OR REPLACE VIEW view_service_resources AS
SELECT
    sr.*,
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
    service_resources sr
    JOIN accounts a ON sr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;


--18. Create summary view
CREATE OR REPLACE VIEW view_service_resources_summary AS
SELECT
    a.account_id,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    sr.service_name,
    sr.resource_type,
    sr.region as resource_region,
    sr.availability_zone,
    COUNT(*) as resource_count,
    COUNT(CASE WHEN sr.state IN ('running', 'available', 'Active') THEN 1 END) as active_resources,
    COUNT(CASE WHEN sr.state IN ('stopped', 'Inactive') THEN 1 END) as inactive_resources
FROM service_resources sr
LEFT JOIN accounts a ON sr.account_id = a.id
GROUP BY a.account_id, a.region, a.account_name, a.account_type, a.category, a.account_status, a.partner_name, a.customer_name, sr.service_name, sr.resource_type, sr.region, sr.availability_zone;

--19. Compute optimizers view
CREATE OR REPLACE VIEW view_compute_optimizer AS
SELECT
    co.*,
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
    compute_optimizer co
    LEFT JOIN accounts a ON co.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--20. Guard duty findings view
CREATE OR REPLACE VIEW view_guard_duty_findings AS
SELECT
    gdf.*,
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
    guard_duty_findings gdf
    JOIN accounts a ON gdf.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--21. KMS keys view
CREATE OR REPLACE VIEW view_kms_keys AS
SELECT
    kk.*,
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
    kms_keys kk
    JOIN accounts a ON kk.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--22. WAF rules view
CREATE OR REPLACE VIEW view_waf_rules AS
SELECT
    wr.*,
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
    waf_rules wr
    JOIN accounts a ON wr.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--23. WAF Rules detailed view
CREATE OR REPLACE VIEW view_waf_rules_detailed AS
SELECT
    wrd.*,
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
    waf_rules_detailed wrd
    JOIN accounts a ON wrd.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--24. CloudTrail logs view
CREATE OR REPLACE VIEW view_cloudtrail_logs AS
SELECT
    ctl.*,
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
    cloudtrail_logs ctl
    JOIN accounts a ON ctl.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--25. Secrets manager secrets view
CREATE OR REPLACE VIEW view_secrets_manager_secrets AS
SELECT
    sms.*,
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
    secrets_manager_secrets sms
    JOIN accounts a ON sms.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--26. Certificates view
CREATE OR REPLACE VIEW view_certificates AS
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

--27. Inspector findings view
CREATE OR REPLACE VIEW view_inspector_findings AS
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

--28. Inventory instances view
CREATE OR REPLACE VIEW view_inventory_instances AS
SELECT
    ii.*,
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
    inventory_instances ii
    JOIN accounts a ON ii.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--29. Inventory applications view
CREATE OR REPLACE VIEW view_inventory_applications AS
SELECT
    ia.*,
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
    inventory_applications ia
    JOIN inventory_instances ii ON ia.instance_id = ii.id
    JOIN accounts a ON ia.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--30. Inventory patches view
CREATE OR REPLACE VIEW view_inventory_patches AS
SELECT
    ip.*,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    CONCAT (a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    ii.instance_id as instance_name,
    ii.instance_type
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

--31. Marketplace usage view
CREATE OR REPLACE VIEW view_marketplace_usage AS
SELECT
    mu.*,
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
    marketplace_usage mu
    JOIN accounts a ON mu.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--32. Trusted advisor checks view
CREATE OR REPLACE VIEW view_trusted_advisor_checks AS
SELECT
    tac.*,
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
    trusted_advisor_checks tac
    JOIN accounts a ON tac.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--33. Health events view
CREATE OR REPLACE VIEW view_health_events AS
SELECT
    he.*,
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
    health_events he
    JOIN accounts a ON he.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--34. Application signals view
CREATE OR REPLACE VIEW view_application_signals AS
SELECT
    as_.*,
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
    application_signals as_
    JOIN accounts a ON as_.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--35. Resilience hub apps view
CREATE OR REPLACE VIEW view_resilience_hub_apps AS
SELECT
    rha.*,
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
    resilience_hub_apps rha
    JOIN accounts a ON rha.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--36. Summary view with product count only
CREATE OR REPLACE VIEW view_summary AS
SELECT
    -- Account Identifiers
    a.id as account_id,
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    a.csp as account_csp,

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

--37. Account summary view (CORRECTED - single version)
CREATE OR REPLACE VIEW view_acct_summary AS
SELECT
    a.*,
    a.account_id as account,
    a.region as account_region,
    a.category as account_category,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    
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

--38. Product summary view with individual products
CREATE OR REPLACE VIEW view_product_summary AS
SELECT
    -- Account Identifiers
    a.id as account_id,
    a.account_id as account,
    a.region as account_region,
    a.account_name,

    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    a.csp as account_csp,
    a.account_type as account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,

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

--39. Security findings summary view
CREATE OR REPLACE VIEW view_acct_security_findings_summary AS
SELECT
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
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
    'N/A' as region_finding,
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

--40. Compute Optimizer View
CREATE OR REPLACE VIEW view_compute_optimizer_summary AS
SELECT
    a.account_id as account,
    a.region as account_region,
    a.account_name,
    a.account_type,
    a.category as account_category,
    a.account_status as account_status,
    a.partner_name as account_partner,
    a.customer_name as account_customer,
    CONCAT(a.account_id, '-', a.account_name) as account_full,
    p.name as project_product_name,
    co.resource_type,
    co.finding,
    COUNT(*) as resource_count,
    SUM(co.estimated_monthly_savings_usd) as total_monthly_savings,
    AVG(co.savings_opportunity_percentage) as avg_savings_percentage,
    AVG(co.performance_risk) as avg_performance_risk,
    COUNT(CASE WHEN co.finding = 'NotOptimized' THEN 1 END) as not_optimized_count,
    COUNT(CASE WHEN co.estimated_monthly_savings_usd > 0 THEN 1 END) as savings_opportunities
FROM compute_optimizer co
LEFT JOIN accounts a ON co.account_id = a.id
LEFT JOIN (
    SELECT DISTINCT ON (account_id) account_id, product_id
    FROM product_accounts
    ORDER BY account_id, id
) pa ON a.id = pa.account_id
LEFT JOIN products p ON pa.product_id = p.id
GROUP BY a.account_id, a.region, a.account_name, a.account_type, a.category, a.account_status, a.partner_name, a.customer_name, p.name, co.resource_type, co.finding;

--41. Create a Support Tickets View
CREATE OR REPLACE VIEW view_acct_support_tickets AS
SELECT
    st.*,
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
    support_tickets st
    JOIN accounts a ON st.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;

--42. Create a Savings Plan and Reserved Instances View
CREATE OR REPLACE VIEW view_ri_sp_daily_savings AS
SELECT
    r.*,
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
    ri_sp_daily_savings r
    JOIN accounts a ON r.account_id = a.id
    LEFT JOIN (
        SELECT DISTINCT ON (account_id) account_id, product_id
        FROM product_accounts
        ORDER BY account_id, id
    ) pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id;