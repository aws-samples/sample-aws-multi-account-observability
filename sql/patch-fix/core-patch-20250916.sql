
-- Updating Tables to delete on cascade
ALTER TABLE contact_info DROP CONSTRAINT contact_info_account_id_fkey;
ALTER TABLE contact_info ADD CONSTRAINT contact_info_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE;

ALTER TABLE alternate_contacts DROP CONSTRAINT alternate_contacts_account_id_fkey;
ALTER TABLE alternate_contacts ADD CONSTRAINT alternate_contacts_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE;

ALTER TABLE logs DROP CONSTRAINT logs_account_id_fkey;
ALTER TABLE logs ADD CONSTRAINT logs_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE inventory_instances DROP CONSTRAINT inventory_instances_account_id_fkey;
ALTER TABLE inventory_instances ADD CONSTRAINT inventory_instances_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE services DROP CONSTRAINT services_account_id_fkey;
ALTER TABLE services ADD CONSTRAINT services_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE cost_reports DROP CONSTRAINT cost_reports_account_id_fkey;
ALTER TABLE cost_reports ADD CONSTRAINT cost_reports_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE security DROP CONSTRAINT security_account_id_fkey;
ALTER TABLE security ADD CONSTRAINT security_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE product_accounts DROP CONSTRAINT product_accounts_account_id_fkey;
ALTER TABLE product_accounts ADD CONSTRAINT product_accounts_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE service_costs DROP CONSTRAINT service_costs_cost_report_id_fkey;
ALTER TABLE service_costs ADD CONSTRAINT service_costs_cost_report_id_fkey 
    FOREIGN KEY (cost_report_id) REFERENCES cost_reports(id) ON DELETE CASCADE;

ALTER TABLE cost_forecasts DROP CONSTRAINT cost_forecasts_cost_report_id_fkey;
ALTER TABLE cost_forecasts ADD CONSTRAINT cost_forecasts_cost_report_id_fkey 
    FOREIGN KEY (cost_report_id) REFERENCES cost_reports(id) ON DELETE CASCADE;

ALTER TABLE findings DROP CONSTRAINT findings_security_id_fkey;
ALTER TABLE findings ADD CONSTRAINT findings_security_id_fkey 
    FOREIGN KEY (security_id) REFERENCES security(id) ON DELETE CASCADE;

ALTER TABLE log_messages DROP CONSTRAINT log_messages_log_id_fkey;
ALTER TABLE log_messages ADD CONSTRAINT log_messages_log_id_fkey 
    FOREIGN KEY (log_id) REFERENCES logs(id) ON DELETE CASCADE;

ALTER TABLE waf_rules_detailed DROP CONSTRAINT waf_rules_detailed_account_id_fkey;
ALTER TABLE waf_rules_detailed ADD CONSTRAINT waf_rules_detailed_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE config_reports DROP CONSTRAINT config_reports_account_id_fkey;
ALTER TABLE config_reports ADD CONSTRAINT config_reports_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE guard_duty_findings DROP CONSTRAINT guard_duty_findings_account_id_fkey;
ALTER TABLE guard_duty_findings ADD CONSTRAINT guard_duty_findings_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE certificates DROP CONSTRAINT certificates_account_id_fkey;
ALTER TABLE certificates ADD CONSTRAINT certificates_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE inspector_findings DROP CONSTRAINT inspector_findings_account_id_fkey;
ALTER TABLE inspector_findings ADD CONSTRAINT inspector_findings_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE inventory_applications DROP CONSTRAINT inventory_applications_account_id_fkey;
ALTER TABLE inventory_applications ADD CONSTRAINT inventory_applications_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE inventory_patches DROP CONSTRAINT inventory_patches_account_id_fkey;
ALTER TABLE inventory_patches ADD CONSTRAINT inventory_patches_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE marketplace_usage DROP CONSTRAINT marketplace_usage_account_id_fkey;
ALTER TABLE marketplace_usage ADD CONSTRAINT marketplace_usage_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE trusted_advisor_checks DROP CONSTRAINT trusted_advisor_checks_account_id_fkey;
ALTER TABLE trusted_advisor_checks ADD CONSTRAINT trusted_advisor_checks_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE health_events DROP CONSTRAINT health_events_account_id_fkey;
ALTER TABLE health_events ADD CONSTRAINT health_events_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE application_signals DROP CONSTRAINT application_signals_account_id_fkey;
ALTER TABLE application_signals ADD CONSTRAINT application_signals_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;

ALTER TABLE resilience_hub_apps DROP CONSTRAINT resilience_hub_apps_account_id_fkey;
ALTER TABLE resilience_hub_apps ADD CONSTRAINT resilience_hub_apps_account_id_fkey 
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE;


-- Alter account table to add partner and customer name
ALTER TABLE accounts 
ADD COLUMN partner_name TEXT DEFAULT 'None',
ADD COLUMN customer_name TEXT DEFAULT 'None',
ADD COLUMN category TEXT DEFAULT 'Internet';


-- Create new service_resources table
CREATE TABLE service_resources (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    service_name VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    region VARCHAR(50),
    availability_zone VARCHAR(50),
    state VARCHAR(50),
    instance_type VARCHAR(50),
    vpc_id VARCHAR(255),
    engine VARCHAR(100),
    instance_class VARCHAR(100),
    multi_az BOOLEAN,
    size_gb INTEGER,
    volume_type VARCHAR(50),
    creation_date TIMESTAMP WITH TIME ZONE,
    type VARCHAR(100),
    scheme VARCHAR(50),
    instance_count INTEGER,
    min_size INTEGER,
    max_size INTEGER,
    available_ip_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_service_resources_account_id ON service_resources(account_id);
CREATE INDEX idx_service_resources_service_name ON service_resources(service_name);
CREATE INDEX idx_service_resources_resource_type ON service_resources(resource_type);
CREATE INDEX idx_service_resources_region ON service_resources(region);
CREATE INDEX idx_service_resources_availability_zone ON service_resources(availability_zone);
CREATE INDEX idx_service_resources_state ON service_resources(state);

-- Create view
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


-- Compute Optimizer
-- Drop existing compute_optimizer table and related objects if they exist
DROP VIEW IF EXISTS view_compute_optimizer_summary CASCADE;
DROP VIEW IF EXISTS view_compute_optimizer CASCADE;
DROP TABLE IF EXISTS compute_optimizer_recommendations CASCADE;
DROP TABLE IF EXISTS compute_optimizer CASCADE;

-- Create new compute_optimizer table
CREATE TABLE compute_optimizer (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(12) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_arn VARCHAR(255) NOT NULL,
    resource_name VARCHAR(255),
    finding VARCHAR(50),
    current_instance_type VARCHAR(50),
    current_memory_size INTEGER,
    current_volume_type VARCHAR(50),
    current_volume_size INTEGER,
    recommended_instance_type VARCHAR(50),
    recommended_memory_size INTEGER,
    recommended_volume_type VARCHAR(50),
    recommended_volume_size INTEGER,
    savings_opportunity_percentage DECIMAL(5,2),
    estimated_monthly_savings_usd DECIMAL(10,2),
    performance_risk DECIMAL(3,2),
    cpu_utilization_max DECIMAL(5,2),
    memory_utilization_avg DECIMAL(5,2),
    migration_effort VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_compute_optimizer_account_id ON compute_optimizer(account_id);
CREATE INDEX idx_compute_optimizer_resource_type ON compute_optimizer(resource_type);
CREATE INDEX idx_compute_optimizer_finding ON compute_optimizer(finding);
CREATE INDEX idx_compute_optimizer_savings ON compute_optimizer(estimated_monthly_savings_usd);
CREATE INDEX idx_compute_optimizer_performance_risk ON compute_optimizer(performance_risk);


-- Create main view
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


-- Create config_inventory table
CREATE TABLE config_inventory (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    resource_type VARCHAR(255) NOT NULL,
    resource_subtype VARCHAR(255),
    resource_id VARCHAR(255) NOT NULL,
    resource_name VARCHAR(255),
    region VARCHAR(50),
    availability_zone VARCHAR(50),
    state VARCHAR(50),
    instance_type VARCHAR(50),
    instance_class VARCHAR(100),
    engine VARCHAR(100),
    vpc_id VARCHAR(255),
    size_gb INTEGER,
    volume_type VARCHAR(50),
    creation_date TIMESTAMP WITH TIME ZONE,
    multi_az BOOLEAN,
    scheme VARCHAR(50),
    type VARCHAR(100),
    instance_count INTEGER,
    min_size INTEGER,
    max_size INTEGER,
    available_ip_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_config_inventory_account_id ON config_inventory(account_id);
CREATE INDEX idx_config_inventory_resource_type ON config_inventory(resource_type);
CREATE INDEX idx_config_inventory_resource_subtype ON config_inventory(resource_subtype);
CREATE INDEX idx_config_inventory_resource_id ON config_inventory(resource_id);
CREATE INDEX idx_config_inventory_region ON config_inventory(region);
CREATE INDEX idx_config_inventory_availability_zone ON config_inventory(availability_zone);
CREATE INDEX idx_config_inventory_state ON config_inventory(state);
CREATE INDEX idx_config_inventory_vpc_id ON config_inventory(vpc_id);
CREATE INDEX idx_config_inventory_creation_date ON config_inventory(creation_date);

-- Create unique constraint for account + resource_id
CREATE UNIQUE INDEX idx_config_inventory_unique_resource ON config_inventory(account_id, resource_id);

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