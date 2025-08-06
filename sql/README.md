# Database Optimization for Agency360

This directory contains SQL scripts for optimizing the Agency360 database.

## Fixing Upsert Performance Issues

The receiver function was experiencing slow performance and errors with the message:
```
ERROR: there is no unique or exclusion constraint matching the ON CONFLICT specification
```

This occurs because PostgreSQL's native upsert functionality (`INSERT ... ON CONFLICT ... DO UPDATE`) requires unique constraints on the columns specified in the `ON CONFLICT` clause.

## Solution

1. **Add Missing Unique Constraints**

   Run the `add-unique-constraints.sql` script to add the necessary unique constraints:

   ```bash
   psql -h your-aurora-endpoint -U postgres -d core -f sql/add-unique-constraints.sql
   ```

2. **Code Improvements**

   The receiver.py script has been updated to:
   - Check for unique constraints before using native upsert
   - Fall back to SELECT + INSERT/UPDATE pattern when constraints don't exist
   - Use batch processing for better performance
   - Handle errors gracefully to prevent cascading failures

## Verifying Constraints

You can verify that constraints were added successfully with:

```sql
SELECT tc.table_name, tc.constraint_name, tc.constraint_type, 
       string_agg(ccu.column_name, ', ') as columns
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage ccu 
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
  AND tc.table_name IN (
    'config_reports', 'services', 'cost_reports', 'security',
    'cloudtrail_logs', 'secrets_manager_secrets', 'inspector_findings',
    'inventory_instances', 'health_events', 'logs'
  )
GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type
ORDER BY tc.table_name;
```

## Performance Monitoring

After applying these changes, monitor the performance of the receiver function:

1. Check CloudWatch logs for error messages
2. Monitor Aurora PostgreSQL performance metrics
3. Track Lambda execution times

If performance issues persist, consider:
- Increasing Lambda memory/timeout
- Scaling Aurora capacity
- Implementing additional database optimizations