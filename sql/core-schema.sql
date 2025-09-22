-- Create the main accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(12) NOT NULL UNIQUE,
    account_name VARCHAR(255) NOT NULL,
    account_email VARCHAR(255) NOT NULL,
    account_status VARCHAR(50) NOT NULL,
    account_arn VARCHAR(255) NOT NULL,
    partner_name  TEXT DEFAULT 'None',
    customer_name  TEXT DEFAULT 'None',
    joined_method VARCHAR(50) NOT NULL,
    joined_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    account_type VARCHAR(50),
    csp VARCHAR(50),
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the contact_info table
CREATE TABLE contact_info (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(12) REFERENCES accounts(account_id) ON DELETE CASCADE,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    address_line3 VARCHAR(255),
    city VARCHAR(100),
    country_code VARCHAR(2),
    postal_code VARCHAR(20),
    state_or_region VARCHAR(100),
    company_name VARCHAR(255),
    phone_number VARCHAR(20),
    website_url VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id)
);

-- Create the alternate_contacts table
CREATE TABLE alternate_contacts (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(12) REFERENCES accounts(account_id) ON DELETE CASCADE,
    contact_type VARCHAR(50) NOT NULL,  -- 'billing', 'operations', 'security'
    full_name VARCHAR(255),
    title VARCHAR(255),
    email VARCHAR(255),
    phone_number VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, contact_type)
);



/* Services Table Schema */
-- Create the services table
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    service VARCHAR(255) NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    cost DECIMAL(20,10) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    utilization DECIMAL(20,10),
    utilization_unit VARCHAR(100),
    usage_types TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT date_check CHECK (date_to >= date_from),
    UNIQUE (account_id, service, date_from)
);


/*Cost Table Schema*/
-- Create enum for period granularity
CREATE TYPE period_granularity_type AS ENUM ('MONTHLY', 'WEEKLY', 'DAILY');

-- Create the main cost reports table
CREATE TABLE cost_reports (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    current_period_cost NUMERIC(20,10) NOT NULL,
    previous_period_cost NUMERIC(20,10) NOT NULL,
    cost_difference NUMERIC(20,10) NOT NULL,
    cost_difference_percentage NUMERIC(20,10) NOT NULL,
    potential_monthly_savings NUMERIC(20,10) DEFAULT 0,
    anomalies_detected INTEGER DEFAULT 0,
    saving_opportunities_count INTEGER DEFAULT 0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_granularity period_granularity_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, period_start)
);

-- Create the services cost table for top services
CREATE TABLE service_costs (
    id SERIAL PRIMARY KEY,
    cost_report_id INTEGER REFERENCES cost_reports(id) ON DELETE CASCADE,
    service_name VARCHAR(255) NOT NULL,
    cost NUMERIC(20,10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the forecast table
CREATE TABLE cost_forecasts (
    id SERIAL PRIMARY KEY,
    cost_report_id INTEGER REFERENCES cost_reports(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount NUMERIC(20,10) NOT NULL,
    prediction_interval_lower_bound NUMERIC(20,10),
    prediction_interval_upper_bound NUMERIC(20,10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


/* Security */

-- Create the security table

CREATE TABLE security (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    service VARCHAR(255) NOT NULL,
    total_findings INTEGER NOT NULL DEFAULT 0,
    critical_count INTEGER NOT NULL DEFAULT 0,
    high_count INTEGER NOT NULL DEFAULT 0,
    medium_count INTEGER NOT NULL DEFAULT 0,
    low_count INTEGER NOT NULL DEFAULT 0,
    informational_count INTEGER NOT NULL DEFAULT 0,
    open_findings INTEGER NOT NULL DEFAULT 0,
    resolved_findings INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, service)
);

-- Create the findings table
CREATE TABLE findings (
    id SERIAL PRIMARY KEY,
    security_id INTEGER NOT NULL REFERENCES security(id) ON DELETE CASCADE,
    finding_id VARCHAR(255) NOT NULL,
    service VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    recommendation TEXT,
    compliance_status VARCHAR(50),
    region VARCHAR(50),
    workflow_state VARCHAR(50),
    record_state VARCHAR(50),
    product_name VARCHAR(255),
    company_name VARCHAR(255),
    product_arn VARCHAR(255),
    generator_id VARCHAR(255),
    generator VARCHAR(255),
    UNIQUE(finding_id)
);

/* Create Product Table */
-- Create the products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the product_accounts junction table
CREATE TABLE product_accounts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, account_id)
);


-- Create the logs table
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    date_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    account_status VARCHAR(50) DEFAULT 'Pass',
    cost_status VARCHAR(50) DEFAULT 'Pass',
    service_status VARCHAR(50) DEFAULT 'Pass',
    security_status VARCHAR(50) DEFAULT 'Pass',
    config_status VARCHAR(50) DEFAULT 'Pass',
    inventory_status VARCHAR(50) DEFAULT 'Pass',
    marketplace_status VARCHAR(50) DEFAULT 'Pass',
    trusted_advisor_status VARCHAR(50) DEFAULT 'Pass',
    health_status VARCHAR(50) DEFAULT 'Pass',
    application_status VARCHAR(50) DEFAULT 'Pass',
    resilience_hub_status VARCHAR(50) DEFAULT 'Pass',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, date_created)
);

-- Create the log_messages table for storing messages
CREATE TABLE log_messages (
    id SERIAL PRIMARY KEY,
    log_id INTEGER NOT NULL REFERENCES logs(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    message_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

/* NEW TABLES FOR EXPANDED DATA - ADD TO EXISTING SCHEMA */
-- Config compliance reports
CREATE TABLE config_reports (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    compliance_score NUMERIC(5,2),
    total_rules INTEGER,
    compliant_rules INTEGER,
    non_compliant_rules INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, date_from)
);

CREATE TABLE non_compliant_resources (
    id SERIAL PRIMARY KEY,
    config_report_id INTEGER REFERENCES config_reports(id) ON DELETE CASCADE,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    compliance_type VARCHAR(50),
    rule_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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



-- Compute Optimizer 
CREATE TABLE compute_optimizer (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
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

-- Security services
CREATE TABLE guard_duty_findings (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    detector_id VARCHAR(255),
    finding_type VARCHAR(255),
    severity NUMERIC(3,1),
    title TEXT,
    description TEXT,
    confidence NUMERIC(3,1),
    region VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE kms_keys (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    key_id VARCHAR(255),
    arn VARCHAR(255),
    description TEXT,
    key_usage VARCHAR(50),
    key_state VARCHAR(50),
    creation_date TIMESTAMP WITH TIME ZONE,
    enabled BOOLEAN DEFAULT TRUE,
    key_rotation_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE waf_rules (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255),
    waf_id VARCHAR(255),
    arn VARCHAR(255),
    scope VARCHAR(50),
    description TEXT,
    default_action JSONB,
    rules_count INTEGER DEFAULT 0,
    logging_enabled BOOLEAN DEFAULT FALSE,
    geo_blocking_enabled BOOLEAN DEFAULT FALSE,
    blocked_countries TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- WAF Rules detailed table
CREATE TABLE waf_rules_detailed (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    web_acl_name VARCHAR(255) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    priority INTEGER NOT NULL,
    action TEXT,
    statement_type VARCHAR(100),
    is_managed_rule BOOLEAN DEFAULT FALSE,
    is_custom_rule BOOLEAN DEFAULT TRUE,
    rate_limit BOOLEAN DEFAULT FALSE,
    logging_enabled BOOLEAN DEFAULT FALSE,
    geo_blocking BOOLEAN DEFAULT FALSE,
    sql_injection BOOLEAN DEFAULT FALSE,
    sample_request_enabled BOOLEAN DEFAULT FALSE,
    cloudwatch_enabled BOOLEAN DEFAULT FALSE,
    has_xss_protection BOOLEAN DEFAULT FALSE,
    waf_version VARCHAR(10) DEFAULT 'v2',
    is_compliant BOOLEAN DEFAULT FALSE,
    scope VARCHAR(20) DEFAULT 'REGIONAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, web_acl_name, rule_name)
);

CREATE TABLE cloudtrail_logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255),
    arn VARCHAR(255),
    is_logging BOOLEAN DEFAULT FALSE,
    is_multi_region BOOLEAN DEFAULT FALSE,
    s3_bucket VARCHAR(255),
    kms_key_id VARCHAR(255),
    log_file_validation BOOLEAN DEFAULT FALSE,
    latest_delivery_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (arn)
);

CREATE TABLE secrets_manager_secrets (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    name VARCHAR(255),
    arn VARCHAR(255),
    description TEXT,
    created_date TIMESTAMP WITH TIME ZONE,
    last_changed_date TIMESTAMP WITH TIME ZONE,
    rotation_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (arn)
);

CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    arn VARCHAR(255),
    domain_name VARCHAR(255),
    status VARCHAR(50),
    type VARCHAR(50),
    not_after TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (arn)
);

CREATE TABLE inspector_findings (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    finding_arn VARCHAR(255),
    severity VARCHAR(50),
    status VARCHAR(50),
    type VARCHAR(100),
    title TEXT,
    description TEXT,
    first_observed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (finding_arn)
);

-- Inventory tables
CREATE TABLE inventory_instances (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instance_id VARCHAR(255),
    instance_type VARCHAR(50),
    platform VARCHAR(50),
    ip_address VARCHAR(45),
    computer_name VARCHAR(255),
    ping_status VARCHAR(50),
    last_ping_date_time TIMESTAMP WITH TIME ZONE,
    agent_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (instance_id)
);

CREATE TABLE inventory_applications (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instance_id INTEGER REFERENCES inventory_instances(id) ON DELETE CASCADE,
    name VARCHAR(255),
    version VARCHAR(100),
    publisher VARCHAR(255),
    install_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_patches (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    instance_id INTEGER REFERENCES inventory_instances(id) ON DELETE CASCADE,
    title VARCHAR(255),
    classification VARCHAR(100),
    severity VARCHAR(50),
    state VARCHAR(50),
    installed_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Marketplace usage
CREATE TABLE marketplace_usage (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    product_code VARCHAR(255),
    product_name VARCHAR(255),
    cost_consumed NUMERIC(20,10),
    currency VARCHAR(3) DEFAULT 'USD',
    period_start DATE,
    period_end DATE,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, product_code, period_start)
);

-- Trusted Advisor checks
CREATE TABLE trusted_advisor_checks (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    check_name VARCHAR(255),
    category VARCHAR(100),
    severity VARCHAR(50),
    recommendation TEXT,
    affected_resources_count INTEGER DEFAULT 0,
    potential_savings NUMERIC(20,10),
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, check_name)
);

-- Health events
CREATE TABLE health_events (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    arn VARCHAR(255),
    service VARCHAR(100),
    event_type_code VARCHAR(255),
    region VARCHAR(50),
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    status_code VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (arn)
);

-- Application signals
CREATE TABLE application_signals (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    service_name VARCHAR(255),
    namespace VARCHAR(255),
    key_attributes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (account_id, service_name)
);

-- Resilience Hub assessments
CREATE TABLE resilience_hub_apps (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    app_arn VARCHAR(255),
    name VARCHAR(255),
    compliance_status VARCHAR(50),
    resiliency_score NUMERIC(5,2),
    status VARCHAR(50),
    cost NUMERIC(20,10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    creation_time TIMESTAMP WITH TIME ZONE,
    last_assessment_time TIMESTAMP WITH TIME ZONE,
    rpo INTEGER,
    rto INTEGER,
    last_drill TIMESTAMP WITH TIME ZONE,
    UNIQUE (app_arn)
);



/* Set Indexes */

-- Create indexes for better query performance
CREATE INDEX idx_accounts_account_id ON accounts(account_id);
CREATE INDEX idx_accounts_account_status ON accounts(account_status);
CREATE INDEX idx_contact_info_account_id ON contact_info(account_id);
CREATE INDEX idx_alternate_contacts_account_id ON alternate_contacts(account_id);

-- Accounts - Create indexes for better query performance
CREATE INDEX idx_services_account_id ON services(account_id);
CREATE INDEX idx_services_service ON services(service);
CREATE INDEX idx_services_date_range ON services(date_from, date_to);


-- Cost - Create indexes for better performance
CREATE INDEX idx_cost_reports_account_id ON cost_reports(account_id);
CREATE INDEX idx_service_costs_cost_report_id ON service_costs(cost_report_id);
CREATE INDEX idx_cost_forecasts_cost_report_id ON cost_forecasts(cost_report_id);
CREATE INDEX idx_cost_reports_period ON cost_reports(period_start, period_end);

-- Security -  Create indexes
CREATE INDEX idx_security_account_id ON security(account_id);
CREATE INDEX idx_security_service ON security(service);
CREATE INDEX idx_findings_security_id ON findings(security_id);
CREATE INDEX idx_findings_severity ON findings(severity);
CREATE INDEX idx_findings_status ON findings(status);
CREATE INDEX idx_findings_region ON findings(region);
CREATE INDEX idx_findings_generator ON findings(generator);

-- Products - Create indexes
CREATE INDEX idx_product_accounts_product_id ON product_accounts(product_id);
CREATE INDEX idx_product_accounts_account_id ON product_accounts(account_id);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_owner ON products(owner);

-- Create index for frequent queries
CREATE INDEX idx_logs_account_id ON logs(account_id);
CREATE INDEX idx_logs_date_created ON logs(date_created);
CREATE INDEX idx_log_messages_log_id ON log_messages(log_id);

-- Create index for frequent queries
CREATE INDEX idx_waf_rules_detailed_account_id ON waf_rules_detailed(account_id);
CREATE INDEX idx_waf_rules_detailed_web_acl ON waf_rules_detailed(web_acl_name);
CREATE INDEX idx_waf_rules_detailed_compliance ON waf_rules_detailed(is_compliant);
CREATE INDEX idx_waf_rules_detailed_managed ON waf_rules_detailed(is_managed_rule);

CREATE INDEX idx_config_reports_account_id ON config_reports(account_id);

CREATE INDEX idx_guard_duty_findings_account_id ON guard_duty_findings(account_id);
CREATE INDEX idx_inventory_instances_account_id ON inventory_instances(account_id);
CREATE INDEX idx_marketplace_usage_account_id ON marketplace_usage(account_id);
CREATE INDEX idx_trusted_advisor_checks_account_id ON trusted_advisor_checks(account_id);
CREATE INDEX idx_health_events_account_id ON health_events(account_id);
CREATE INDEX idx_application_signals_account_id ON application_signals(account_id);
CREATE INDEX idx_resilience_hub_apps_account_id ON resilience_hub_apps(account_id);

