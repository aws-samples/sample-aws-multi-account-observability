-- Createing Views
--1. View Accounts merged with Services
CREATE OR REPLACE VIEW view_acct_serv AS
SELECT
    s.id,
    s.account_id,
    a.account_id as account,
    a.account_name as account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    s.service,
    s.date_from,
    s.date_to,
    s.cost,
    s.currency,
    s.utilization,
    s.utilization_unit,
    s.usage_types,  -- converted array to JSON string
    s.created_at,
    s.updated_at
FROM accounts as a
INNER JOIN services as s ON s.account_id = a.id;

--2. View Accounts merged with Costs
CREATE OR REPLACE VIEW view_acct_cost_rep AS
SELECT
    cr.id,
    cr.account_id,
    a.account_id as account,
    a.account_name as account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    concat(initcap(cr.period_granularity::text), ' Cost Report - ',
              to_char(cr.period_end::timestamp with time zone, 'DD Mon YYYY'::text)) AS cost_report_name,

    ROUND(cr.current_period_cost, 4) as current_period_cost,
    ROUND(cr.previous_period_cost, 4) as previous_period_cost,
    ROUND(cr.cost_difference, 4) as cost_difference,
    ROUND(cr.cost_difference_percentage, 2) as cost_difference_percentage,
    ROUND(cr.potential_monthly_savings, 4) as potential_monthly_savings,
    cr.anomalies_detected,
    cr.saving_opportunities_count,
    cr.period_start as date_from,
    cr.period_end as date_to,
    cr.period_granularity,
    cr.created_at,
    -- Optional: Add period duration
    (cr.period_end - cr.period_start) as period_duration_days
FROM accounts as a
INNER JOIN cost_reports as cr ON cr.account_id = a.id;

--3. View Accounts merged with Cost Reports, Service Costs
CREATE OR REPLACE VIEW view_acct_serv_cost AS
SELECT sc.id,
    a.id as account_id,
    a.account_id as account,
    a.account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    sc.service_name,
    round(sc.cost, 2) as cost,
    
    concat(initcap(cr.period_granularity::text), ' Cost Report - ',
            to_char(cr.period_end::timestamp with time zone, 'DD Mon YYYY'::text)) AS cost_report_name,
    cr.period_start as date_from,
    cr.period_end as date_to,
    cr.period_granularity,
    cr.cost_difference_percentage,
    sc.created_at
FROM accounts a
    JOIN cost_reports cr ON cr.account_id = a.id
    JOIN service_costs sc ON sc.cost_report_id = cr.id;

--4. View Accoutns, COst Report and Cost forecast
CREATE OR REPLACE VIEW view_acct_cost_rep_forecast AS
SELECT cr.id,
    cr.account_id,
    a.account_id  AS account,
    a.account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    concat(initcap(cr.period_granularity::text), ' Cost Report - ',
            to_char(cr.period_end::timestamp with time zone, 'DD Mon YYYY'::text)) as cost_report_name,
    round(cr.current_period_cost, 4) as current_period_cost,
    round(cr.previous_period_cost, 4) as previous_period_cost,
    round(cr.cost_difference, 4) as cost_difference,
    round(cr.cost_difference_percentage, 2) as cost_difference_percentage,
    round(cr.potential_monthly_savings, 4) as potential_monthly_savings,
    cr.anomalies_detected,
    cr.saving_opportunities_count,
    cr.period_start as date_from,
    cr.period_end as date_to,
    cr.period_granularity,
    
    round(cf.amount, 4) as forecast_amount,
    round(cf.prediction_interval_lower_bound, 4) as forecast_lower_bound,
    round(cf.prediction_interval_upper_bound, 4) as forecast_upper_bound,
    cf.period_start as forecast_period_start,
    cf.period_end as forecast_period_end,
    round((cf.amount - cr.current_period_cost) / cr.current_period_cost * 100::numeric,2) as forecast_change_percentage,
    round(cf.prediction_interval_upper_bound - cf.prediction_interval_lower_bound, 4) as forecast_range,
    round(cf.amount - cr.current_period_cost, 4) as forecast_absolute_change,
    round((cf.prediction_interval_upper_bound - cf.prediction_interval_lower_bound) / NULLIF(cf.amount, 0::numeric) * 100::numeric, 2) as forecast_confidence_range_percentage,
    CASE
        WHEN cf.amount > cr.current_period_cost THEN 'Increase'::text
        WHEN cf.amount < cr.current_period_cost THEN 'Decrease'::text
        ELSE 'No Change'::text
        END AS forecast_trend,
    cr.created_at,
    cr.period_end - cr.period_start as period_duration_days
FROM accounts a
         JOIN cost_reports cr ON cr.account_id = a.id
         LEFT JOIN cost_forecasts cf ON cf.cost_report_id = cr.id;


-- 5. View Accounts & Security
CREATE OR REPLACE VIEW view_acct_security AS
SELECT
    s.id,
    s.account_id,
    -- Account information
    a.account_id as account,
    a.account_name as account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    -- Security information
    s.service,
    s.total_findings,
    s.critical_count,
    s.high_count,
    s.medium_count,
    s.low_count,
    s.informational_count,
    s.open_findings,
    s.resolved_findings,

    -- Calculated fields
    ROUND((s.resolved_findings::DECIMAL / NULLIF(s.total_findings, 0)), 4) as resolution_rate,
    ROUND((s.open_findings::DECIMAL / NULLIF(s.total_findings, 0)), 4) as open_rate,

    -- Severity distribution
    ROUND((s.critical_count::DECIMAL / NULLIF(s.total_findings, 0)), 4) as critical_percentage,
    ROUND((s.high_count::DECIMAL / NULLIF(s.total_findings, 0)), 4) as high_percentage,
    ROUND((s.medium_count::DECIMAL / NULLIF(s.total_findings, 0)), 4) as medium_percentage,
    ROUND((s.low_count::DECIMAL / NULLIF(s.total_findings, 0)), 4) as low_percentage,
    ROUND((s.informational_count::DECIMAL / NULLIF(s.total_findings, 0)), 4) as informational_percentage,

    -- Risk indicator with count
    CASE
        WHEN s.critical_count > 0 THEN CONCAT('Critical (', s.critical_count, ')')
        WHEN s.high_count > 0 THEN CONCAT('High (', s.high_count, ')')
        WHEN s.medium_count > 0 THEN CONCAT('Medium (', s.medium_count, ')')
        WHEN s.low_count > 0 THEN CONCAT('Low (', s.low_count, ')')
        ELSE CONCAT('Informational (', s.informational_count, ')')
    END as highest_severity,

    -- Additional metrics
    CASE
        WHEN s.total_findings = 0 THEN 'No Findings'
        WHEN s.open_findings = 0 THEN 'All Resolved'
        WHEN s.resolved_findings = 0 THEN 'None Resolved'
        ELSE 'Partially Resolved'
    END as resolution_status,

    -- Risk Level
    CASE
        WHEN s.critical_count > 0 THEN 1
        WHEN s.high_count > 0 THEN 2
        WHEN s.medium_count > 0 THEN 3
        WHEN s.low_count > 0 THEN 4
        ELSE 5
    END as risk_level,

    -- Timestamps
    s.created_at,
    s.updated_at,

    -- Age of security assessment
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, s.created_at)) as days_since_assessment

FROM accounts as a
INNER JOIN security as s ON s.account_id = a.id
ORDER BY
    CASE
        WHEN s.critical_count > 0 THEN 1
        WHEN s.high_count > 0 THEN 2
        WHEN s.medium_count > 0 THEN 3
        WHEN s.low_count > 0 THEN 4
        ELSE 5
    END,
    s.total_findings DESC;


-- 6. View Account and Security Findings Summary

CREATE OR REPLACE VIEW view_acct_security_findings_summary AS
SELECT
    a.id as account_id,
    a.account_id as account,
    a.account_name as account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    f.severity,
    -- Status Counts
    COUNT(*) as total_findings,
    COUNT(CASE WHEN f.status = 'NEW' THEN 1 END) as new_count,
    COUNT(CASE WHEN f.status = 'NOTIFIED' THEN 1 END) as notified_count,
    COUNT(CASE WHEN f.status = 'SUPPRESSED' THEN 1 END) as suppressed_count,
    COUNT(CASE WHEN f.status = 'RESOLVED' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN f.status = 'REMOVED' THEN 1 END) as removed_count,
    -- Workflow Status Counts
    COUNT(CASE WHEN f.workflow_state = 'IN_PROGRESS' THEN 1 END) as in_progress_count,
    COUNT(CASE WHEN f.workflow_state = 'ARCHIVED' THEN 1 END) as archived_count,
    COUNT(CASE WHEN f.workflow_state = 'CLOSED' THEN 1 END) as closed_count,
    -- Active Issues (excluding resolved, removed, archived, closed)
    COUNT(CASE
        WHEN f.status NOT IN ('RESOLVED', 'REMOVED')
        AND (f.workflow_state NOT IN ('ARCHIVED', 'CLOSED') OR f.workflow_state IS NULL)
        THEN 1
    END) as active_issues,
    f.service as finding_service,
    f.region
FROM accounts a
INNER JOIN security s ON s.account_id = a.id
INNER JOIN findings f ON f.security_id = s.id
GROUP BY
    a.id,
    a.account_id,
    a.account_name,
    f.severity,
    f.service,
    f.region;

-- 7. View Account and Security Findings Details
CREATE OR REPLACE VIEW view_acct_security_findings_details AS
SELECT

    -- Account Context
    a.id as account_id,
    a.account_id as account,
    a.account_name as account_name,

    -- Finding Core Information
    f.id,
    f.finding_id as finding_reference,
    f.title,
    f.severity,
    f.status,
    f.workflow_state,


    -- Status Classification
    CASE
        WHEN f.status = 'NEW' THEN 'Needs Review'
        WHEN f.status = 'NOTIFIED' THEN 'Awaiting Response'
        WHEN f.status = 'SUPPRESSED' THEN 'Muted'
        WHEN f.status = 'RESOLVED' THEN 'Fixed'
        WHEN f.status = 'REMOVED' THEN 'Not Applicable'
        ELSE f.status
    END as status_description,

    -- Workflow Classification
    CASE
        WHEN f.workflow_state = 'IN_PROGRESS' THEN 'Under Investigation'
        WHEN f.workflow_state = 'ARCHIVED' THEN 'Historical Record'
        WHEN f.workflow_state = 'CLOSED' THEN 'Investigation Complete'
        ELSE 'Pending'
    END as workflow_description,

    -- Age Calculations
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, f.created_at)) as total_days,
    CASE
        WHEN f.status IN ('RESOLVED', 'REMOVED') OR f.workflow_state IN ('ARCHIVED', 'CLOSED')
        THEN EXTRACT(DAY FROM AGE(f.updated_at, f.created_at))
        ELSE EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, f.created_at))
    END as days_open,

    -- Resource Information
    f.service as finding_service,
    f.resource_type,
    f.resource_id,
    f.region,

    -- Additional Context
    f.compliance_status,
    f.product_name,

    -- Priority Indicator
    CASE
        WHEN f.status = 'NEW' AND f.severity = 'CRITICAL' THEN 'Immediate Action Required'
        WHEN f.status = 'NEW' AND f.severity = 'HIGH' THEN 'Urgent Review Needed'
        WHEN f.status IN ('RESOLVED', 'REMOVED') THEN 'Completed'
        WHEN f.workflow_state = 'IN_PROGRESS' THEN 'Under Review'
        WHEN f.status = 'SUPPRESSED' THEN 'Accepted Risk'
        ELSE 'Normal Priority'
    END as priority_indicator,

    -- Timestamps
    f.created_at,
    f.updated_at
FROM accounts a
INNER JOIN security s ON s.account_id = a.id
INNER JOIN findings f ON f.security_id = s.id
ORDER BY
    CASE
        WHEN f.severity = 'CRITICAL' THEN 1
        WHEN f.severity = 'HIGH' THEN 2
        WHEN f.severity = 'MEDIUM' THEN 3
        WHEN f.severity = 'LOW' THEN 4
        ELSE 5
    END,
    CASE
        WHEN f.status = 'NEW' THEN 1
        WHEN f.status = 'NOTIFIED' THEN 2
        WHEN f.workflow_state = 'IN_PROGRESS' THEN 3
        WHEN f.status = 'SUPPRESSED' THEN 4
        WHEN f.status IN ('RESOLVED', 'REMOVED') THEN 5
        ELSE 6
    END,
    days_open DESC;

-- 8. View Account and Security Findings Trends

CREATE OR REPLACE VIEW view_acct_security_findings_trends AS
SELECT
    a.id as account_id,
    a.account_id as account,
    a.account_name as account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    DATE_TRUNC('day', f.created_at) as date,
    f.severity,
    f.status,
    f.workflow_state,
    COUNT(*) as finding_count,

    -- Status-based metrics
    COUNT(CASE WHEN f.status = 'NEW' THEN 1 END) as new_findings,
    COUNT(CASE WHEN f.status IN ('RESOLVED', 'REMOVED') THEN 1 END) as resolved_findings,
    COUNT(CASE WHEN f.workflow_state = 'IN_PROGRESS' THEN 1 END) as in_progress_findings,

    -- Average resolution time
    AVG(CASE
        WHEN f.status IN ('RESOLVED', 'REMOVED')
        THEN EXTRACT(DAY FROM AGE(f.updated_at, f.created_at))
    END) as avg_resolution_days,

    f.service as finding_service,
    f.region
FROM accounts a
INNER JOIN security s ON s.account_id = a.id
INNER JOIN findings f ON f.security_id = s.id
GROUP BY
    a.id,
    a.account_id,
    a.account_name,
    DATE_TRUNC('day', f.created_at),
    f.severity,
    f.status,
    f.workflow_state,
    f.service,
    f.region
ORDER BY
    date DESC;

-- 9. View Account and Aggregated products
CREATE OR REPLACE VIEW view_acct_products AS
SELECT a.id as account_id,
    a.account_id as account,
    a.account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    a.account_email,
    a.account_status,
    a.joined_method,
    a.joined_timestamp,
    count(DISTINCT p.id) as associated_products_count,
    string_agg(DISTINCT p.name::text, ', '::text ORDER BY (p.name::text)) as associated_products,
    string_agg(DISTINCT p.owner::text, ', '::text ORDER BY (p.owner::text)) as product_owners,
    CASE
        WHEN count(p.id) = 0 THEN 'Unassigned'::text
        WHEN count(p.id) = 1 THEN 'Single Product'::text
        ELSE 'Multiple Products'::text
        END AS assignment_status,
    max(pa.updated_at) as latest_product_association,
    EXTRACT(day FROM age(CURRENT_TIMESTAMP, a.joined_timestamp))  as account_age_days,
    a.created_at as account_created_at,
    a.updated_at as account_updated_at
FROM accounts a
         LEFT JOIN product_accounts pa ON a.id = pa.account_id
         LEFT JOIN products p ON pa.product_id = p.id
GROUP BY a.id, a.account_id, a.account_name, a.account_email, a.account_status, a.joined_method, a.joined_timestamp,
         a.created_at, a.updated_at
ORDER BY a.account_name;


-- 10. View Product and its accounts
CREATE OR REPLACE VIEW view_product_acct AS
WITH account_product_counts AS (SELECT a_1.id                 AS account_id,
                                       count(pa_1.product_id) AS product_count
                                FROM accounts a_1
                                         LEFT JOIN product_accounts pa_1 ON a_1.id = pa_1.account_id
                                GROUP BY a_1.id)
SELECT a.id as account_id,
    a.account_id as account,
    a.account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
    a.account_email,
    a.account_status,
    a.joined_method,
    a.joined_timestamp,
    p.id as product_id,
    p.name as product_name,
    p.owner as product_owner,
    p."position" as product_position,
    p.description as product_description,
    CASE
        WHEN p.id IS NULL THEN 'Unassigned'::text
        ELSE 'Assigned'::text
        END AS assignment_status,
    apc.product_count,
    CASE
        WHEN apc.product_count = 0 THEN 'No Products'::text
        WHEN apc.product_count = 1 THEN 'Single Product'::text
        ELSE 'Multiple Products'::text
        END AS product_assignment_type,
    COALESCE(pa.created_at, a.created_at) AS relationship_created_at,
    COALESCE(pa.updated_at, a.updated_at) AS relationship_updated_at,
    EXTRACT(day FROM age(CURRENT_TIMESTAMP, a.joined_timestamp)) AS account_age_days
FROM accounts a
    LEFT JOIN product_accounts pa ON a.id = pa.account_id
    LEFT JOIN products p ON pa.product_id = p.id
    LEFT JOIN account_product_counts apc ON a.id = apc.account_id
ORDER BY a.account_name, p.name;

-- 11. View Account and Logs data to check the loading of data
CREATE OR REPLACE VIEW view_acct_logs AS
WITH latest_logs AS (
    -- Get the most recent log entry for each account
    SELECT DISTINCT ON (account_id)
        l.account_id,
        l.id as log_id,
        l.date_created,
        l.account_status,
        l.cost_status,
        l.service_status,
        l.security_status,
        l.created_at,
        l.updated_at
    FROM logs l
    ORDER BY l.account_id, l.date_created DESC
),
log_message_summary AS (
    -- Aggregate messages for each log
    SELECT
        lm.log_id,
        STRING_AGG(lm.message, ' | ' ORDER BY lm.created_at) as all_messages,
        COUNT(lm.id) as message_count,
        STRING_AGG(DISTINCT lm.message_type, ', ') as message_types
    FROM log_messages lm
    GROUP BY lm.log_id
)
SELECT
    -- Account Information
    a.id as account_id,
    a.account_id as account,
    a.account_name,
    l.cost_status,
    l.service_status,
    l.security_status,

    -- Status Summary
    CASE
        WHEN l.account_status = 'ERROR' OR
             l.cost_status = 'ERROR' OR
             l.service_status = 'ERROR' OR
             l.security_status = 'ERROR' THEN 'Error'
        WHEN l.account_status = 'WARNING' OR
             l.cost_status = 'WARNING' OR
             l.service_status = 'WARNING' OR
             l.security_status = 'WARNING' THEN 'Warning'
        ELSE 'OK'
    END as overall_status,

    -- Log Messages
    lm.all_messages as log_messages,
    lm.message_count,
    lm.message_types,

    -- Timing Information
    l.date_created as log_date,
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, l.date_created)) as days_since_last_log,

    -- Status Changes
    CASE
        WHEN a.account_status != l.account_status THEN 'Changed'
        ELSE 'Unchanged'
    END as status_change_indicator,

    -- Health Score (example calculation)
    CASE
        WHEN l.account_status = 'ERROR' THEN 0
        WHEN l.account_status = 'WARNING' THEN 50
        ELSE 100
    END +
    CASE
        WHEN l.cost_status = 'ERROR' THEN 0
        WHEN l.cost_status = 'WARNING' THEN 50
        ELSE 100
    END +
    CASE
        WHEN l.service_status = 'ERROR' THEN 0
        WHEN l.service_status = 'WARNING' THEN 50
        ELSE 100
    END +
    CASE
        WHEN l.security_status = 'ERROR' THEN 0
        WHEN l.security_status = 'WARNING' THEN 50
        ELSE 100
    END as health_score,

    -- Timestamps
    a.created_at as account_created_at,
    l.created_at as log_created_at,
    l.updated_at as log_updated_at

FROM accounts a
LEFT JOIN latest_logs l ON a.id = l.account_id
LEFT JOIN log_message_summary lm ON l.log_id = lm.log_id
ORDER BY
    CASE
        WHEN l.account_status = 'ERROR' OR
             l.cost_status = 'ERROR' OR
             l.service_status = 'ERROR' OR
             l.security_status = 'ERROR' THEN 1
        WHEN l.account_status = 'WARNING' OR
             l.cost_status = 'WARNING' OR
             l.service_status = 'WARNING' OR
             l.security_status = 'WARNING' THEN 2
        ELSE 3
    END,
    l.date_created DESC;

-- 12. View Account and Log Messages data to check the loading of data
CREATE OR REPLACE VIEW view_acct_log_messages AS
SELECT
    -- Account Information
    a.id as account_id,
    a.account_id as account,
    a.account_name,

    -- Log Information
    l.date_created as log_date,

    -- Message Details
    lm.id as message_id,
    lm.message,
    lm.message_type,
    lm.created_at as message_timestamp,

    -- Time Information
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, lm.created_at)) as days_ago

FROM accounts a
INNER JOIN logs l ON a.id = l.account_id
INNER JOIN log_messages lm ON l.id = lm.log_id
ORDER BY
    lm.created_at DESC;


-- 13. View Account, Product, Security, Cost, Services Summary
CREATE OR REPLACE VIEW view_summary AS
WITH latest_cost_report AS (
    -- Get the most recent cost report for each account and granularity
    SELECT *
    FROM cost_reports
    ORDER BY account_id, period_granularity, period_end DESC
),
service_metrics AS (
    -- Aggregate service metrics
    SELECT
        account_id,
        COUNT(DISTINCT id) as service_count,
        COUNT(DISTINCT service) as unique_services,
        SUM(cost) as total_service_cost,
        STRING_AGG(DISTINCT service, ', ') as services_used
    FROM services
    GROUP BY account_id
),
security_metrics AS (
    -- Aggregate security metrics
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
),
log_status AS (
    -- Get latest log status
    SELECT DISTINCT ON (account_id)
        account_id,
        account_status,
        cost_status,
        service_status,
        security_status
    FROM logs
    ORDER BY account_id, date_created DESC
),
product_count AS (
    -- Count number of products per account
    SELECT
        account_id,
        COUNT(DISTINCT product_id) as number_of_products
    FROM product_accounts
    GROUP BY account_id
)
SELECT
    -- Account Identifiers
    a.id as account_id,
    a.account_id as account,
    a.account_name,
    a.csp as account_csp,
    a.account_type as account_type,
    CONCAT(a.account_id, ' - ', a.account_name) as account_full,
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

    -- Status Information
    ls.account_status as latest_account_status,
    ls.cost_status as latest_cost_status,
    ls.service_status as latest_service_status,
    ls.security_status as latest_security_status,

    -- Overall Health Score
    CASE
        WHEN ls.account_status = 'ERROR' OR
             ls.cost_status = 'ERROR' OR
             ls.service_status = 'ERROR' OR
             ls.security_status = 'ERROR' THEN 'Critical'
        WHEN ls.account_status = 'WARNING' OR
             ls.cost_status = 'WARNING' OR
             ls.service_status = 'WARNING' OR
             ls.security_status = 'WARNING' THEN 'Warning'
        ELSE 'Healthy'
    END as overall_health,

    -- Account Information
    a.account_email,
    a.joined_method,
    a.joined_timestamp,
    EXTRACT(DAY FROM AGE(CURRENT_TIMESTAMP, a.joined_timestamp)) as account_age_days

FROM accounts a
LEFT JOIN latest_cost_report cr ON cr.account_id = a.id
LEFT JOIN service_metrics sm ON sm.account_id = a.id
LEFT JOIN security_metrics sec ON sec.account_id = a.id
LEFT JOIN log_status ls ON ls.account_id = a.id
LEFT JOIN product_count pc ON pc.account_id = a.id

WHERE
    (cr.period_granularity::text = 'MONTHLY'::text OR
     cr.period_granularity::text = 'WEEKLY'::text OR
     cr.period_granularity::text = 'DAILY'::text)

ORDER BY
    a.account_name,
    cr.period_start DESC;

-- 14. Product Accounts View Elaborated
    -- Create view for product_accounts with additional fields
CREATE OR REPLACE VIEW view_product_accounts AS
SELECT
    pa.id,
    pa.product_id,
    pa.account_id,
    p.name AS product_name,
    a.account_id AS account_number,
    a.account_name,
    CONCAT(a.account_id, ' - ', a.account_name) AS account_full,
    pa.created_at,
    pa.updated_at
FROM
    product_accounts pa
JOIN
    products p ON pa.product_id = p.id
JOIN
    accounts a ON pa.account_id = a.id
ORDER BY
    p.name, a.account_name;