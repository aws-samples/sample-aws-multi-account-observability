# Migration Script: Upgrade v2.9.3 → v2.9.4

This release lets you answer "which CVEs are in my accounts, and where?" from the analytics database and from AWS Quick chat.

- Run these scripts on a test environment first.
- No existing data is destroyed. Existing `inspector_findings` rows keep their values; the new columns fill in on the next daily run.
- The RDS Data API accepts **one statement per call**. Run the statements in [APPLY-ORDERED.sql](APPLY-ORDERED.sql) one at a time in the Aurora query editor.
- Every statement is safe to re-run (`IF NOT EXISTS` / `DROP VIEW IF EXISTS`).
- Rollback: [APPLY-ORDERED-ROLLBACK.sql](APPLY-ORDERED-ROLLBACK.sql).

---

## 1. What Changed

| Area | Change |
|---|---|
| **Sender** | `get_inspector()` pages through `inspector2:ListFindings` to the end. It sends every `ACTIVE` finding on every run, whatever its age, plus findings that became `CLOSED` or `SUPPRESSED` inside the collection window. Before, it read only the first page and only findings touched inside the window, so most open CVEs never reached the database. Each finding now carries its affected resource (type, ID, readable name, Region), package (name, installed version, fixed-in version, package manager), fix and exploit availability, remediation and advisory URL. |
| **Receiver** | Stores the CVE and CVSS/EPSS fields the v2.9.3 sender already sent but the receiver dropped, plus the new resource and package fields. Loads Inspector rows in batches of 200 per Data API call. |
| **Schema** | 21 new columns on `inspector_findings`, 4 new indexes. |
| **Views** | `view_inspector_findings` recreated with the new columns. New `view_inspector_cves`: one row per CVE per account and Region, `ACTIVE` findings only, with worst severity, highest CVSS/EPSS, affected resource count and names, packages, and fix availability. |
| **IAM** | None. The sender role already has `inspector2:ListFindings`. |

---

## 2. Migrate the Database

Run each statement in [APPLY-ORDERED.sql](APPLY-ORDERED.sql) in order:

| Step | Statement |
|---|---|
| 1 | `ALTER TABLE inspector_findings ADD COLUMN IF NOT EXISTS ...` |
| 2-5 | `CREATE INDEX IF NOT EXISTS idx_inspector_findings_*` |
| 6 | `DROP VIEW IF EXISTS view_inspector_findings` (its `if.*` now expands to new columns in the middle of the list, which `CREATE OR REPLACE VIEW` refuses) |
| 7 | `CREATE VIEW view_inspector_findings ...` |
| 8 | `CREATE OR REPLACE VIEW view_inspector_cves ...` |

---

## 3. Update Lambda Scripts

1. Replace `sender.py` in every sender account and Region.
2. Replace `receiver.py` in the analytics account.

Deploy the receiver before or together with the senders. An old receiver ignores the new fields, so nothing breaks in between.

A sender with many findings now sends a larger payload (about 2 KB per finding, so about 5 MB for 2,500 findings) and makes one `ListFindings` call per 100 findings. Check that the sender Lambda's timeout and memory are adequate for your largest account.

---

## 4. Refresh Quick Datasets

The dashboard template does not use Inspector data. If you built your own dataset on `view_inspector_findings`, refresh it so the new columns appear.

---

## 5. Ask About CVEs in Quick Chat

To let people ask questions such as "which critical CVEs have a fix?" in Quick chat:

1. **Create datasets** from `view_inspector_cves` (one row per CVE) and `view_inspector_findings` (one row per CVE per resource), using the same Aurora data source and VPC connection as the other datasets. Set them to refresh daily, after the receiver run. See [Creating a dataset from a database](https://docs.aws.amazon.com/quick/latest/userguide/create-a-database-data-set.html).
2. **Enrich each dataset** with column descriptions and synonyms, for example "vulnerability" for `cve_id`, "server" or "image" for `resource_name`, and "exploit likelihood" for `epss_score`. See [Data Preparation Experience (New)](https://docs.aws.amazon.com/quick/latest/userguide/data-prep-experience-new.html).
3. **Create a topic** with both datasets and a relationship on `account_id` and `cve_id`, so chat can go from a CVE to the resources that carry it. See [Working with AWS Quick Sight Topics](https://docs.aws.amazon.com/quick/latest/userguide/topics.html) and [Using Topics in AWS Quick chat](https://docs.aws.amazon.com/quick/latest/userguide/topics-in-chat.html).
4. **Add the topic to a space** and share the space with your security team. Users then add the space to a chat conversation, or attach it to a chat agent. See [Spaces in AWS Quick](https://docs.aws.amazon.com/quick/latest/userguide/working-with-spaces.html).

Example questions:

- How many critical and high CVEs do we have in each account?
- Which CVEs with a known fix affect the most resources?
- List the CVEs on the instance named `web-server-01`, with the fixed version for each package.
- Which container images have critical CVEs, and which packages cause them?
- Which CVEs have an EPSS score above 0.1?

Access follows the dataset and topic permissions. Share the datasets only with people who may see vulnerability data for those accounts.

---

## 6. Post-Migration Validation

After the next daily run:

```sql
-- CVE fields are populated (expect most ACTIVE package findings to have a cve_id)
SELECT status, type, COUNT(*) AS findings, COUNT(cve_id) FILTER (WHERE cve_id <> '') AS with_cve
FROM inspector_findings GROUP BY status, type ORDER BY status, type;

-- Top CVEs to fix first
SELECT account_full, cve_id, severity, cvss_score, epss_score, affected_resources, resource_names
FROM view_inspector_cves
WHERE severity IN ('CRITICAL', 'HIGH') AND fix_available
ORDER BY epss_score DESC NULLS LAST LIMIT 20;
```

To cross-check a sender account, compare the `ACTIVE` count with Inspector:

```bash
aws inspector2 list-findings --region <region> \
  --filter-criteria '{"findingStatus":[{"comparison":"EQUALS","value":"ACTIVE"}]}' \
  --query 'length(findings)'
```

The CLI pages automatically, so the number is the full count.

---

## Rollback Plan

1. Redeploy the v2.9.3 `receiver.py` and `sender.py`.
2. Run [APPLY-ORDERED-ROLLBACK.sql](APPLY-ORDERED-ROLLBACK.sql) one statement at a time.

The rollback drops the new columns and their data. Re-applying the migration and the v2.9.4 scripts restores them on the next daily run.
