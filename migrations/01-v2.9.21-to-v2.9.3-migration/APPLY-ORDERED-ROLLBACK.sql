-- =============================================================================
-- 01-v2.9.21-to-v2.9.3-migration ROLLBACK, flattened to one statement per entry
-- =============================================================================
-- Generated from sql/03-rollback.sql. Regenerate rather than hand-edit
--
-- Reverses APPLY-ORDERED.sql. The log_messages DELETE is NOT reversible.
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
