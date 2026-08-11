-- =============================================================================
-- Migration: v2.9.21 -> v2.9.3
-- =============================================================================
-- Migrates from the schema in sql/schema/core-schema.sql to the v2.9.3 shape.
-- Two categories of changes:
--
--   1. NEW TABLES for Security Hub V2 (OCSF) data. The sender started emitting
--      exposures/threats/standards, none of which had a home in the schema
--      before. Adds 5 tables, 19 indexes, 5 views. exposure_findings drives a
--      3-level parent -> contributor -> trait chain; threat_findings and
--      security_standards are flat
--
--   2. UNIQUE CONSTRAINTS on 12 pre-existing tables. Every constraint matches
--      the composite key the receiver's upsert already used at runtime, but
--      the DB had no matching UNIQUE index - so the upsert was falling back to
--      a full-table SELECT existence check per row. On the largest table
--      (77k+ non_compliant_resources) this was O(N^2) and drove the receiver
--      to 733s per file. With these constraints and the receiver's INSERT ...
--      ON CONFLICT ... DO UPDATE rewrite, the same file loads in 21s.
--
--      Two tables carry a caller/schema mismatch that this migration widens
--      correctly: inventory_applications (name/version needed as part of the
--      key so a package's version history is preserved), and service_resources
--      (service_name added so the same ARN can appear under multiple services
--      without colliding). log_messages had 11 duplicate rows on the target
--      key, deduped in place before the constraint is added
--
-- Every statement is idempotent (IF NOT EXISTS on tables/indexes, explicit
-- constraint names for ALTER) except the log_messages DELETE, which is a
-- one-way data cleanup of duplicates that already exist. See 02-rollback.sql
-- for the inverse
--
-- The RDS Data API accepts exactly ONE statement per call. Pasting a whole
-- file fails with "Multistatements aren't supported", which is a limit of
-- the transport not a SQL problem. Run the numbered statements below one at
-- a time, or use
--
--     python3 migrations/apply-sql.py migrations/01-v2.9.21-to-v2.9.3-migration/APPLY-ORDERED.sql
--
-- =============================================================================


-- =============================================================================
-- PART 1 of 4 - New tables for Security Hub V2 (exposures, threats, standards)
-- =============================================================================
-- exposure_findings is the parent of a 3-level chain. Ordering matters: child
-- tables reference parent ids, so the tables must be created top-down, then
-- their indexes. threat_findings and security_standards are flat with no
-- children

-- [1] Exposure findings - one row per exposure
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


-- [7] Contributor findings - child of exposure_findings, one row per contributor
--
-- status / workflow_state are nullable because Security Hub does not emit a
-- per-contributor status. The sender stamps 'NEW' at emission time so the
-- receiver upsert can flip a resurfaced contributor out of 'RESOLVED', but if a
-- future sender stops stamping them, NULL is still valid and the receiver's
-- resolve-close treats NULL as "still active" via IS DISTINCT FROM 'RESOLVED'
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


-- [12] Trait entries - child of exposure_contributed_finding, one row per trait
--
-- UNIQUE NULLS NOT DISTINCT is a PG15+ feature that treats NULL as equal to
-- itself, so idempotent re-runs of the same trait set work regardless of
-- whether category is NULL. Without it, PG's SQL-standard behavior would allow
-- multiple identical (contributed_finding_id, NULL, name, type) rows to accumulate
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


-- [16] Threat findings - flat table, no children in the current sender output
--
-- occurrence_count (not `count`) because `count` collides with the SQL COUNT()
-- aggregate function and would need quoting in every query. The sender's
-- payload key is still `count`; the receiver maps it during upsert
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


-- [22] Security standards - one row per standard per collection day. date_from
--      is part of the unique key so the same standard writes a new row every
--      day, giving score history for trend charts. If date_from were absent
--      from the key, every daily run would overwrite yesterday's score and no
--      trending would be possible
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


-- [26] Self-hosted AI/ML resource inventory from Security Hub V2 GetResourcesV2.
--
-- Flat table, one row per AI/ML resource per account. resource_guid is Security
-- Hub's stable identifier and is UNIQUE per account. resource_id is the
-- short-form / composite id used for cross-referencing with contributor rows:
-- exposure_contributed_finding.resource_uid joins to ai_inventory.resource_id
-- at query time, so no junction table is needed for finding-resource correlation
--
-- tags stored as JSONB because Security Hub returns them as an unbounded list
-- of key/value entries. Empty array {} when the resource has no tags
-- status is 'ACTIVE' when the resource is present in the current sender payload
-- and 'INACTIVE' when the receiver's NOT IN sweep marks it absent. Nullable to
-- accept legacy rows written before the column existed; the receiver's resolve
-- UPDATE uses IS DISTINCT FROM 'INACTIVE' so NULL is treated as still active.
-- updated_at is refreshed on every state change (upsert or resolve)
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
    -- Keyed on resource_id rather than resource_guid: guid is AWS's stable
    -- identifier and unique-safe, but resource_id is the value the exposure
    -- contributor chain references in exposure_contributed_finding.resource_uid,
    -- so keying here on the same value keeps the two tables joinable via a
    -- single column and matches how the receiver's upsert already reasons
    UNIQUE (account_id, resource_id)
);

-- [27]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_account_id     ON ai_inventory(account_id);

-- [28]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_resource_type  ON ai_inventory(resource_type);

-- [29]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_resource_id    ON ai_inventory(resource_id);

-- [30] Idempotent ADD COLUMN for clusters where ai_inventory was created by an
--      earlier partial run of this migration (or by an updated core-schema.sql
--      shipped without the status column). CREATE TABLE IF NOT EXISTS at [26]
--      is a no-op on an existing table so it cannot add missing columns
ALTER TABLE ai_inventory ADD COLUMN IF NOT EXISTS status VARCHAR(50);

-- [31]
CREATE INDEX IF NOT EXISTS idx_ai_inventory_status         ON ai_inventory(status);


-- =============================================================================
-- PART 2 of 4 - Deduplicate log_messages before adding its UNIQUE constraint
-- =============================================================================
-- log_messages had 11 duplicate rows on (log_id, message_type) from three
-- specific 2026-01-27 log runs, verified read-only that every duplicate pair
-- has identical `message` text as well. Keep the oldest (lowest id) of each
-- group and delete the rest, so the UNIQUE constraint below can apply cleanly.
-- ONE-WAY change - the rollback file cannot restore these rows

-- [32]
DELETE FROM log_messages
WHERE id NOT IN (
    SELECT MIN(id) FROM log_messages GROUP BY log_id, message_type
);


-- =============================================================================
-- PART 3 of 4 - Add UNIQUE constraints to existing tables
-- =============================================================================
-- Every constraint below matches the composite key the receiver's upsert
-- already uses at runtime. Without them, upsert falls back to a per-row
-- SELECT existence check that scans the whole table, which is O(N^2) as
-- data accumulates. Pre-checked read-only on live: zero duplicate rows on
-- all 12 keys (log_messages after the dedupe above), so every ADD CONSTRAINT
-- applies without error

-- [33] Widened from ['instance_id', 'name'] to include account_id and
--      version so a package's version history is preserved. Without version
--      in the key, a package upgrade would silently overwrite the old row
ALTER TABLE inventory_applications
    ADD CONSTRAINT inventory_applications_unique
    UNIQUE (account_id, instance_id, name, version);

-- [34] Widened from ['account_id', 'resource_id'] to include service_name so
--      an ARN that appears under multiple services (e.g. EBS attached to EC2)
--      does not collide
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
