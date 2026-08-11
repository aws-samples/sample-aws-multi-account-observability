-- Migration v2.9.21 -> v2.9.3, flattened. See sql/ for source.

-- [1]
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

-- [2]
CREATE INDEX IF NOT EXISTS idx_exposure_findings_account_id ON exposure_findings(account_id);

-- [3]
CREATE INDEX IF NOT EXISTS idx_exposure_findings_severity ON exposure_findings(severity);

-- [4]
CREATE INDEX IF NOT EXISTS idx_exposure_findings_status ON exposure_findings(status);

-- [5]
CREATE INDEX IF NOT EXISTS idx_exposure_findings_resource_id ON exposure_findings(resource_id);

-- [6]
CREATE INDEX IF NOT EXISTS idx_exposure_findings_cve_id ON exposure_findings(cve_id);

-- [7]
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

-- [8]
CREATE INDEX IF NOT EXISTS idx_ecf_account_id ON exposure_contributed_finding(account_id);

-- [9]
CREATE INDEX IF NOT EXISTS idx_ecf_exposure_finding_id ON exposure_contributed_finding(exposure_finding_id);

-- [10]
CREATE INDEX IF NOT EXISTS idx_ecf_cve_id ON exposure_contributed_finding(cve_id);

-- [11]
CREATE INDEX IF NOT EXISTS idx_ecf_status ON exposure_contributed_finding(status);

-- [12]
CREATE TABLE IF NOT EXISTS exposure_finding_trait (
    id                      SERIAL PRIMARY KEY,
    account_id              INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    contributed_finding_id  INTEGER NOT NULL REFERENCES exposure_contributed_finding(id) ON DELETE CASCADE,
    category                VARCHAR(64),
    name                    VARCHAR(512) NOT NULL,
    type                    VARCHAR(64) NOT NULL,
    UNIQUE NULLS NOT DISTINCT (contributed_finding_id, name, type)
);

-- [13]
CREATE INDEX IF NOT EXISTS idx_eft_account_id ON exposure_finding_trait(account_id);

-- [14]
CREATE INDEX IF NOT EXISTS idx_eft_contributed_finding_id ON exposure_finding_trait(contributed_finding_id);

-- [15]
CREATE INDEX IF NOT EXISTS idx_eft_category ON exposure_finding_trait(category);

-- [16]
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

-- [17]
CREATE INDEX IF NOT EXISTS idx_threat_findings_account_id ON threat_findings(account_id);

-- [18]
CREATE INDEX IF NOT EXISTS idx_threat_findings_severity ON threat_findings(severity);

-- [19]
CREATE INDEX IF NOT EXISTS idx_threat_findings_status ON threat_findings(status);

-- [20]
CREATE INDEX IF NOT EXISTS idx_threat_findings_finding_type ON threat_findings(finding_type);

-- [21]
CREATE INDEX IF NOT EXISTS idx_threat_findings_actor_uid ON threat_findings(actor_uid);

-- [22]
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

-- [23]
CREATE INDEX IF NOT EXISTS idx_security_standards_account_id ON security_standards(account_id);

-- [24]
CREATE INDEX IF NOT EXISTS idx_security_standards_name ON security_standards(standard_name);

-- [25]
CREATE INDEX IF NOT EXISTS idx_security_standards_date_from ON security_standards(date_from);

-- [26]
CREATE TABLE IF NOT EXISTS ai_inventory (
    id                     SERIAL PRIMARY KEY,
    account_id             INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    resource_guid          VARCHAR(255) NOT NULL,
    resource_id            VARCHAR(512) NOT NULL,
    resource_name          VARCHAR(512),
    resource_type          VARCHAR(255),
    resource_category      VARCHAR(100),
    resource_sub_category  VARCHAR(100),
    discovery_type         VARCHAR(100),
    region                 VARCHAR(50),
    host_resource_guid     VARCHAR(255),
    host_resource_type     VARCHAR(255),
    canonical_id           VARCHAR(512),
    model_count            INTEGER NOT NULL DEFAULT 0,
    agent_count            INTEGER NOT NULL DEFAULT 0,
    total_ai_count         INTEGER NOT NULL DEFAULT 0,
    tags                   JSONB,
    status                 VARCHAR(50),
    created_at             TIMESTAMP WITH TIME ZONE,
    updated_at             TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    
    
    
    
    UNIQUE (account_id, resource_id)
);

-- [27]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_account_id     ON ai_inventory(account_id);

-- [28]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_resource_type  ON ai_inventory(resource_type);

-- [29]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_resource_id    ON ai_inventory(resource_id);

-- [30]
ALTER TABLE ai_inventory ADD COLUMN IF NOT EXISTS status VARCHAR(50);

-- [31]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_status         ON ai_inventory(status);

-- [32]
DELETE FROM log_messages
WHERE id NOT IN (
    SELECT MIN(id) FROM log_messages GROUP BY log_id, message_type
);

-- [33]
ALTER TABLE inventory_applications
    ADD CONSTRAINT inventory_applications_unique
    UNIQUE (account_id, instance_id, name, version);

-- [34]
ALTER TABLE service_resources
    ADD CONSTRAINT service_resources_unique
    UNIQUE (account_id, service_name, resource_id);

-- [35]
ALTER TABLE products
    ADD CONSTRAINT products_name_unique
    UNIQUE (name);

-- [36]
ALTER TABLE non_compliant_resources
    ADD CONSTRAINT non_compliant_resources_unique
    UNIQUE (config_report_id, resource_id, rule_name);

-- [37]
ALTER TABLE service_costs
    ADD CONSTRAINT service_costs_unique
    UNIQUE (cost_report_id, service_name, region);

-- [38]
ALTER TABLE cost_forecasts
    ADD CONSTRAINT cost_forecasts_unique
    UNIQUE (cost_report_id, period_start, region);

-- [39]
ALTER TABLE guard_duty_findings
    ADD CONSTRAINT guard_duty_findings_unique
    UNIQUE (account_id, detector_id);

-- [40]
ALTER TABLE kms_keys
    ADD CONSTRAINT kms_keys_key_id_unique
    UNIQUE (key_id);

-- [41]
ALTER TABLE waf_rules
    ADD CONSTRAINT waf_rules_waf_id_unique
    UNIQUE (waf_id);

-- [42]
ALTER TABLE inventory_patches
    ADD CONSTRAINT inventory_patches_unique
    UNIQUE (instance_id, title);

-- [43]
ALTER TABLE compute_optimizer
    ADD CONSTRAINT compute_optimizer_resource_arn_unique
    UNIQUE (resource_arn);

-- [44]
ALTER TABLE log_messages
    ADD CONSTRAINT log_messages_unique
    UNIQUE (log_id, message_type);

-- [45]
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

-- [46]
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

-- [47]
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

-- [48]
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

-- [49]
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

-- [50]
DROP VIEW IF EXISTS view_ai_inventory;

-- [51]
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
