-- =============================================================================
-- Rollback for v2.9.21 -> v2.9.3
-- =============================================================================
-- Exact inverse of 01-schema.sql and 02-views.sql, in reverse dependency
-- order:
--
--   1. Drop views first (they reference the tables below)
--   2. Drop the 12 UNIQUE constraints added in part 3
--   3. Drop the 5 new tables in reverse FK order:
--      exposure_finding_trait -> exposure_contributed_finding -> exposure_findings,
--      then threat_findings and security_standards independently
--
-- CASCADE is deliberately NOT used anywhere here. Every object this migration
-- created is named explicitly below, so if something outside this list has
-- grown a dependency on one of these tables, the DROP fails loudly with a
-- named error instead of silently taking that unknown object down with it
--
-- Indexes are not dropped individually - they go with the table or the
-- constraint they sit on
--
-- The log_messages DELETE in 01-schema.sql [26] is NOT reversible from this
-- file. Those 11 rows were exact-duplicate content on (log_id, message_type,
-- message) removed to allow the UNIQUE constraint to apply; restoring them
-- would require a database backup taken before the migration ran
--
-- Data loss if run: rows in the 5 new tables get dropped with them. All 5
-- tables are rebuilt from the next sender payload on the receiver's next run,
-- so this is only a problem if the sender has stopped emitting
--
-- Run one statement at a time, or use
--
--     python3 migrations/apply-sql.py migrations/01-v2.9.21-to-v2.9.3-migration/APPLY-ORDERED-ROLLBACK.sql
-- =============================================================================


-- =============================================================================
-- PART 1 of 3 - Drop the 6 new views
-- =============================================================================

-- [1]
DROP VIEW IF EXISTS view_ai_inventory;

-- [2]
DROP VIEW IF EXISTS view_security_standards;

-- [3]
DROP VIEW IF EXISTS view_threat_findings;

-- [4]
DROP VIEW IF EXISTS view_exposure_finding_trait;

-- [5]
DROP VIEW IF EXISTS view_exposure_contributed_finding;

-- [6]
DROP VIEW IF EXISTS view_exposure_findings;


-- =============================================================================
-- PART 2 of 3 - Drop UNIQUE constraints on existing tables (12 total)
-- =============================================================================
-- Constraint names are the ones assigned explicitly in 01-schema.sql, so no
-- guessing at auto-generated names. IF EXISTS keeps the drop idempotent on
-- re-runs

-- [7]
ALTER TABLE inventory_applications DROP CONSTRAINT IF EXISTS inventory_applications_unique;

-- [8]
ALTER TABLE service_resources DROP CONSTRAINT IF EXISTS service_resources_unique;

-- [9]
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_name_unique;

-- [10]
ALTER TABLE non_compliant_resources DROP CONSTRAINT IF EXISTS non_compliant_resources_unique;

-- [11]
ALTER TABLE service_costs DROP CONSTRAINT IF EXISTS service_costs_unique;

-- [12]
ALTER TABLE cost_forecasts DROP CONSTRAINT IF EXISTS cost_forecasts_unique;

-- [13]
ALTER TABLE guard_duty_findings DROP CONSTRAINT IF EXISTS guard_duty_findings_unique;

-- [14]
ALTER TABLE kms_keys DROP CONSTRAINT IF EXISTS kms_keys_key_id_unique;

-- [15]
ALTER TABLE waf_rules DROP CONSTRAINT IF EXISTS waf_rules_waf_id_unique;

-- [16]
ALTER TABLE inventory_patches DROP CONSTRAINT IF EXISTS inventory_patches_unique;

-- [17]
ALTER TABLE compute_optimizer DROP CONSTRAINT IF EXISTS compute_optimizer_resource_arn_unique;

-- [18]
ALTER TABLE log_messages DROP CONSTRAINT IF EXISTS log_messages_unique;


-- =============================================================================
-- PART 3 of 3 - Drop the 6 new tables in reverse FK order
-- =============================================================================

-- [19]
DROP TABLE IF EXISTS exposure_finding_trait;

-- [20]
DROP TABLE IF EXISTS exposure_contributed_finding;

-- [21]
DROP TABLE IF EXISTS exposure_findings;

-- [22]
DROP TABLE IF EXISTS threat_findings;

-- [23]
DROP TABLE IF EXISTS security_standards;

-- [24]
DROP TABLE IF EXISTS ai_inventory;
