/* To Drop Views */
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


/* To Drop Views */
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


-- Example Scripts: to Creating Products
INSERT INTO products (name, owner, position, description) VALUES
('Cloud Infrastructure Platform', 'John Smith', 'Platform Engineering Manager', 'Core cloud infrastructure and platform services')

-- Example Script: Associate accounts with products (each product gets 2 accounts)
INSERT INTO product_accounts (product_id, account_id) 
SELECT p.id, a.id 
FROM products p 
CROSS JOIN accounts a 
WHERE a.account_id IN ('123456789012', '234567890123', '345678901234', '456789012345')
AND (
  (p.name = 'Cloud Infrastructure Platform' AND a.account_id IN ('123456789012', '234567890123')) OR
  (p.name = 'Data Analytics Suite' AND a.account_id IN ('345678901234', '456789012345')) 
);