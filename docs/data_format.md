# View360 Analytics Data Format Documentation

This document describes the JSON data format used for transferring data from sender accounts to the analytics account in the View360 Analytics platform.

## Overview

The data is structured as a JSON object with top-level keys representing different data categories. Each sender account generates this JSON file daily or on-demand and uploads it to the analytics account S3 bucket.

## Top-Level Structure

```json
{
  "account": {},
  "config": {},
  "service": [],
  "cost": {},
  "security": {},
  "inventory": {},
  "ai_inventory": [],
  "marketplace": [],
  "trusted_advisor": [],
  "health": [],
  "application": [],
  "resilience_hub": [],
  "service_resources": [],
  "compute_optimizer": [],
  "ri_sp_savings": [],
  "config_inventory": [],
  "support_tickets": {},
  "logs": {}
}
```

**Changes in v2.9.3:**
- `ai_inventory` (new top-level array): Self-hosted AI/ML resource inventory from Security Hub V2's `GetResourcesV2`
- `security.exposures` (new array), `security.threats` (new array), `security.standards` (new array): Security Hub V2 (OCSF) exposure findings with contributor/trait chain, threat detections, and dated security-standard scores
- `security.inspector[]` items gain CVSS/EPSS fields (`cve_id`, `cvss_score`, `cvss_severity`, `cvss_version`, `cvss_vector`, `epss_score`, `cve_count`) — moved off the legacy ASFF Security Hub path onto native inspector2 where the scoring is richer

---

## Field Descriptions

### 1. Account Section

Contains AWS account metadata and contact information.

**Fields:**
- `account_id` (string): AWS account identifier (12-digit number)
- `account_name` (string): Human-readable name for the account
- `account_email` (string): Email address associated with the root user
- `account_status` (string): Account status (e.g., "ACTIVE")
- `account_arn` (string): ARN of the account
- `partner_name` (string): Partner organization name
- `customer_name` (string): Customer organization name
- `category` (string): Account category classification
- `account_type` (string): Environment type (e.g., "PRODUCTION", "DEVELOPMENT", "STAGING")
- `joined_method` (string): How the account joined the organization
- `joined_timestamp` (datetime): When the account was created
- `region` (string): Primary AWS region for the account
- `product` (string): Product or service associated with the account

**Contact Information:**
- `contact_info` (object): Primary contact details
  - `address_line1` (string): First line of address
  - `address_line2` (string): Second line of address
  - `address_line3` (string): Third line of address
  - `city` (string): City name
  - `country_code` (string): Two-letter country code
  - `postal_code` (string): Postal/ZIP code
  - `state_or_region` (string): State or region
  - `company_name` (string): Company name
  - `phone_number` (string): Contact phone number
  - `website_url` (string): Company website URL
  - `full_name` (string): Full account name

**Alternate Contacts:**
- `alternate_contacts` (object): Alternative contacts for different purposes
  - `billing` (object): Billing contact information
    - `name` (string): Contact name
    - `title` (string): Job title
    - `email` (string): Email address
    - `phone` (string): Phone number
  - `operations` (object): Operations contact information (same structure as billing)
  - `security` (object): Security contact information (same structure as billing)

**Example:**
```json
{
  "account_id": "123456789101",
  "account_name": "appc",
  "region": "ap-southeast-1",
  "account_type": "PRODUCTION",
  "partner_name": "AWS",
  "customer_name": "Amazon",
  "contact_info": {
    "city": "Seattle",
    "country_code": "US",
    "postal_code": "98108"
  }
}
```

---

### 2. Config Section

AWS Config compliance data and non-compliant resources.

**Fields:**
- `date_from` (date): Start date of the reporting period
- `date_to` (date): End date of the reporting period
- `compliance_score` (float): Overall compliance score (0-100)
- `total_rules` (integer): Total number of Config rules evaluated
- `compliant_rules` (integer): Number of compliant rules
- `non_compliant_rules` (integer): Number of non-compliant rules
- `non_compliant_resources` (array): List of non-compliant resources
  - `rule_name` (string): Name of the violated Config rule
  - `resource_id` (string): Resource identifier
  - `resource_type` (string): AWS resource type
  - `config_rule_invoked_time` (datetime): When the rule was evaluated
  - `conformance_pack` (string): Associated conformance pack name
  - `compliance_type` (string): Compliance status
  - `annotation` (string): Additional context about the finding
  - `evaluation_mode` (string): How the rule was evaluated

**Example:**
```json
{
  "date_from": "2026-01-07",
  "date_to": "2026-01-08",
  "compliance_score": 42.34,
  "total_rules": 111,
  "compliant_rules": 47,
  "non_compliant_rules": 64,
  "non_compliant_resources": []
}
```

---

### 3. Service Section

AWS service usage and costs aggregated by service.

**Array of Objects with Fields:**
- `service` (string): Name of the AWS service
- `usage_types` (string): Usage type identifier (typically "Aggregated")
- `date_from` (date): Start date of the reporting period
- `date_to` (date): End date of the reporting period
- `cost` (float): Cost for this service during the period
- `currency` (string): Currency code (e.g., "USD")
- `utilization` (float): Utilization metric value (optional)
- `utilization_unit` (string): Unit of measurement for utilization (optional)

**Example:**
```json
[
  {
    "service": "Amazon Relational Database Service",
    "usage_types": "Aggregated",
    "date_from": "2026-01-07",
    "date_to": "2026-01-08",
    "cost": 69.9057927817,
    "currency": "USD",
    "utilization": null,
    "utilization_unit": null
  }
]
```

---

### 4. Cost Section

Comprehensive cost analysis including current, previous, and forecast data.

**Fields:**
- `account_id` (string): AWS account identifier
- `current_period_cost` (float): Total cost for the current reporting period
- `previous_period_cost` (float): Total cost for the previous comparable period
- `cost_difference` (float): Absolute difference between current and previous period
- `cost_difference_percentage` (float): Percentage change in cost
- `top_services` (array): Top 5 services by cost
  - `service` (string): Service name
  - `cost` (float): Service cost
- `period` (object): Reporting period details
  - `start` (date): Period start date
  - `end` (date): Period end date
  - `granularity` (string): Time granularity (DAILY, WEEKLY, MONTHLY)
- `forecast` (array): Cost predictions for future periods
  - `period` (object): Forecast period
    - `start` (date): Forecast start date
    - `end` (date): Forecast end date
  - `amount` (float): Predicted cost amount

**Example:**
```json
{
  "account_id": "123456789101",
  "current_period_cost": 421.52,
  "previous_period_cost": 478.63,
  "cost_difference": -57.12,
  "cost_difference_percentage": -11.93,
  "top_services": [
    {
      "service": "Amazon RDS",
      "cost": 69.91
    }
  ],
  "forecast": [
    {
      "period": {"start": "2026-01-01", "end": "2026-02-01"},
      "amount": 14476.25
    }
  ]
}
```

---

### 5. Security Section

Comprehensive security findings from multiple AWS security services.

**Sub-sections:**

#### 5.1 Security Hub
- `security_hub` (array): Security Hub findings grouped by service
  - `service` (string): Service name
  - `total_findings` (integer): Total number of findings
  - `severity_counts` (object): Count by severity
    - `CRITICAL` (integer)
    - `HIGH` (integer)
    - `MEDIUM` (integer)
    - `LOW` (integer)
    - `INFORMATIONAL` (integer)
  - `open_findings` (integer): Number of unresolved findings
  - `resolved_findings` (integer): Number of resolved findings
  - `findings` (array): Detailed findings
    - `finding_id` (string): Unique finding identifier
    - `service` (string): AWS service related to the finding
    - `title` (string): Brief description
    - `description` (string): Detailed description
    - `severity` (string): Severity level
    - `status` (string): Current status (NEW, NOTIFIED, SUPPRESSED, RESOLVED)
    - `workflow_state` (string): Workflow status
    - `resource_type` (string): Type of affected resource
    - `resource_id` (string): Identifier of affected resource
    - `created_at` (datetime): When finding was first detected
    - `updated_at` (datetime): When finding was last updated
    - `recommendation` (string): Remediation recommendation
    - `compliance_status` (string): Compliance status
    - `region` (string): AWS region

#### 5.2 GuardDuty
- `guard_duty` (array): GuardDuty threat findings
  - `id` (string): Finding identifier
  - `type` (string): Type of GuardDuty finding
  - `severity` (float): Numeric severity score (0-10)
  - `title` (string): Brief description
  - `description` (string): Detailed description
  - `confidence` (float): Confidence score (0-10)
  - `region` (string): AWS region
  - `created_at` (datetime): Creation timestamp
  - `updated_at` (datetime): Last update timestamp

#### 5.3 KMS Keys
- `kms` (array): KMS key information
  - `key_id` (string): KMS key identifier
  - `arn` (string): ARN of the KMS key
  - `description` (string): Key description
  - `key_usage` (string): Purpose of the key
  - `key_state` (string): Current state
  - `creation_date` (datetime): Creation timestamp
  - `enabled` (boolean): Whether the key is enabled
  - `key_rotation_enabled` (boolean): Whether automatic key rotation is enabled

#### 5.4 WAF
- `waf` (array): WAF web ACLs
  - `name` (string): Name of the web ACL
  - `id` (string): WAF identifier
  - `arn` (string): ARN of the web ACL
  - `scope` (string): Scope (REGIONAL or CLOUDFRONT)
  - `description` (string): Web ACL description
  - `default_action` (object): Default action for non-matching requests
  - `rules_count` (integer): Number of rules in the web ACL
  - `capacity` (integer): WCU capacity used
  - `managed_rules_count` (integer): Number of managed rules
  - `custom_rules_count` (integer): Number of custom rules
  - `rate_limit_rules_count` (integer): Number of rate limiting rules
  - `associated_resources` (array): Associated resource ARNs
  - `logging_enabled` (boolean): Whether logging is enabled
  - `geo_blocking_enabled` (boolean): Whether geographic blocking is enabled
  - `blocked_countries` (array): List of blocked country codes

#### 5.5 WAF Rules
- `waf_rules` (array): Detailed WAF rule information
  - `web_acl_name` (string): Associated web ACL name
  - `rule_name` (string): Rule name
  - `priority` (integer): Rule priority
  - `action` (object): Rule action
  - `statement_type` (string): Type of rule statement
  - `is_managed_rule` (boolean): Whether it's a managed rule
  - `is_custom_rule` (boolean): Whether it's a custom rule
  - `rate_limit` (boolean): Whether it's a rate limiting rule
  - `logging_enabled` (boolean): Whether logging is enabled
  - `geo_blocking` (boolean): Whether geo-blocking is used
  - `sql_injection` (boolean): Whether SQL injection protection is enabled
  - `has_xss_protection` (boolean): Whether XSS protection is enabled
  - `is_compliant` (boolean): Whether the rule meets compliance requirements
  - `scope` (string): REGIONAL or CLOUDFRONT

#### 5.6 CloudTrail
- `cloudtrail` (array): CloudTrail trails
  - `name` (string): Trail name
  - `arn` (string): ARN of the trail
  - `is_logging` (boolean): Whether logging is active
  - `is_multi_region` (boolean): Whether the trail applies to all regions
  - `s3_bucket` (string): S3 bucket for log storage
  - `kms_key_id` (string): KMS key for log encryption
  - `log_file_validation` (boolean): Whether log file validation is enabled
  - `latest_delivery_time` (datetime): Timestamp of latest log delivery

#### 5.7 Secrets Manager
- `secrets_manager` (array): Secrets Manager secrets
  - `name` (string): Secret name
  - `arn` (string): ARN of the secret
  - `description` (string): Secret description
  - `created_date` (datetime): Creation timestamp
  - `last_changed_date` (datetime): Last modification timestamp
  - `last_accessed_date` (datetime): Last access timestamp
  - `rotation_enabled` (boolean): Whether automatic rotation is enabled
  - `kms_key_id` (string): KMS key for encryption

#### 5.8 Certificate Manager
- `certificate_manager` (array): ACM certificates
  - `arn` (string): ARN of the certificate
  - `domain_name` (string): Domain name on the certificate
  - `status` (string): Current status
  - `type` (string): Certificate type
  - `not_after` (datetime): Expiration timestamp

#### 5.9 Inspector
- `inspector` (array): Inspector findings
  - `finding_arn` (string): ARN of the Inspector finding
  - `severity` (string): Severity level
  - `status` (string): Current status
  - `type` (string): Type of finding
  - `title` (string): Brief description
  - `description` (string): Detailed description
  - `first_observed_at` (datetime): When first detected
  - `last_observed_at` (datetime): When last observed
  - `updated_at` (datetime): Last update timestamp
  - `cve_id` (string): CVE identifier (e.g., "CVE-2026-6893"). Empty for non-CVE findings.
  - `cvss_score` (float, nullable): Environment-adjusted CVSS score (0.0–10.0). Sourced from `inspectorScore` when available, else falls back to the highest `baseScore` from `packageVulnerabilityDetails.cvss[]`. NULL when neither is present (typically Amazon Linux `ALAS*` advisories).
  - `cvss_severity` (string): Qualitative severity band derived from `cvss_score` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `NONE`).
  - `cvss_version` (string): CVSS spec version (`3.1`, `4.0`, etc.)
  - `cvss_vector` (string): Full vector string from the chosen `cvss[]` entry.
  - `epss_score` (float, nullable): EPSS probability (0.0–1.0) from `epss.score`. NULL when absent.
  - `cve_count` (integer): 1 for the finding's CVE, plus every entry in `relatedVulnerabilities[]` (vendor advisories for the same CVE, e.g. ALAS ids counted alongside).

**CVSS provenance:** Scoring lives here, not on the legacy ASFF Security Hub path. Reason: Security Hub aggregates Inspector, so the only ASFF findings carrying a `Vulnerabilities` array are Inspector's own — putting scores in both places double-counted the same vulnerability across two tables. `_extract_cvss_inspector` in `sender.py` reads the native inspector2 shape (`packageVulnerabilityDetails.cvss[]`, `packageVulnerabilityDetails.vulnerabilityId`, `epss.score`, `inspectorScore`) rather than the ASFF shape.

Validated over 600 live findings: `cvss_severity` matched the AWS severity band 596/600, with the 4 non-matches being correct behavior (2 `UNTRIAGED` findings that have no CVSS band, and 2 Amazon Linux advisories where AWS supplies no scoring at all).

#### 5.10 Exposures (Security Hub V2 / OCSF) — NEW in v2.9.3

Correlated multi-signal findings from Security Hub's V2 (OCSF) surface. Each exposure is a chain: an exposure has one or more contributors, each contributor has one or more traits explaining why it contributes.

- `exposures` (array): Active exposure findings, one entry per exposure
  - `finding_id` (string): Internal correlation hash (`metadata.uid`). Unique per exposure.
  - `finding_arn` (string): Console-visible ARN (`finding_info.uid`)
  - `service` (string): Affected resource type (e.g. `AWS::IAM::User`, `AWS::DynamoDB::Table`)
  - `title` (string): Brief description
  - `description` (string): Detailed narrative of the exposure
  - `severity` (string): `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL` (upper-cased from OCSF's title-case)
  - `status` (string): `NEW`, `NOTIFIED`, `RESOLVED`, `SUPPRESSED`
  - `resource_type` (string): Same as `service` — kept for consistency with legacy findings
  - `resource_id` (string): Affected resource identifier
  - `created_at` (datetime): First seen
  - `updated_at` (datetime): Last updated
  - `recommendation` (string): Remediation guidance
  - `compliance_status` (string): Compliance field from OCSF (empty for pure exposures)
  - `region` (string): AWS region (`global` for IAM-scoped exposures)
  - `workflow_state` (string): Same lifecycle as `status`
  - `record_state` (string): Title-cased status (`New`/`Resolved`), preserves the OCSF surface value
  - `product_name` (string): Typically `Security Hub Exposure Detection`
  - `company_name` (string): `AWS`
  - `product_arn` (string): Producer product ARN
  - `generator_id` (string): Generating rule/detector
  - `generator` (string): Same as `product_name`
  - `cve_id`, `cvss_score`, `cvss_severity`, `cvss_version`, `cvss_vector`, `epss_score`, `cve_count`: Same 7 fields as Inspector. Populated only for vulnerability-flavored exposures. NULL/empty on pure IAM/misconfiguration exposures.
  - `contributed_finding` (array): The evidence chain (see 5.11)

Sender-side collection ([`sender.py`](../scripts/sender.py) `get_security_hub_v2`) filters via `class_name=Detection Finding` + `finding_info.types PREFIX Exposure`, and scopes to `status IN ('New', 'Notified')` — the API-level filter for active exposures. No date filter, because V2 exposures are long-lived correlated findings representing current state, not point-in-time events.

**Resolve-close semantics:** an exposure in the DB but absent from the current payload is marked `status='RESOLVED'` by the receiver rather than deleted. Row is preserved as history. If the exposure reappears in a later payload, its `status` returns to `NEW`.

**Example:**
```json
{
  "finding_id": "e17e79fa975e02b4221e2c66dca99215ba211b96292acb1e0955fea61a0761b7",
  "finding_arn": "arn:aws:securityhub:us-east-1:12345678910:exposure:d68a0b03...",
  "service": "AWS::IAM::User",
  "title": "Potential Unauthorized Access: IAM user has weak password policies...",
  "severity": "MEDIUM",
  "status": "NEW",
  "resource_type": "AWS::IAM::User",
  "resource_id": "AIDA3QLF7DEAMGDWGU7RY",
  "created_at": "2026-06-19T04:25:56.743Z",
  "updated_at": "2026-08-06T02:50:38.786Z",
  "region": "global",
  "workflow_state": "NEW",
  "record_state": "New",
  "cve_id": "", "cvss_score": null,
  "contributed_finding": [ /* see 5.11 */ ]
}
```

#### 5.11 Contributed Findings (nested under each exposure) — NEW in v2.9.3

Each entry represents one piece of evidence contributing to an exposure. Contributors can be actual Security Hub findings (e.g. a failed IAM.7 control) OR resource-configuration observations (a bare IAM user with `is_finding=false`).

- `contributed_finding[]` (nested array under each exposure)
  - `finding_id` (string): The contributor's own uid. Same `finding_id` can appear under **multiple exposures** in the same account — see cross-exposure protection below.
  - `finding_arn` (string): Contributor's ARN if resolvable, otherwise empty
  - `source` (string): Product name (`Security Hub`, `Inspector`, empty for resource observations)
  - `title` (string): Contributor's title
  - `is_finding` (boolean): True if the contributor is a real finding (has an ARN, can be looked up), false if it's a resource-configuration observation
  - `resource_uid` (string): The resource identifier this contributor points at
  - `status` (string): `NEW` when the contributor is present in this payload. Sender stamps this at emission time so a reappearing contributor is re-opened correctly by the receiver's upsert.
  - `workflow_state` (string): Same as `status`
  - `cve_id`, `cvss_score`, `cvss_severity`, `cvss_version`, `cvss_vector`, `epss_score`, `cve_count`: Populated when the contributor is a resolvable Inspector finding. Empty/NULL for non-vulnerability contributors.
  - `trait_count` (integer): Number of traits carried on this contributor
  - `trait_categories` (string): Comma-separated categories of the **contributing** traits only (e.g. `"Impact, Vulnerability"`)
  - `trait_names` (string): Pipe-separated names of every trait (contributing + contextual)
  - `traits` (array): The individual trait records (see 5.12)

**Cross-exposure protection:** The receiver's resolve-close for contributors uses a `NOT EXISTS` check — a contributor's `finding_id` is only marked `RESOLVED` if it isn't still tied to any other active exposure in the same account. Example: an IAM user contributing to three separate exposures for weak password policy stays active until all three exposures resolve.

#### 5.12 Traits (nested under each contributor) — NEW in v2.9.3

Traits explain *why* an exposure exists. Each trait names a specific weakness of the resource the contributor identifies.

- `traits[]` (nested array under each contributed_finding)
  - `category` (string): Trait taxonomy — `Vulnerability`, `Misconfiguration`, `Impact`, `Assumability`, or empty
  - `name` (string): Full trait text (e.g. `"The IAM user has an inject code privileged executor access path"`)
  - `type` (string): `Contributing Trait` (part of the causal chain) or `Contextual Trait` (describes the surrounding resource)

**Example — one exposure with three contributors and their traits:**
```json
"contributed_finding": [
  {
    "finding_id": "AIDA3QLF7DEAMGDWGU7RY",
    "source": "",
    "title": "AWS::IAM::User BLANK",
    "is_finding": false,
    "status": "NEW",
    "workflow_state": "NEW",
    "trait_count": 5,
    "trait_categories": "Impact",
    "trait_names": "The IAM user has an inject code... | ... | The IAM user has a service admin policy",
    "traits": [
      {"category": "Impact",           "name": "The IAM user has an inject code privileged executor access path", "type": "Contributing Trait"},
      {"category": "Misconfiguration", "name": "The IAM user has an administrative access policy",                "type": "Contextual Trait"}
    ]
  },
  {
    "finding_id": "f3b802923567047ec2bb2cba69d67aac76d85a61835bcf4b506187ee461267a9",
    "source": "Security Hub",
    "title": "Password policies for IAM users should have strong configurations",
    "is_finding": true,
    "status": "NEW",
    "cvss_score": null,
    "trait_count": 1,
    "traits": [{"category": "Misconfiguration", "name": "The AWS Account of the IAM user has weak password policies", "type": "Contributing Trait"}]
  }
]
```

#### 5.13 Threats (Security Hub V2 / OCSF) — NEW in v2.9.3

GuardDuty-sourced (and other) threat detections from the V2 surface. Flat table, no contributor chain in the current sender output.

- `threats` (array)
  - `finding_id`, `finding_arn`, `service`, `title`, `description`, `severity`, `status`, `resource_type`, `resource_id`, `created_at`, `updated_at`, `recommendation`, `region`, `workflow_state`, `record_state`, `product_name`, `company_name`, `product_arn`, `generator_id`, `generator`: Same as exposures (see 5.10)
  - `finding_type` (string): OCSF finding_info.types entry, minus the `Threats` marker (e.g. `Discovery:IAMUser/AnomalousBehavior`)
  - `analytic_type` (string): Detection method — typically `Behavioral` for GuardDuty
  - `actor_name` (string): Principal name that triggered the detection
  - `actor_uid` (string): Principal UID (falls back to `uid` if `uid_alt` is absent)
  - `api_operation` (string): API call that triggered the detection (e.g. `ListServiceSpecificCredentials`)
  - `api_service` (string): AWS service the API belongs to (e.g. `iam.amazonaws.com`)
  - `source_ip` (string): Source IP of the caller
  - `source_country` (string): Country name resolved from the source IP
  - `count` (integer): Occurrence count. Written to `threat_findings.occurrence_count` in the DB (renamed to avoid collision with the SQL `COUNT()` aggregate function).

**Sender filter:** `class_name=Detection Finding` + `finding_info.types PREFIX_NOT_EQUALS Exposure` — i.e. Detection Findings that aren't exposures. Same `status IN ('New', 'Notified')` filter and same resolve-close semantics as exposures.

**Threats deliberately carry NO CVSS fields** — GuardDuty findings score threats via GuardDuty's own severity scale (0-10 numeric), not CVSS. The `severity` string field captures this.

#### 5.14 Security Standards (Security Hub V2) — NEW in v2.9.3

Daily snapshot of Security Hub standard compliance scores. Feeds the security posture trend chart.

- `standards` (array)
  - `standard_name` (string): Short-form name (e.g. `cis-aws-foundations-benchmark/v/1.2.0`)
  - `standard_arn` (string): Full ARN
  - `subscription_arn` (string): This account's subscription ARN
  - `status` (string): Subscription state (`READY`, `PENDING`, etc.)
  - `passed` (integer): Number of controls in `PASSED` state
  - `failed` (integer): Number of controls in `FAILED` state
  - `score` (integer): Percentage — `round(passed / (passed + failed) * 100)`
  - `date_from` (date, `YYYY-MM-DD`): Collection window start — stamped by the sender at emission time
  - `date_to` (date, `YYYY-MM-DD`): Collection window end — same as above

**Key design point:** the DB's UNIQUE key on `security_standards` is `(account_id, standard_arn, date_from)`. Every daily run writes a **new row** per standard, not an in-place update. `score` over `date_from` is the trend axis. Without `date_from` in the key, yesterday's row would be overwritten every day and no trending would be possible.

**Example:**
```json
[
  {
    "standard_name": "cis-aws-foundations-benchmark/v/1.2.0",
    "standard_arn": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0",
    "subscription_arn": "arn:aws:securityhub:us-east-1:12345678910:subscription/cis-aws-foundations-benchmark/v/1.2.0",
    "status": "READY",
    "passed": 39,
    "failed": 34,
    "score": 53,
    "date_from": "2026-08-05",
    "date_to": "2026-08-06"
  }
]
```

---

### 6. Inventory Section

EC2 instance inventory from Systems Manager with SSM agent compliance.

**Sub-sections:**

#### 6.1 Instances
- `instances` (array): EC2 instance details
  - `instance_id` (string): EC2 instance identifier
  - `platform` (string): Operating system platform
  - `platform_type` (string): Platform type (Linux/Windows)
  - `platform_version` (string): OS version
  - `agent_version` (string): Version of the SSM agent
  - `is_latest_version` (boolean): Whether agent is latest version
  - `last_ping` (datetime): Timestamp of last successful connection
  - `computer_name` (string): Hostname of the instance
  - `instance_type` (string): Resource type
  - `ip_address` (string): IP address of the instance
  - `ping_status` (string): Connectivity status
  - `association_status` (string): SSM association status
  - `association_execution_date` (datetime): Last association execution
  - `association_success_date` (datetime): Last successful association

#### 6.2 Patches
- `patches` (array): System patches
  - `instance_id` (string): EC2 instance identifier
  - `title` (string): Patch title/description
  - `classification` (string): Type of patch (Security, etc.)
  - `severity` (string): Severity level
  - `state` (string): Installation status
  - `installed_time` (datetime): When the patch was installed

---

### 6b. AI Inventory Section — NEW in v2.9.3

Self-hosted AI/ML resource inventory from Security Hub V2's `GetResourcesV2` API. Distinct from Section 6 (Inventory), which covers EC2/SSM inventory. This is a top-level array (not nested under `security`) because it describes resources, not findings.

**Array of Objects with Fields:**
- `resource_guid` (string): Security Hub's stable GUID for the resource
- `resource_id` (string): Short-form resource ID (e.g. `gateway-quick-start-f3d764-axpqf6sqss`). For child resources (like `GatewayTarget`) this is a composite `<parent>|<child>`.
- `resource_name` (string): Human-readable name
- `resource_type` (string): Security Hub's OCSF-style type (e.g. `AWS::SageMaker::Endpoint`, `AWS::Bedrock::Agent`)
- `resource_category` (string): Always `AI/ML` (filter used at query time)
- `resource_sub_category` (string): Finer classification (e.g. `Model`, `Agent`, `AgentFramework`, `AgentToolsAndIdentity`, `ExternalEndpoint`, `Development`, `ModelServing`)
- `discovery_type` (string): How Security Hub discovered the resource
- `region` (string): AWS region
- `account_id` (string): 12-digit AWS account ID
- `created_at` (datetime): `ResourceCreationTimeDt`
- `tags` (array): Resource tags as returned by Security Hub
- `host_resource_guid` (string): GUID of the hosting resource (for AI resources running on top of another resource)
- `host_resource_type` (string): Type of the hosting resource
- `canonical_id` (string): Provider-canonical identifier
- `model_count` (integer): `SelfHostedAIModelResourceCount`
- `agent_count` (integer): `SelfHostedAIAgentResourceCount`
- `total_ai_count` (integer): `SelfHostedTotalAIResourceCount`
- `finding` (array of contributor refs): Populated by `_link_findings_to_root` in the sender — each entry is a reference to a Security Hub V2 finding that concerns this resource, keyed on `resource_id` (with a fallback to the parent id for composite child resources). Same shape as `contributed_finding[]` in Section 5.11 minus the traits.

**Example:**
```json
[
  {
    "resource_guid": "6c4b7c26-...",
    "resource_id": "gateway-quick-start-f3d764-axpqf6sqss",
    "resource_name": "gateway-quick-start-f3d764-axpqf6sqss",
    "resource_type": "AWS::Bedrock::Agent",
    "resource_category": "AI/ML",
    "resource_sub_category": "Agent",
    "region": "us-east-1",
    "account_id": "12345678910",
    "created_at": "2026-07-11T09:22:41Z",
    "host_resource_type": "AWS::EC2::Instance",
    "model_count": 0,
    "agent_count": 1,
    "total_ai_count": 1,
    "finding": []
  }
]
```

---

### 7. Marketplace Section

AWS Marketplace product usage and costs.

**Array of Objects with Fields:**
- `product_code` (string): Marketplace product identifier
- `product_name` (string): Name of the product
- `dimension` (string): Usage dimension
- `customer_identifier` (string): Customer identifier
- `value` (string): Usage value
- `expiration_date` (datetime): Subscription expiration date
- `cost_consumed` (float): Cost for the reporting period
- `currency` (string): Currency code
- `period_start` (date): Start date of the reporting period
- `period_end` (date): End date of the reporting period
- `daily_costs` (array): Daily cost breakdown
  - `date` (date): Date
  - `cost` (float): Cost for that date
- `status` (string): Current status of the subscription

---

### 8. Trusted Advisor Section

Trusted Advisor check results and recommendations.

**Array of Objects with Fields:**
- `check_name` (string): Name of the Trusted Advisor check
- `category` (string): Category of the check
- `severity` (string): Severity level (warning, error)
- `recommendation` (string): Recommended action
- `affected_resources_count` (integer): Number of affected resources
- `potential_savings` (float): Potential cost savings
- `timestamp` (datetime): Timestamp of the check

---

### 9. Health Section

AWS Health events and service notifications.

**Array of Objects with Fields:**
- `arn` (string): ARN of the health event
- `service` (string): Affected AWS service
- `event_type_code` (string): Type of health event
- `event_type_category` (string): Event category
- `region` (string): Affected AWS region
- `availability_zone` (string): Affected availability zone
- `start_time` (datetime): Start time of the event
- `end_time` (datetime): End time of the event (null if ongoing)
- `last_updated_time` (datetime): Last update timestamp
- `status_code` (string): Current status of the event
- `event_scope_code` (string): Scope of the event

---

### 10. Application Section

Application monitoring signals from CloudWatch Application Signals.

**Array of Objects with Fields:**
- `service_name` (string): Name of the monitored service
- `namespace` (string): CloudWatch namespace
- `key_attributes` (object): Identifying attributes
- `attribute_map` (object): Additional attributes
- `metric_references` (array): Referenced metrics

---

### 11. Resilience Hub Section

Resilience Hub application assessments.

**Array of Objects with Fields:**
- `app_arn` (string): ARN of the Resilience Hub application
- `name` (string): Application name
- `description` (string): Application description
- `compliance_status` (string): Compliance status
- `resiliency_score` (float): Resilience score (0-100)
- `status` (string): Current status
- `cost` (float): Cost of resilience measures
- `creation_time` (datetime): Creation timestamp
- `last_assessment_time` (datetime): Timestamp of last resilience assessment
- `rpo` (integer): Recovery Point Objective (seconds)
- `rto` (integer): Recovery Time Objective (seconds)
- `last_drill` (datetime): Timestamp of last disaster recovery drill

---

### 12. Service Resources Section

Inventory of AWS resources across multiple services.

**Array of Objects with Fields:**
- `service_name` (string): AWS service name (EC2, RDS, EBS, S3, ELB, AutoScaling, VPC)
- `resource_type` (string): Type of AWS resource
- `resource_id` (string): Resource identifier
- `resource_name` (string): Resource name
- `region` (string): AWS region
- `availability_zone` (string): Availability Zone
- `state` (string): Current state
- `instance_type` (string): EC2 instance type (for EC2)
- `vpc_id` (string): VPC identifier (for VPC resources)
- `engine` (string): Database engine (for RDS)
- `instance_class` (string): Instance class (for RDS)
- `multi_az` (boolean): Multi-AZ deployment (for RDS)
- `size_gb` (integer): Size in GB (for EBS)
- `volume_type` (string): Volume type (for EBS)
- `creation_date` (datetime): Creation timestamp (for S3)
- `type` (string): Load balancer type (for ELB)
- `scheme` (string): Load balancer scheme (for ELB)
- `instance_count` (integer): Number of instances (for AutoScaling)
- `min_size` (integer): Minimum size (for AutoScaling)
- `max_size` (integer): Maximum size (for AutoScaling)
- `available_ip_count` (integer): Available IP addresses (for VPC subnets)

---

### 13. Compute Optimizer Section

Compute Optimizer recommendations for cost optimization.

**Array of Objects with Fields:**
- `account_id` (string): AWS account identifier
- `resource_type` (string): Type of resource (EC2, EBS, Lambda)
- `resource_arn` (string): ARN of the resource
- `resource_name` (string): Resource name
- `finding` (string): Optimization finding
- `current_instance_type` (string): Current instance type (for EC2)
- `current_memory_size` (integer): Current memory size (for Lambda)
- `current_volume_type` (string): Current volume type (for EBS)
- `current_volume_size` (integer): Current volume size (for EBS)
- `recommended_instance_type` (string): Recommended instance type
- `recommended_memory_size` (integer): Recommended memory size
- `recommended_volume_type` (string): Recommended volume type
- `recommended_volume_size` (integer): Recommended volume size
- `savings_opportunity_percentage` (float): Potential savings percentage
- `estimated_monthly_savings_usd` (float): Estimated monthly savings
- `performance_risk` (float): Performance risk score
- `cpu_utilization_max` (float): Maximum CPU utilization
- `memory_utilization_avg` (float): Average memory utilization
- `migration_effort` (string): Effort required for migration

---

### 14. Config Inventory Section

Resource inventory from AWS Config (currently placeholder).

**Array of Objects with Fields:**
- `resource_type` (string): Type of resource
- `resource_subtype` (string): Resource subtype
- `resource_id` (string): Resource identifier
- `resource_name` (string): Resource name
- `region` (string): AWS region
- `availability_zone` (string): Availability Zone
- `state` (string): Current state
- Additional fields matching service_resources structure

---

### 15. Support Tickets Section

AWS Support case tracking.

**Fields:**
- `date_from` (date): Start date of the reporting period
- `date_to` (date): End date of the reporting period
- `total_tickets` (integer): Total number of tickets
- `tickets` (array): List of support tickets
  - `case_id` (string): Internal case identifier
  - `display_id` (string): Display case identifier
  - `subject` (string): Ticket subject
  - `status` (string): Current status
  - `severity_code` (string): Severity level
  - `service_code` (string): Related AWS service
  - `category_code` (string): Ticket category
  - `time_created` (datetime): Creation timestamp
  - `submitted_by` (string): Submitter email
  - `language` (string): Language code (default: "en")

**Example:**
```json
{
  "date_from": "2026-01-07",
  "date_to": "2026-01-08",
  "total_tickets": 0,
  "tickets": []
}
```

---

### 16. Logs Section

Data processing status and error tracking.

**Fields:**
- `account_status` (string): Account data collection status
- `config_status` (string): Config data collection status
- `service_status` (string): Service data collection status
- `cost_status` (string): Cost data collection status
- `security_status` (string): Security data collection status
- `inventory_status` (string): Inventory data collection status
- `marketplace_status` (string): Marketplace data collection status
- `trusted_advisor_status` (string): Trusted Advisor data collection status
- `health_status` (string): Health data collection status
- `application_status` (string): Application data collection status
- `resilience_hub_status` (string): Resilience Hub data collection status
- `compute_optimizer_status` (string): Compute Optimizer data collection status
- `service_resources_status` (string): Service resources data collection status
- `config_inventory_status` (string): Config inventory data collection status
- `support_tickets_status` (string): Support tickets data collection status
- `message` (array): List of error messages or warnings

**Status Values:**
- `Pass`: Data collected successfully
- `Fail`: Data collection failed

---

## Data Collection Frequency

- **Daily**: Default collection frequency
- **Weekly**: Aggregated weekly data
- **Monthly**: Aggregated monthly data
- **Yearly**: Aggregated yearly data
- **On-Demand**: Triggered manually or via EventBridge

## File Naming Convention

Files are uploaded to S3 with the following naming pattern:

```
s3://{bucket}/data/{account_id}/{region}/{YYYY-MM-DD}_{interval}.json
```

Example:
```
s3://analytics-bucket/data/123456789101/ap-southeast-1/2026-01-08_DAILY.json
```

## Data Retention

- Raw JSON files are moved to `loaded/` folder after successful processing
- Database retains historical data based on configured retention policies
- S3 lifecycle policies can be configured for long-term archival

## Security Considerations

- All data is encrypted at rest using KMS
- Data in transit is encrypted using HTTPS
- IAM roles enforce least privilege access
- Cross-account access is restricted to specific sender accounts
- Sensitive data (PII) should be masked or excluded

## Version History

- **v2.9.3** (August 2026): Security Hub V2 (OCSF) exposures/threats/contributor/trait chain, security standards daily snapshots for score trending, AI/ML resource inventory from `GetResourcesV2`, CVSS/EPSS scoring moved from ASFF Security Hub path onto native `inspector2` findings, per-contributor `status`/`workflow_state` fields, resolve-close lifecycle for exposures and threats with cross-exposure `NOT EXISTS` protection for shared contributors, receiver `INSERT ... ON CONFLICT ... RETURNING xmax = 0` rewrite (733s → 21s runtime, ~35× faster).
- **v2.x** (January 2026): Added multi-region support, support tickets, enhanced compliance tracking
- **v1.x** (Pre-January 2026): Initial version with basic observability features
