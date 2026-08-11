""" ONLY FOR DEVELOPMENT REMOVE ON LAMBDA """
""" from dotenv import load_dotenv, dotenv_values 
load_dotenv() """

""" IMPORTS """
import boto3
import sys
import json
import os
from typing import List, Dict, Any, Optional, Union
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from functools import lru_cache
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading



""" GLOBAL VARIABLES """
SUCCESS     = "🟢"  # Green dot
FAIL        = "🟡"  # yellow dot
ERROR       = "🔴"  # Warning sign
INFO        = "🔵"  # Info Sign
DELETED     = "🗑️"  # Deleted
TIMING      = "⏱️"  # Clock

DB_NAME     = os.environ.get("DB_NAME")
ARN_AURORA  = os.environ.get("AURORA_CLUSTER_ARN")
ARN_SECRET  = os.environ.get("AURORA_SECRET_ARN")
REGION      = os.environ.get("REGION") #boto3.client('sts').meta.region_name
BUCKET      = os.environ.get("BUCKET")

# Turn on for per-loader and per-security-sub-block timing lines. Off in prod because the
# extra print calls and time.time() reads add nothing when nothing is broken - and clutter
# the log. Flip to True (or set DEBUG=true in the env) when a run gets slow and you need to
# know which sub-block owns the tail
DEBUG       = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
KMS_KEY_ID  = os.environ.get("ANALYTICS_KMS_KEY")

AWS_TYPECAST_2  =   {
                        'timestamp'                 :   [
                                                            'created_at',
                                                            'updated_at',
                                                            'joined_timestamp',
                                                            'period_start',
                                                            'period_end',
                                                            'date_from',  
                                                            'date_to',    
                                                            'date_created',
                                                            'last_ping_date_time',
                                                            'install_time',
                                                            'installed_time',
                                                            'timestamp',
                                                            'start_time',
                                                            'end_time',
                                                            'creation_time',
                                                            'last_assessment_time',
                                                            'last_drill',
                                                            'creation_date',
                                                            'latest_delivery_time',
                                                            'created_date',
                                                            'not_after',
                                                            'first_observed_at',
                                                            'last_changed_date',
                                                            'association_execution_date',
                                                            'association_success_date',
                                                            'start_date',
                                                            'end_date',
                                                            'date',
                                                            'time_created',
                                                            'returnable_until'
                                                        ],
                        'period_granularity_type'   :   [
                                                            'period_granularity'
                                                        ],
                        'varchar_array'             :   [
                                                            
                                                        ],
                        'numeric'                   :   [
                                                            'cost',
                                                            'utilization',
                                                            'current_period_cost',
                                                            'previous_period_cost',
                                                            'cost_difference',
                                                            'cost_difference_percentage',
                                                            'potential_monthly_savings',
                                                            'amount',
                                                            'prediction_interval_lower_bound',
                                                            'prediction_interval_upper_bound',
                                                            'utilization_percentage',
                                                            'on_demand_cost',
                                                            'reservation_cost',
                                                            'net_savings',
                                                            'instance_count',
                                                            'min_size',
                                                            'max_size'
                                                        ],
                        'jsonb'                     :   [
                                                            'key_attributes',
                                                            'configuration',
                                                            'tags',
                                                            'default_action'
                                                        ],
                    }

TYPE_CASTING    =   {
                        'timestamp with time zone'  : AWS_TYPECAST_2['timestamp'],
                        'period_granularity_type'   : AWS_TYPECAST_2['period_granularity_type'],
                        'varchar[]'                 : AWS_TYPECAST_2['varchar_array'],
                        'numeric'                   : AWS_TYPECAST_2['numeric']
                    }

###START: HELPER CLASSES###

""" 1. TEST PERMISSIONS FOR AWS SERVICES """
class AWSBoto3Permissions:
    def __init__(self, params=None):
        self.boto3_config           = Config(connect_timeout=5,read_timeout=10,retries={'max_attempts': 2})
        self.boto3_config_optional  = Config(connect_timeout=2,read_timeout=3, retries={'max_attempts': 0})

        # Get current date and 30 days ago for CE
        self.end_date 		= datetime.now()
        self.start_date 	= self.end_date - timedelta(days=30)
        self.aws_services 	= {
                                    'sts'               : {
                                                            'name'      : 'STS',
                                                            'client'    : boto3.client('sts', region_name=REGION, config=self.boto3_config),
                                                            'action'    : 'get_caller_identity',
                                                            'params'    : params,
                                                            'status'    : False,
                                                            "reqd"      : True
                                                            
                                                        },
                                    'account'           : {
                                                            'name'      : 'Account',
                                                            'client'    : boto3.client('account', region_name=REGION, config=self.boto3_config_optional),
                                                            'action'    : 'get_contact_information',
                                                            'params'    : params,
                                                            'status'    : False,
                                                            "reqd"      : False
                                                        },
                                    'rds-data'          : {
                                                            'name'      : 'Aurora RDS',
                                                            'client'    : boto3.client('rds-data', region_name=REGION, config=self.boto3_config),
                                                            'action'    : 'close',
                                                            'params'    : params,
                                                            'status'    : False,
                                                            "reqd"      : True
                                                        },
                                    's3'                : {
                                                            'name'      : 's3',
                                                            'client'    : boto3.client('s3', region_name=REGION, config=self.boto3_config),
                                                            'action'    : 'close',
                                                            'params'    : params,
                                                            'status'    : False,
                                                            "reqd"      : True
                                                        }
                                }

    def _is_optional(self, reqd):
        if not reqd:
            return "Optional"
        else:
            return "Required"

    def _check(self, service):
        is_opt = self._is_optional(service["reqd"])
        try:
            if service["params"]:
                service["client"].__getattribute__(service["action"])(
                    **service["params"]
                )
            else:
                service["client"].__getattribute__(service["action"])()
            service["status"] = True
            print(f"{SUCCESS} Connected to {service['name']} ({is_opt})")
        except ClientError as e:
            print(f"{FAIL} Not Connected to {service['name']} ({is_opt}): {str(e)}")
            service["status"] = False
        except Exception as e:
            print(f"{ERROR} Error testing {service['name']} ({is_opt}): {str(e)}")
            service["status"] = None

    def test(self):
        print("Testing Connectivity to AWS Service Clients")
        print("*" * 43)
        
        print(f"{INFO} Version Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"{INFO} Version Boto3 {boto3.__version__}")

        passed 	= 0
        failed 	= 0
        counter = 0

        for key, val in self.aws_services.items():
            self._check(val)

            if val["status"] == True:
                passed += 1
            elif val["status"] == False:
                if(val['reqd'] == False):
                    passed += 1
                else:
                    failed += 1

            counter += 1

        error = counter - (passed + failed)
        print(
            f"\n\033[92m{passed} Connected\033[0m \n\033[93m{failed} Not Connected\033[0m \n\033[91m{error} Has Errors\033[0m\n"
        )

        if failed > 0:
            return False
        else:
            return True

""" 1a. ENUM for Types of Logs """
class AWSLogType(str, Enum):
    ERROR   = "ERROR"
    INFO    = "INFO"
    WARN    = "WARN"
    SUCCESS = "SUCCESS"

""" 1a. ENUM for AWS Resources """
class AWSResourceType(str, Enum):
    ACCOUNT             = "Account"
    CONFIG              = "Config"
    SERVICE             = "Service"
    COST                = "Cost"
    SECURITY            = "Security"
    INVENTORY           = "Inventory"
    MARKETPLACE         = "Marketplace"
    TRUSTED_ADVISOR     = "Trusted_advisor"
    HEALTH              = "Health"
    APPLICATION         = "Application"
    RESILIENCE_HUB      = "Resilience Hub"
    COMPUTE_OPTIMIZER   = "Compute Optimizer"
    RI_SP_SAVINGS       = "RI/SP Savings"
    SERVICE_RESOURCES   = "Service Resources"
    CONFIG_INVENTORY    = "Config Inventory"
    SUPPORT_TICKETS     = "Support Tickets"
    AI_INVENTORY        = "AI Inventory"
    LOGS                = "Logs"

""" 2. S3 MANAGER : Wrapper class to interact with the S3 Bucket """
class S3Manager:
    __slots__ = ('bucket', 's3')
    
    def __init__(self, bucket_name: str):
        self.bucket = bucket_name
        self.s3 = boto3.client('s3')
    
    def list_files(self, prefix: str = '') -> List[Dict[str, str]]:
        """Lightning-fast file listing"""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [
                {'file_name': obj['Key'].split('/')[-1], 'file_path': obj['Key']}
                for obj in response.get('Contents', [])
            ]
        except Exception:
            return []
    
    def read_file(self, file_path: str) -> str:
        """Optimized file reading"""
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=file_path)['Body'].read().decode('utf-8')
        except Exception:
            return ""
    
    def move_to_processed(self, file_path) -> bool:
        try:
            # Replace 'data' with 'processed' in the path
            temp_path = file_path
            new_path = temp_path.replace('data/', 'loaded/', 1)
            
            # Copy object to new location
            self.s3.copy_object(
                Bucket=self.bucket,
                CopySource={'Bucket': self.bucket, 'Key': file_path},
                Key=new_path
            )
            
            # Delete original file
            self.s3.delete_object(Bucket=self.bucket, Key=file_path)
            
            #print(f"{SUCCESS} Moved {file_path} to {new_path}")
            return True
            
        except Exception as e:
            #print(f"{ERROR} Failed to move {file_path}: {e}")
            return False

    def delete_files(self, file_path) -> bool:
        try:
            return self.move_to_processed(file_path)
        except Exception as e:
            print(f"{ERROR} Failed to delete {file_path}: {e}")
            return False

""" 3. DB MANAGER : Wrapper class that manages the database interactions. Insert, Update, Select Queries """
class DBManager:
    __slots__ = ('database', 'client', 'cluster_arn', 'secret_arn', '_base_params')
    
    def __init__(self, database_name: str, cluster_arn: Optional[str] = None, secret_arn: Optional[str] = None):
        self.database       = database_name
        self.client         = boto3.client('rds-data', region_name=REGION)
        self.cluster_arn    = cluster_arn or os.environ['AURORA_CLUSTER_ARN']
        self.secret_arn     = secret_arn or os.environ['AURORA_SECRET_ARN']
        
        # Pre-compute base parameters
        self._base_params: Dict[str, Any] = {
            'resourceArn'   : self.cluster_arn,
            'secretArn'     : self.secret_arn,
            'database'      : self.database
        }

    def _format_parameters(self, params: Dict[str, Any]) -> List[Dict]:
        """Ultra-fast parameter formatting"""
        return [
            {'name': k, 'value': self._get_value_dict(v)}
            for k, v in params.items()
        ]
    
    def _get_postgres_type(self, field_name: str, type_map: Dict) -> Optional[str]:
        """Get PostgreSQL type for field"""
        for pg_type, fields in type_map.items():
            if field_name in fields:
                # Return the actual PostgreSQL type name
                if pg_type == 'varchar_array':
                    return 'varchar[]'  # Convert to proper PostgreSQL syntax
                elif pg_type == 'timestamp':
                    return 'timestamp'  # Convert to proper PostgreSQL syntax
                else:
                    return pg_type
        return None


    @staticmethod
    def _validate_sql_identifier(identifier: str) -> bool:
        """Validate SQL identifier to prevent injection"""
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))
    
    @staticmethod
    def _get_value_dict(value: Any) -> Dict:
        """Optimized value type detection with JSON support"""
        if value is None:
            return {'isNull': True}
        elif isinstance(value, bool):
            return {'booleanValue': value}
        elif isinstance(value, int):
            return {'longValue': value}
        elif isinstance(value, float):
            return {'doubleValue': value}
        elif isinstance(value, datetime):
            return {'stringValue': value.isoformat()}
        elif isinstance(value, (dict, list)):
            return {'stringValue': json.dumps(value)}
        else:
            return {'stringValue': str(value)}

    @lru_cache(maxsize=128)
    def _extract_columns(self, query: str) -> tuple:
        """Cached column extraction with regex"""
        match = re.search(r'select\s+(.*?)\s+from', query.lower())
        if not match:
            return ()
        
        cols = [col.strip() for col in match.group(1).split(',')]
        return tuple(
            col.split(' as ')[-1].strip() if ' as ' in col.lower() 
            else col.split('.')[-1].strip() 
            for col in cols
        )

    def _format_results(self, response: Dict, columns: tuple, single: bool = False) -> Union[List[Dict], Dict, None]:
        """Lightning-fast result formatting"""
        records = response.get('records', [])
        if not records:
            return None if single else []
        
        results = [
            {col: next(iter(val.values())) if val else None 
             for col, val in zip(columns, record)}
            for record in records
        ]
        
        if single:
            return results[0] if results else None
        return results

    def execute_statement(self, sql: str, params: Optional[Dict] = None) -> Dict:
        """Optimized execution"""
        exec_params         = self._base_params.copy()
        exec_params['sql']  = sql
        
        if params:
            exec_params['parameters'] = self._format_parameters(params)
        
        return self.client.execute_statement(**exec_params)

    def select(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fast select multiple"""
        try:
            response    = self.execute_statement(query, params)
            columns     = self._extract_columns(query)
            result      = self._format_results(response, columns)
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"{ERROR} Select error: {e}")
            return []

    def select_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fast select single"""
        try:
            response    = self.execute_statement(query, params)
            columns     = self._extract_columns(query)
            result      = self._format_results(response, columns, single=True)

            return result if isinstance(result, dict) else None
        except Exception as e:
            print(f"{ERROR} Select one error: {e}")
            return None

    # Update & Insert = Upsert, this is used to update or insert into the Database
    #
    # ONE call per row, down from two. The old shape did a SELECT existence check followed by
    # either UPDATE or INSERT - two Data API round trips per row, at ~200ms each. On a
    # 100-row loader that was ~40s just in network. INSERT ... ON CONFLICT ... DO UPDATE
    # collapses both branches into a single statement and lets Postgres decide which side to
    # take by consulting the unique index on unique_keys
    #
    # Requires: unique_keys MUST match a real UNIQUE constraint on the table, otherwise
    # ON CONFLICT will error. Every existing call site is audited to match. If a new caller
    # is added, add the constraint alongside it - or fall back to the old SELECT-then-write
    # shape by keeping this method's SELECT path as a helper
    #
    # Returns 'created' or 'updated' via the xmax=0 trick: on an INSERT that hit no conflict
    # xmax is 0 because no transaction touched the row before this one; on a DO UPDATE it
    # holds the txid of the update, so it is non-zero. That makes stats attribution precise
    # without a separate query
    def upsert(self, table: str, data: Dict, unique_keys: Union[str, List[str]], stats: Optional[Dict] = None) -> str:
        """Generic upsert. One Data API call per row via INSERT ... ON CONFLICT ... DO UPDATE."""
        try:
            if not self._validate_sql_identifier(table):
                raise ValueError(f"Invalid table name: {table}")

            if isinstance(unique_keys, str):
                unique_keys = [unique_keys]

            for key in unique_keys + list(data.keys()):
                if not self._validate_sql_identifier(key):
                    raise ValueError(f"Invalid column name: {key}")

            # A row lacking any of its declared unique_keys can't be routed by ON CONFLICT
            # to the right existing row, so refuse rather than write a duplicate
            if not all(k in data for k in unique_keys):
                return 'error'

            cols = list(data.keys())

            # Typed placeholders for VALUES, same rules as before
            placeholders = []
            for col in cols:
                pg_type = self._get_postgres_type(col, AWS_TYPECAST_2)
                placeholders.append(f":{col}::{pg_type}" if pg_type else f":{col}")

            # SET clause for the DO UPDATE branch. id/created_at deliberately excluded so a
            # re-insert of the same row does not overwrite them
            update_cols  = [c for c in cols if c not in unique_keys and c not in ('id', 'created_at')]
            update_parts = []
            for c in update_cols:
                pg_type = self._get_postgres_type(c, AWS_TYPECAST_2)
                update_parts.append(f"{c} = EXCLUDED.{c}::{pg_type}" if pg_type else f"{c} = EXCLUDED.{c}")

            if update_parts:
                on_conflict = f"({', '.join(unique_keys)}) DO UPDATE SET {', '.join(update_parts)}" # nosec B608
            else:
                # Nothing to update besides id/created_at means the row is fully identified by
                # its keys alone (e.g. product_accounts). DO NOTHING is the honest semantic
                on_conflict = f"({', '.join(unique_keys)}) DO NOTHING"

            sql = (
                f"INSERT INTO {table} ({', '.join(cols)}) "  # nosec B608
                f"VALUES ({', '.join(placeholders)}) "
                f"ON CONFLICT {on_conflict} "
                # xmax=0 on a fresh row, non-zero on a DO UPDATE row. RETURNING gives one row
                # per applied statement; a DO NOTHING that skipped returns no row at all
                f"RETURNING (xmax = 0) AS was_created"
            )

            response = self.execute_statement(sql, data)
            records  = response.get('records', [])

            if not records:
                # DO NOTHING path with no update columns and a conflict on existing row
                if stats: stats['SKIPPED'] += 1
                return 'skipped'

            was_created = next(iter(records[0][0].values())) if records[0] else False

            if was_created:
                if stats: stats['CREATED'] += 1
                return 'created'
            else:
                if stats: stats['UPDATED'] += 1
                return 'updated'

        except Exception as e:
            print(f"{ERROR} Upsert error for {table}: {e}")
            if stats: stats['SKIPPED'] += 1
            return 'error'

    # Batch upsert - collapses N per-row calls into ONE network round trip
    #
    # The RDS Data API's batch_execute_statement takes an array of parameter sets, applies
    # the same SQL to each, and returns per-row results in a single call. For a leaf table
    # like exposure_finding_trait that carries ~200 rows per file, this is the difference
    # between ~400 network calls (SELECT + UPSERT per row via the regular upsert method) and
    # 1 call for the whole load.
    #
    # Only usable when every row shares the same column set - which is exactly the case for
    # the exposure/threat/trait loaders where rows are built from a fixed allowlist. If any
    # row has a different key set, split into groups by key set and batch each group.
    #
    # Uses INSERT ... ON CONFLICT ... DO UPDATE so a re-run of the same batch is idempotent.
    # RETURNING is not used - callers that need the generated id must either pre-fetch a
    # {unique_key -> id} map (see load_security_hub_v2_data) or fall back to select_one
    def batch_upsert(self, table: str, rows: List[Dict], unique_keys: Union[str, List[str]], stats: Optional[Dict] = None) -> int:
        """Batch upsert N rows in ONE Data API call. Returns row count applied."""
        try:
            if not rows:
                return 0

            if not self._validate_sql_identifier(table):
                raise ValueError(f"Invalid table name: {table}")

            if isinstance(unique_keys, str):
                unique_keys = [unique_keys]

            # Column list is the UNION of every row's keys, so rows with different key sets
            # (e.g. service_resources where some rows have 'engine' and others don't) all fit
            # under one SQL statement. Missing keys per row are backfilled with None below
            cols = []
            seen = set()
            for row in rows:
                for k in row.keys():
                    if k not in seen:
                        seen.add(k)
                        cols.append(k)

            for key in unique_keys + cols:
                if not self._validate_sql_identifier(key):
                    raise ValueError(f"Invalid column name: {key}")

            # Normalize every row to the full column set. This has to happen before
            # _format_parameters so that batch_execute_statement gets a consistent shape
            rows = [{c: row.get(c) for c in cols} for row in rows]

            # Typed placeholders, same rules as the single-row upsert
            placeholders = []
            for col in cols:
                pg_type = self._get_postgres_type(col, AWS_TYPECAST_2)
                placeholders.append(f":{col}::{pg_type}" if pg_type else f":{col}")

            # Update every non-key column on conflict. Skipping id/created_at matches the
            # single-row upsert's convention
            update_cols  = [c for c in cols if c not in unique_keys and c not in ('id', 'created_at')]
            update_parts = []
            for c in update_cols:
                pg_type = self._get_postgres_type(c, AWS_TYPECAST_2)
                update_parts.append(f"{c} = EXCLUDED.{c}::{pg_type}" if pg_type else f"{c} = EXCLUDED.{c}")

            on_conflict = f"({', '.join(unique_keys)}) DO UPDATE SET {', '.join(update_parts)}" if update_parts else f"({', '.join(unique_keys)}) DO NOTHING" # nosec B608

            sql = (
                f"INSERT INTO {table} ({', '.join(cols)}) "  # nosec B608
                f"VALUES ({', '.join(placeholders)}) "
                f"ON CONFLICT {on_conflict}"
            )

            # batch_execute_statement takes an array of parameter sets, each formatted the
            # same way execute_statement's single 'parameters' field is
            parameter_sets = [self._format_parameters(row) for row in rows]

            self.client.batch_execute_statement(
                resourceArn     = self.cluster_arn,
                secretArn       = self.secret_arn,
                database        = self.database,
                sql             = sql,
                parameterSets   = parameter_sets
            )

            if stats:
                stats['CREATED'] += len(rows)   # rough attribution, batch API does not
                                                # distinguish INSERT from UPDATE per row
            return len(rows)

        except Exception as e:
            print(f"{ERROR} Batch upsert error for {table}: {e}")
            if stats: stats['SKIPPED'] += len(rows)
            return 0

###END: HELPER CLASSES###

""" 4. CORE MANAGER : Manages the Data Loadign from the JSON File to Aurora Postgres """
class CoreManager:
    def __init__(self):
        self.sts_client = boto3.client('sts')
        self.db         = DBManager(database_name=DB_NAME or '', cluster_arn=ARN_AURORA, secret_arn=ARN_SECRET)
        self.stats      = {'CREATED': 0, 'UPDATED': 0, 'SKIPPED': 0, 'TOTAL': 0, 'LOADED': 0}
        self.curr_acct  = None  

    def set_log(self, log_type:AWSLogType, topic:AWSResourceType, msg=None):
        message = msg if msg is not None else "Data Loaded"
        if self.curr_acct is None:
            account_id = "Unknown"
        else:
            account_id = self.curr_acct['account_id']
        
        if log_type == "WARN":
            print(f"{FAIL} {account_id}/{topic.value} : {message}")
        elif log_type == "ERROR":
            print(f"{ERROR} {account_id}/{topic.value} Error : {message}")
        #else:
        #    print(f"{SUCCESS} {account_id}/{topic.value} : {message}")

    def validate_data_structure(self, data: Dict) -> bool:
        """Validate required attributes exist"""
        required_attrs = {
            'account', 'config', 'service', 'cost', 'security',
            'inventory', 'marketplace', 'trusted_advisor', 'health',
            'application', 'resilience_hub', 'logs'
        }
        return required_attrs.issubset(set(data.keys()))

    def _get_default_account(self, key: str, account_id: str) -> str:
        """Get default values for null fields"""
        defaults = {
            'account_name'      : 'Unknown',
            'account_email'     : 'unknown@example.com',
            'account_status'    : 'ACTIVE',
            'account_arn'       : f"arn:aws:organizations::{account_id}:account",
            'joined_method'     : 'CREATED',
            'csp'               : 'AWS',
            'account_type'      : 'PRODUCTION',
            'joined_timestamp'  : '1970-01-01T00:00:00Z'
        }
        return defaults.get(key, '')
    

    
    #Method: UPSERT
    def load_account_data(self, data: Dict) -> bool:
        """Load account data with parent-child upsert like inventory"""
        try:
            # Process main account data first (parent)
            if 'account_id' in data:
                account_data = {}
                for k, v in data.items():
                    
                    # Load product if exists
                    if k in ['account_type', 'category', 'customer_name', 'partner_name'] and v and v != 'None':
                        account_data[k] = v
                    
                    elif k not in ['contact_info', 'alternate_contacts', 'product']:
                        account_data[k]     = v if v is not None else self._get_default_account(k, data.get('account_id', ''))
                        account_data["csp"] = self._get_default_account("csp", "AWS")

                # Upsert account
                result = self.db.upsert('accounts', account_data, ['account_id', 'region'], self.stats)
                
                # Get current account for other operations
                if result in ['created', 'updated']:
                    account_result = self.db.select_one(
                        "SELECT id, account_id FROM accounts WHERE account_id = :account_id AND region = :region",
                        {'account_id': data['account_id'], 'region':data['region']}
                    )
                    if account_result:
                        self.curr_acct = account_result

                # Load product if exists (AFTER curr_acct is set)
                if 'product' in data and data['product'] and self.curr_acct is not None:
                    self.load_product_data(data['product'])
            
            # Process contact info (child)
            contact = data.get('contact_info', {})
            if contact and any(v is not None for v in contact.values()) and self.curr_acct is not None:
                contact['account_id'] = self.curr_acct['id']
                self.db.upsert('contact_info', contact, 'account_id', self.stats)
            
            # Process alternate contacts (children)
            alt_contacts = data.get('alternate_contacts', {})
            if alt_contacts and self.curr_acct is not None:
                for contact_type, contact_data in alt_contacts.items():
                    if contact_data:
                        contact_record = {
                            'account_id'    : self.curr_acct['id'],
                            'contact_type'  : contact_type,
                            'full_name'     : contact_data.get('name'),
                            'title'         : contact_data.get('title'),
                            'email'         : contact_data.get('email')
                        }
                        self.db.upsert('alternate_contacts', contact_record, ['account_id', 'contact_type'], self.stats)
            
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.ACCOUNT)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.ACCOUNT, msg=e)
            return False
    
    #Method: UPSERT
    def load_product_data(self, product_name: str) -> bool:
        """Load products (comma-delimited) and link to account"""
        try:
            if not self.curr_acct or not product_name:
                return False
            
            # Split by comma and process each product
            products = [p.strip() for p in product_name.split(',') if p.strip()]
            
            # Get product IDs for new products
            new_product_ids = []
            for prod in products:
                if self._load_product(prod):
                    product = self.db.select_one("SELECT id FROM products WHERE LOWER(name) = LOWER(:name)", {'name': prod})
                    if product:
                        new_product_ids.append(product['id'])
            
            # Remove old product links not in new list
            if new_product_ids:
                placeholders            = ','.join([f':id{i}' for i in range(len(new_product_ids))])
                params                  = {f'id{i}': pid for i, pid in enumerate(new_product_ids)}
                params['account_id']    = self.curr_acct['id']
                
                self.db.execute_statement(f"DELETE FROM product_accounts WHERE account_id = :account_id AND product_id NOT IN ({placeholders})", params)  # nosec B608

            
            return True
        except Exception as e:
            print(f"{ERROR} Product load error: {e}")
            return False
    
    def _load_product(self, product_name: str) -> bool:
        """Load single product and link to account"""
        try:
            # Check if product exists (case-insensitive)
            product = self.db.select_one("SELECT id FROM products WHERE LOWER(name) = LOWER(:name)", {'name': product_name})
            
            if product:
                # Update existing product
                self.db.upsert('products', {'id': product['id'], 'name': product_name, 'owner': 'System'}, 'id', self.stats)
            else:
                # Create new product
                self.db.upsert('products', {'name': product_name, 'owner': 'System'}, 'name', self.stats)
                product = self.db.select_one("SELECT id FROM products WHERE LOWER(name) = LOWER(:name)", {'name': product_name})
            
            if product and self.curr_acct is not None:
                # Link product to account
                self.db.upsert('product_accounts', 
                              {'product_id': product['id'], 'account_id': self.curr_acct['id']}, 
                              ['product_id', 'account_id'], self.stats)
            return True
        except Exception as e:
            print(f"{ERROR} Single product load error: {e}")
            return False
    #Method: UPSERT
    def load_config_data(self, data: Dict) -> bool:
        """Load config data with parent-child upsert like inventory"""
        try:
            if not self.curr_acct:
                print(f"{ERROR} No account loaded")
                return False
            
            non_compliant   = data.pop('non_compliant_resources', [])
            # Load config report first (parent)
            data['account_id']  = self.curr_acct['id']
            result              = self.db.upsert('config_reports', data, ['account_id', 'date_from'], self.stats)
            
            # Get config_report_id for resources
            if result in ['created', 'updated']:
                db_config = self.db.select_one(
                    "SELECT id FROM config_reports WHERE account_id = :account_id AND date_from = :date_from::date",
                    {'account_id': self.curr_acct['id'], 'date_from': data['date_from']}
                )
                
                # Load non-compliant resources (children) - batched. This table accumulates
                # ~200 rows per run and holds ~80k rows total across all history, so the
                # per-row upsert path was the biggest single tail-latency contributor
                if db_config and non_compliant:
                    ncr_rows = []
                    for resource in non_compliant:
                        resource['created_at']          = resource.pop('config_rule_invoked_time', None)
                        resource['config_report_id']    = db_config['id']
                        ncr_rows.append(resource)

                    if ncr_rows:
                        self.db.batch_upsert('non_compliant_resources', ncr_rows,
                                              ['config_report_id', 'resource_id', 'rule_name'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.CONFIG)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.CONFIG, msg=e)
            print(f"{ERROR} Config load error: {e}")
            return False
    #Method: UPSERT
    def load_service_data(self, data: List[Dict]) -> bool:
        """Load service data with blazing fast upsert"""
        try:
            if not self.curr_acct:
                print(f"{ERROR} No account loaded")
                return False
            
            # Define schema fields to filter JSON data
            service_fields = {
                'account_id', 'service', 'date_from', 'date_to', 'cost', 
                'currency', 'utilization', 'utilization_unit', 'usage_types'
            }
            
            if isinstance(data, list):
                service_rows = []
                for service in data:
                    # Filter to only schema fields
                    filtered_service                = {k: v for k, v in service.items() if k in service_fields}
                    filtered_service['account_id']  = self.curr_acct['id']

                    # Convert usage_types array to comma-separated string
                    if 'usage_types' in filtered_service and isinstance(filtered_service['usage_types'], list):
                        filtered_service['usage_types'] = ','.join(str(item) for item in filtered_service['usage_types'])

                    service_rows.append(filtered_service)

                if service_rows:
                    self.db.batch_upsert('services', service_rows,
                                          ['account_id', 'service', 'usage_types', 'date_from'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SERVICE)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.SERVICE, msg=e)
            return False
    #Method: UPSERT
    def load_cost_data(self, data: Dict) -> bool:
        """Load cost data with parent-child upsert like inventory"""
        try:
            if not self.curr_acct:
                print(f"{ERROR} No account loaded")
                return False
            
            cost_map = {}  # Map cost_report_id
            
            # Extract nested data
            top_services = data.pop('top_services', [])
            forecasts = data.pop('forecast', [])
            period = data.pop('period', {})
            
            # Load cost report first (parent)
            cost_report =   {
                                **data,
                                'account_id'        : self.curr_acct['id'],
                                'period_start'      : period.get('start'),
                                'period_end'        : period.get('end'),
                                'period_granularity': period.get('granularity'),
                                'region'            : "Global"                  # Cost Explorer is a Global Service
                            }
            
            result = self.db.upsert('cost_reports', cost_report, ['account_id', 'period_start', 'region'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Cost Reports Loaded")

            # Get cost_report_id for children
            if result in ['created', 'updated']:
                db_cost = self.db.select_one(
                    "SELECT id FROM cost_reports WHERE account_id = :account_id AND period_start = :period_start::date",
                    {'account_id': self.curr_acct['id'], 'period_start': cost_report['period_start']}
                )
                if db_cost:
                    cost_map['cost_report_id'] = db_cost['id']
            
            # Load service costs (children) - batched
            if top_services and cost_map:
                cost_report_id = cost_map['cost_report_id']

                cost_rows = [
                    {
                        'cost_report_id': cost_report_id,
                        'service_name'  : service['service'],
                        'cost'          : service['cost'],
                        'region'        : "Global"                  # Cost Explorer is a Global Service
                    }
                    for service in top_services
                ]
                if cost_rows:
                    self.db.batch_upsert('service_costs', cost_rows,
                                          ['cost_report_id', 'service_name', 'region'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Service Cost Loaded")

            # Load forecasts (children) - batched
            if forecasts and cost_map:
                cost_report_id = cost_map['cost_report_id']

                forecast_rows = [
                    {
                        'cost_report_id': cost_report_id,
                        'period_start'  : forecast['period']['start'],
                        'period_end'    : forecast['period']['end'],
                        'amount'        : forecast['amount'],
                        'region'        : "Global"                  # Cost Explorer is a Global Service
                    }
                    for forecast in forecasts
                ]
                if forecast_rows:
                    self.db.batch_upsert('cost_forecasts', forecast_rows,
                                          ['cost_report_id', 'period_start', 'region'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Cost Forecast Loaded")

            
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.COST, msg=e)
            
            return False
    #Method: UPSERT
    def load_security_data(self, data: Dict) -> bool:
        """Load comprehensive security data with blazing fast upserts"""
        # Per sub-block timing when DEBUG is on. _lap is a no-op when off. Sub-block
        # timing lives HERE, not on the outer loader, because load_security_data is a
        # single ThreadPoolExecutor future - the loader-level timer treats it as one
        # opaque call, so a bottleneck inside it needs its own instrumentation
        import time as _t
        _sec_marks = [('start', _t.time())] if DEBUG else None
        def _lap(label):
            if _sec_marks is not None:
                _sec_marks.append((label, _t.time()))
        try:
            # Define schema fields for each security service
            guard_duty_fields           =   {
                                                'account_id', 'detector_id', 'finding_type', 'severity', 
                                                'title', 'description', 'confidence', 'region'
                                            }
            kms_fields                  =   {
                                                'account_id', 'key_id', 'arn', 'description', 'key_usage', 
                                                'key_state', 'creation_date', 'enabled', 'key_rotation_enabled'
                                            }
            waf_fields                  =   {
                                                'account_id', 'name', 'waf_id', 'arn', 'scope', 'description', 
                                                'default_action', 'rules_count', 'logging_enabled', 
                                                'geo_blocking_enabled', 'blocked_countries'
                                            }
            waf_rules_detailed_fields   =   {
                                                'account_id', 'web_acl_name', 'rule_name', 'priority', 'action',
                                                'statement_type', 'is_managed_rule', 'is_custom_rule', 'rate_limit',
                                                'logging_enabled', 'geo_blocking', 'sql_injection', 'sample_request_enabled',
                                                'cloudwatch_enabled', 'has_xss_protection', 'waf_version', 'is_compliant', 'scope'
                                            }
            cloudtrail_fields           =   {
                                                'account_id', 'name', 'arn', 'is_logging', 'is_multi_region', 
                                                's3_bucket', 'kms_key_id', 'log_file_validation', 'latest_delivery_time'
                                            }
            secrets_fields              =   {
                                                'account_id', 'name', 'arn', 'description', 'created_date', 
                                                'last_changed_date', 'rotation_enabled'
                                            }
            cert_fields                 =   {
                                                'account_id', 'arn', 'domain_name', 'status', 'type', 'not_after'
                                            }
            inspector_fields            =   {
                                                'account_id', 'finding_arn', 'severity', 'status', 'type', 
                                                'title', 'description', 'first_observed_at'
                                            }
            finding_fields              =   {
                                                'security_id', 'finding_id', 'service', 'title', 'description',
                                                'severity', 'status', 'resource_type', 'resource_id', 'created_at',
                                                'updated_at', 'recommendation', 'compliance_status', 'region',
                                                'workflow_state', 'record_state', 'product_name', 'company_name',
                                                'product_arn', 'generator_id', 'generator'
                                            }
            security_map                =   {}  # Load Security Hub summaries first (parent), Map service to security_id Map service to security_id

            # Load Security Hub summaries first (parent)
            if 'security_hub' in data:
                for security_service in data['security_hub']:
                    # Extract severity counts
                    severity_counts = security_service.get('severity_counts', {})
                    
                    # Build security summary record directly
                    if self.curr_acct is None:
                        continue
                    filtered_security = {
                                            'account_id'            : self.curr_acct['id'],
                                            'service'               : security_service.get('service'),
                                            'total_findings'        : security_service.get('total_findings', 0),
                                            'critical_count'        : severity_counts.get('CRITICAL', 0),
                                            'high_count'            : severity_counts.get('HIGH', 0),
                                            'medium_count'          : severity_counts.get('MEDIUM', 0),
                                            'low_count'             : severity_counts.get('LOW', 0),
                                            'informational_count'   : severity_counts.get('INFORMATIONAL', 0),
                                            'open_findings'         : security_service.get('open_findings', 0),
                                            'resolved_findings'     : security_service.get('resolved_findings', 0)
                                        }
                    
                    # Upsert security summary
                    result = self.db.upsert('security', filtered_security, ['account_id', 'service'], self.stats)
                    
                    # Get security_id for findings mapping
                    if result in ['created', 'updated']:
                        db_security = self.db.select_one(
                            "SELECT id FROM security WHERE account_id = :account_id AND service = :service",
                            {'account_id': self.curr_acct['id'], 'service': security_service.get('service')}
                        )
                        if db_security:
                            security_map[security_service.get('service')] = db_security['id']
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Secrity Hub Loaded")
            _lap("security_hub_summary")
            # Load findings (children) - batched. Legacy Security Hub findings can run into
                # the hundreds per payload against a ~5k-row table, which was ~95% of the entire
                # receiver's wall clock time before batching. Same batch_upsert helper as
                # everywhere else - collapses N calls to 1
            if 'security_hub' in data and security_map:
                finding_rows = []
                for security_service in data['security_hub']:
                    service_name = security_service.get('service')
                    if service_name in security_map and 'findings' in security_service:
                        security_id = security_map[service_name]

                        for finding in security_service['findings']:
                            filtered_finding                = {k: v for k, v in finding.items() if k in finding_fields}
                            filtered_finding['security_id'] = security_id
                            finding_rows.append(filtered_finding)

                if finding_rows:
                    self.db.batch_upsert('findings', finding_rows, 'finding_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Secrity Hub Findings Loaded")
            _lap("security_hub_findings")
            # Load GuardDuty findings
            if 'guard_duty' in data and self.curr_acct is not None:
                for finding in data['guard_duty']:
                    filtered_finding = {k: v for k, v in finding.items() if k in guard_duty_fields}
                    filtered_finding['account_id']      = self.curr_acct['id']
                    filtered_finding['detector_id']     = finding.get('id')  # Map 'id' to 'detector_id'
                    filtered_finding['finding_type']    = finding.get('type')  # Map 'type' to 'finding_type'
                    
                    self.db.upsert('guard_duty_findings', filtered_finding, ['account_id', 'detector_id'], self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Guard Duty Loaded")
            _lap("guard_duty")
            # Load KMS keys
            if 'kms' in data and self.curr_acct is not None:
                for key in data['kms']:
                    filtered_key = {k: v for k, v in key.items() if k in kms_fields}
                    filtered_key['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('kms_keys', filtered_key, 'key_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="KMS Loaded")
            _lap("kms")
            # Load WAF rules
            if 'waf' in data and self.curr_acct is not None:
                for waf in data['waf']:
                    filtered_waf = {k: v for k, v in waf.items() if k in waf_fields}
                    filtered_waf['account_id']  = self.curr_acct['id']
                    filtered_waf['waf_id']      = waf.get('id')  # Map 'id' to 'waf_id'
                    
                    self.db.upsert('waf_rules', filtered_waf, 'waf_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="WAF Loaded")
            _lap("waf")

            # Load WAF rules detailed
            if 'waf_rules' in data and self.curr_acct is not None:
                for rule in data['waf_rules']:
                    filtered_rule = {k: v for k, v in rule.items() if k in waf_rules_detailed_fields}
                    filtered_rule['account_id'] = self.curr_acct['id']
                    
                    # Convert action dict to JSON string for TEXT field
                    if 'action' in filtered_rule and isinstance(filtered_rule['action'], dict):
                        filtered_rule['action'] = json.dumps(filtered_rule['action'])
                    
                    self.db.upsert('waf_rules_detailed', filtered_rule, ['account_id', 'web_acl_name', 'rule_name'], self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="WAF Rules Detailed Loaded")
            _lap("waf_rules_detailed")

            # Load CloudTrail logs
            if 'cloudtrail' in data and self.curr_acct is not None:
                for trail in data['cloudtrail']:
                    filtered_trail = {k: v for k, v in trail.items() if k in cloudtrail_fields}
                    filtered_trail['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('cloudtrail_logs', filtered_trail, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Cloud Trail Loaded")
            _lap("cloudtrail")

            # Load Secrets Manager secrets
            if 'secrets_manager' in data and self.curr_acct is not None:
                for secret in data['secrets_manager']:
                    filtered_secret = {k: v for k, v in secret.items() if k in secrets_fields}
                    filtered_secret['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('secrets_manager_secrets', filtered_secret, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Secrets Manager Loaded")
            _lap("secrets_manager")

            # Load Certificate Manager certificates
            if 'certificate_manager' in data and self.curr_acct is not None:
                for cert in data['certificate_manager']:
                    filtered_cert = {k: v for k, v in cert.items() if k in cert_fields}
                    filtered_cert['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('certificates', filtered_cert, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Certificate Manager Loaded")
            _lap("certificate_manager")
            # Load Inspector findings - batched, N calls collapse to 1
            if 'inspector' in data and self.curr_acct is not None:
                inspector_rows = []
                for finding in data['inspector']:
                    filtered_finding = {k: v for k, v in finding.items() if k in inspector_fields}
                    filtered_finding['account_id'] = self.curr_acct['id']
                    inspector_rows.append(filtered_finding)

                if inspector_rows:
                    self.db.batch_upsert('inspector_findings', inspector_rows, 'finding_arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Inspector Loaded")
            _lap("inspector")

            # Load Security Hub V2 (exposures, threats, standards)
            self.load_security_hub_v2_data(data)
            _lap("security_hub_v2")

            if _sec_marks is not None:
                _prev = _sec_marks[0][1]
                for _lbl, _t_at in _sec_marks[1:]:
                    print(f"{TIMING}   security.{_lbl}: {round(_t_at - _prev, 2)}s")
                    _prev = _t_at

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.COST, msg=e)
            return False
    #Method: UPSERT

    def load_security_hub_v2_data(self, data: Dict) -> bool:
        """Load Security Hub V2 (OCSF): exposures with their contributed findings and traits,
        threats, and security standards. A finding present in an earlier run but absent from
        this one is marked RESOLVED rather than deleted, so the row stays as history.

        NOTE: get_security_hub_v2 in sender.py wraps both the exposures and threats fetch in
        one try/except that returns {} on any failure, exactly like an empty result. A
        transient AWS throttle or IAM change on the sender side is therefore indistinguishable
        here from a genuinely quiet day, and the resolve step below would incorrectly close
        every real open exposure/threat for the account. Known gap, matches the same blind
        spot already flagged on get_security's except blocks - not guarded here by design,
        revisit alongside that.
        """
        try:
            if self.curr_acct is None:
                return False

            exposure_fields         =   {
                                            'account_id', 'finding_id', 'finding_arn', 'service', 'title',
                                            'description', 'severity', 'status', 'resource_type', 'resource_id',
                                            'created_at', 'updated_at', 'recommendation', 'compliance_status',
                                            'region', 'workflow_state', 'record_state', 'product_name',
                                            'company_name', 'product_arn', 'generator_id', 'generator',
                                            'cve_id', 'cvss_score', 'cvss_severity', 'cvss_version',
                                            'cvss_vector', 'epss_score', 'cve_count'
                                        }
            contributed_fields      =   {
                                            'finding_id', 'finding_arn', 'source', 'title', 'is_finding',
                                            'resource_uid', 'cve_id', 'cvss_score', 'cvss_severity',
                                            'cvss_version', 'cvss_vector', 'epss_score', 'cve_count',
                                            'trait_count', 'trait_categories', 'trait_names',
                                            # status/workflow_state are nullable and not emitted by the sender
                                            # today, but the allowlist accepts them so a future sender value
                                            # flows through untouched. The resolve-close UPDATE below treats
                                            # NULL as active via IS DISTINCT FROM 'RESOLVED'
                                            'status', 'workflow_state'
                                        }
            trait_fields            =   {'category', 'name', 'type'}
            threat_fields           =   {
                                            'account_id', 'finding_id', 'finding_arn', 'service', 'title',
                                            'description', 'severity', 'status', 'resource_type', 'resource_id',
                                            'created_at', 'updated_at', 'recommendation', 'region',
                                            'workflow_state', 'record_state', 'product_name', 'company_name',
                                            'product_arn', 'generator_id', 'generator', 'finding_type',
                                            'analytic_type', 'actor_name', 'actor_uid', 'api_operation',
                                            'api_service', 'source_ip', 'source_country'
                                        }
            standards_fields        =   {
                                            'account_id', 'standard_name', 'standard_arn', 'subscription_arn',
                                            'status', 'passed', 'failed', 'score', 'date_from', 'date_to'
                                        }

            # Load exposures (parent), then contributed findings (child), then traits (grandchild)
            #
            # Data API round-trip cost dominates here: every upsert is already a 2-call
            # SELECT+INSERT/UPDATE. A naive select_one per parent to resolve its integer id for
            # the child FK adds a 3rd call per row, and stacked three levels deep it blows out
            # to ~40 calls per exposure. Instead, the parent id maps are pre-fetched ONCE per
            # level with a single SELECT, and the child upsert reads its FK out of the map.
            # Same trick as security_map / instance_map used elsewhere in this file
            if 'exposures' in data:
                # {finding_id -> exposure_findings.id} for this account, one call
                existing = self.db.select(
                    "SELECT id, finding_id FROM exposure_findings WHERE account_id = :account_id",
                    {'account_id': self.curr_acct['id']}
                )
                exposure_id_map = {row['finding_id']: row['id'] for row in existing}

                # {(exposure_finding_id, finding_id) -> exposure_contributed_finding.id}
                existing_contrib = self.db.select(
                    "SELECT id, exposure_finding_id, finding_id FROM exposure_contributed_finding WHERE account_id = :account_id",
                    {'account_id': self.curr_acct['id']}
                )
                contrib_id_map = {(row['exposure_finding_id'], row['finding_id']): row['id']
                                  for row in existing_contrib}

                # Exposures upsert one-by-one first, so their SERIAL ids materialize and can be
                # used as FKs for the batched contributor rows below. Exposure count is low
                # (dozens per account) so N per-row calls is acceptable here
                for exposure in data['exposures']:
                    filtered_exposure               = {k: v for k, v in exposure.items() if k in exposure_fields}
                    filtered_exposure['account_id'] = self.curr_acct['id']

                    self.db.upsert('exposure_findings', filtered_exposure, 'finding_id', self.stats)

                    # Newly created rows are absent from the pre-fetch, so resolve one on demand
                    exposure_pk = exposure_id_map.get(exposure.get('finding_id'))
                    if exposure_pk is None:
                        db_exposure = self.db.select_one(
                            "SELECT id FROM exposure_findings WHERE finding_id = :finding_id",
                            {'finding_id': exposure.get('finding_id')}
                        )
                        if db_exposure:
                            exposure_pk = db_exposure['id']
                            exposure_id_map[exposure.get('finding_id')] = exposure_pk

                # Contributors and traits ride on batch_upsert - one Data API call per level
                # replaces N * (2 for the upsert existence-check pattern) row-by-row calls.
                # A typical file with 13 exposures * 3 contributors * 5 traits collapses from
                # ~450 network round trips to 2
                contrib_rows = []
                for exposure in data['exposures']:
                    exposure_pk = exposure_id_map.get(exposure.get('finding_id'))
                    if exposure_pk is None:
                        continue
                    for contributed in exposure.get('contributed_finding', []):
                        filtered_contrib                        = {k: v for k, v in contributed.items() if k in contributed_fields}
                        filtered_contrib['account_id']          = self.curr_acct['id']
                        filtered_contrib['exposure_finding_id'] = exposure_pk
                        contrib_rows.append(filtered_contrib)

                if contrib_rows:
                    self.db.batch_upsert(
                        'exposure_contributed_finding', contrib_rows,
                        ['exposure_finding_id', 'finding_id'], self.stats
                    )

                    # Refresh the contrib id map with newly-created rows so trait FKs resolve.
                    # One SELECT rather than N select_ones - same trick as the initial pre-fetch
                    existing_contrib = self.db.select(
                        "SELECT id, exposure_finding_id, finding_id FROM exposure_contributed_finding WHERE account_id = :account_id",
                        {'account_id': self.curr_acct['id']}
                    )
                    contrib_id_map = {(row['exposure_finding_id'], row['finding_id']): row['id']
                                      for row in existing_contrib}

                trait_rows = []
                for exposure in data['exposures']:
                    exposure_pk = exposure_id_map.get(exposure.get('finding_id'))
                    if exposure_pk is None:
                        continue
                    for contributed in exposure.get('contributed_finding', []):
                        contrib_pk = contrib_id_map.get((exposure_pk, contributed.get('finding_id')))
                        if contrib_pk is None:
                            continue
                        for trait in contributed.get('traits', []):
                            filtered_trait                           = {k: v for k, v in trait.items() if k in trait_fields}
                            filtered_trait['account_id']             = self.curr_acct['id']
                            filtered_trait['contributed_finding_id'] = contrib_pk
                            trait_rows.append(filtered_trait)

                if trait_rows:
                    self.db.batch_upsert(
                        'exposure_finding_trait', trait_rows,
                        ['contributed_finding_id', 'name', 'type'], self.stats
                    )

                # A finding_id in the table but not in this run's payload is no longer being
                # reported by Security Hub, so it is closed out rather than left stale. Runs
                # unconditionally, including when present_ids is empty - an account that now
                # reports zero active exposures must resolve every row it previously had, not
                # skip the update because there was nothing to build a NOT IN list against
                present_ids = {e['finding_id'] for e in data['exposures'] if e.get('finding_id')}
                params      = {f'id{i}': fid for i, fid in enumerate(present_ids)}
                params['account_id'] = self.curr_acct['id']
                not_in      = ' AND finding_id NOT IN ({})'.format(
                                  ','.join(f':id{i}' for i in range(len(present_ids)))
                              ) if present_ids else ''

                self.db.execute_statement(
                    f"UPDATE exposure_findings SET status = 'RESOLVED', workflow_state = 'RESOLVED', "  # nosec B608
                    f"record_state = 'Resolved', updated_at = now() "
                    f"WHERE account_id = :account_id{not_in} AND status != 'RESOLVED'",
                    params
                )

                # Contributors resolve when the same finding_id no longer ties to any active
                # exposure in THIS account. The NOT EXISTS check protects a contributor that
                # is still contributing elsewhere (e.g. one IAM user showing up under several
                # exposures - remove one exposure and the IAM user should stay open while any
                # other exposure it feeds is still active). status IS DISTINCT FROM 'RESOLVED'
                # so both NULL and 'NEW' rows are treated as still-active
                self.db.execute_statement(
                    "UPDATE exposure_contributed_finding ecf "
                    "SET status = 'RESOLVED', workflow_state = 'RESOLVED' "
                    "FROM exposure_findings ef "
                    "WHERE ecf.exposure_finding_id = ef.id "
                    "  AND ecf.account_id = :account_id "
                    "  AND ef.status = 'RESOLVED' "
                    "  AND ecf.status IS DISTINCT FROM 'RESOLVED' "
                    "  AND NOT EXISTS ( "
                    "      SELECT 1 FROM exposure_contributed_finding other_ecf "
                    "      JOIN exposure_findings other_ef ON other_ecf.exposure_finding_id = other_ef.id "
                    "      WHERE other_ecf.finding_id  = ecf.finding_id "
                    "        AND other_ecf.account_id  = ecf.account_id "
                    "        AND other_ef.status      != 'RESOLVED' "
                    "  )",
                    {'account_id': self.curr_acct['id']}
                )
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Exposures Loaded")

            # Load threats - batched, same reasoning as contributors above
            if 'threats' in data:
                threat_rows = []
                for threat in data['threats']:
                    filtered_threat                     = {k: v for k, v in threat.items() if k in threat_fields}
                    filtered_threat['account_id']        = self.curr_acct['id']
                    filtered_threat['occurrence_count']  = threat.get('count', 0)
                    threat_rows.append(filtered_threat)

                if threat_rows:
                    self.db.batch_upsert('threat_findings', threat_rows, 'finding_id', self.stats)

                # Same unconditional resolve as exposures above - see comment there
                present_ids = {t['finding_id'] for t in data['threats'] if t.get('finding_id')}
                params      = {f'id{i}': fid for i, fid in enumerate(present_ids)}
                params['account_id'] = self.curr_acct['id']
                not_in      = ' AND finding_id NOT IN ({})'.format(
                                  ','.join(f':id{i}' for i in range(len(present_ids)))
                              ) if present_ids else ''

                self.db.execute_statement(
                    f"UPDATE threat_findings SET status = 'RESOLVED', workflow_state = 'RESOLVED', "  # nosec B608
                    f"record_state = 'Resolved', updated_at = now() "
                    f"WHERE account_id = :account_id{not_in} AND status != 'RESOLVED'",
                    params
                )
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Threats Loaded")

            # Load security standards (dated snapshot, one row per standard per day)
            if 'standards' in data:
                for standard in data['standards']:
                    filtered_standard               = {k: v for k, v in standard.items() if k in standards_fields}
                    filtered_standard['account_id']  = self.curr_acct['id']

                    self.db.upsert(
                        'security_standards', filtered_standard,
                        ['account_id', 'standard_arn', 'date_from'], self.stats
                    )
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Security Standards Loaded")

            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.SECURITY, msg=e)
            return False
    #Method: UPSERT
    def load_inventory_data(self, data: Dict) -> bool:
        """Load inventory instances, applications, and patches with proper relationships"""
        try:
            instance_map = {}
            
            # Define schema fields
            instance_fields =   {
                                    'account_id', 'instance_id', 'instance_type', 'platform', 
                                    'ip_address', 'computer_name', 'ping_status', 
                                    'last_ping_date_time', 'agent_version', 'platform_version','platform_type',
                                    'is_latest_version','association_status','association_execution_date','association_success_date'
                                }
            app_fields      =   {
                                    'instance_id', 'account_id', 'name', 'version', 'publisher', 'architecture', 'application_type', 'install_time'
                                }
            patch_fields    =   {
                                    'instance_id', 'account_id', 'title', 'classification', 'severity', 
                                    'state', 'installed_time'
                                }
            
            # Load instances first
            if 'instances' in data and self.curr_acct is not None:
                for instance in data['instances'] :
                    filtered_instance               = {k: v for k, v in instance.items() if k in instance_fields}
                    filtered_instance['account_id'] = self.curr_acct['id']
                    
                    result = self.db.upsert('inventory_instances', filtered_instance, 'instance_id', self.stats)
                    
                    if result in ['created', 'updated']:
                        db_instance = self.db.select_one(
                            "SELECT id FROM inventory_instances WHERE instance_id = :instance_id",
                            {'instance_id': instance['instance_id']}
                        )
                        if db_instance:
                            instance_map[instance['instance_id']] = db_instance['id']
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.INVENTORY, msg="Inventory Instances Loaded")

            # Load applications - batched. This is the biggest loop in the file (~100 rows on
            # a typical account), so collapsing N calls to 1 is the biggest single wall-clock
            # win from this batching pass
            if 'applications' in data and instance_map and self.curr_acct is not None:
                first_instance_db_id = next(iter(instance_map.values()))

                app_rows = []
                for app in data['applications']:
                    filtered_app                = {k: v for k, v in app.items() if k in app_fields}
                    filtered_app['instance_id'] = first_instance_db_id
                    filtered_app['account_id']  = self.curr_acct['id']  # Add account_id
                    app_rows.append(filtered_app)

                if app_rows:
                    self.db.batch_upsert('inventory_applications', app_rows,
                                          ['account_id', 'instance_id', 'name', 'version'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.INVENTORY, msg="Inventory Applications Loaded")

            # Load patches
            if 'patches' in data and instance_map and self.curr_acct is not None:
                first_instance_db_id = next(iter(instance_map.values()))
                
                for patch in data['patches']:
                    filtered_patch                  = {k: v for k, v in patch.items() if k in patch_fields}
                    filtered_patch['instance_id']   = first_instance_db_id
                    filtered_patch['account_id']    = self.curr_acct['id']  # Add account_id
                    
                    self.db.upsert('inventory_patches', filtered_patch, ['instance_id', 'title'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.INVENTORY, msg="Inventory Patches Loaded")

            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.INVENTORY, msg=e)
            return False
    #Method: UPSERT
    def load_marketplace_data(self, data: List[Dict]) -> bool:
        """Load marketplace usage with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            marketplace_fields = {
                'account_id', 'product_code', 'product_name', 'cost_consumed', 
                'currency', 'period_start', 'period_end', 'status'
            }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for item in data:
                    # Filter to only schema fields
                    filtered_item               = {k: v for k, v in item.items() if k in marketplace_fields}
                    filtered_item['account_id'] = self.curr_acct['id']
                    
                    # Upsert using composite unique key (account_id + product_code + period_start)
                    self.db.upsert(
                        'marketplace_usage', 
                        filtered_item, 
                        ['account_id', 'product_code', 'period_start'], 
                        self.stats
                    )

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.MARKETPLACE)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.MARKETPLACE, msg=e)
            return False
    #Method: UPSERT
    def load_trusted_advisor_data(self, data: List[Dict]) -> bool:
        """Load trusted advisor checks with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            advisor_fields  =   {
                                    'account_id', 'check_name', 'category', 'severity', 
                                    'recommendation', 'affected_resources_count', 
                                    'potential_savings', 'timestamp'
                                }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for check in data:
                    # Filter to only schema fields
                    filtered_check = {k: v for k, v in check.items() if k in advisor_fields}
                    filtered_check['account_id'] = self.curr_acct['id']
                    
                    # Upsert using composite unique key (account_id + check_name)
                    self.db.upsert(
                                    'trusted_advisor_checks', 
                                    filtered_check, 
                                    ['account_id', 'check_name'], 
                                    self.stats
                                )

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.TRUSTED_ADVISOR)

            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.TRUSTED_ADVISOR, msg=e)
            return False
    #Method: UPSERT
    def load_health_data(self, data: List[Dict]) -> bool:
        """Load health events with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            health_fields   =   {
                                    'account_id', 'arn', 'service', 'event_type_code', 
                                    'region', 'start_time', 'end_time', 'status_code'
                                }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for event in data:
                    # Filter to only schema fields
                    filtered_event                  = {k: v for k, v in event.items() if k in health_fields}
                    filtered_event['account_id']    = self.curr_acct['id']
                    
                    # Upsert using unique key (arn is unique for health events)
                    self.db.upsert(
                                    'health_events', 
                                    filtered_event, 
                                    'arn', 
                                    self.stats
                                )
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.HEALTH)

            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.HEALTH, msg=e)
            return False
    #Method: UPSERT
    def load_application_data(self, data: List[Dict]) -> bool:
        """Load application signals with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            app_fields  =   {
                                'account_id', 'service_name', 'namespace', 'key_attributes'
                            }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for signal in data:
                    # Filter to only schema fields
                    filtered_signal                 = {k: v for k, v in signal.items() if k in app_fields}
                    filtered_signal['account_id']   = self.curr_acct['id']
                    
                    # Convert key_attributes to JSON for JSONB storage
                    if 'key_attributes' in filtered_signal:
                        filtered_signal['key_attributes'] = json.dumps(filtered_signal['key_attributes'])
                    
                    # Upsert using composite unique key (account_id + service_name)
                    self.db.upsert(
                                    'application_signals', 
                                    filtered_signal, 
                                    ['account_id', 'service_name'], 
                                    self.stats
                                )
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.APPLICATION)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.APPLICATION, msg=e)
            return False
    #Method: UPSERT
    def load_resilience_hub_data(self, data: List[Dict]) -> bool:
        """Load resilience hub apps with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            resilience_fields   =   {
                                        'account_id', 'app_arn', 'name', 'description', 'creation_time',
                                        'last_assessment_time', 'compliance_status', 'resiliency_score', 
                                        'status', 'rpo', 'rto', 'last_drill', 'cost'
                                    }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for app in data:
                    # Filter to only schema fields
                    filtered_app                = {k: v for k, v in app.items() if k in resilience_fields}
                    filtered_app['account_id']  = self.curr_acct['id']
                    
                    # Upsert using unique key (app_arn is unique for resilience hub apps)
                    self.db.upsert('resilience_hub_apps', filtered_app, 'app_arn', self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.RESILIENCE_HUB)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.RESILIENCE_HUB, msg=e)
            return False
    #Method: UPSERT
    def load_service_resources_data(self, data: List[Dict]) -> bool:
        """Load service resources with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            resource_fields =   {
                                    'account_id', 'service_name', 'resource_type', 'resource_id', 'resource_name',
                                    'region', 'availability_zone', 'state', 'instance_type', 'vpc_id', 'engine',
                                    'instance_class', 'multi_az', 'size_gb', 'volume_type', 'creation_date',
                                    'type', 'scheme', 'instance_count', 'min_size', 'max_size', 'available_ip_count'
                                }
            
            numeric_fields  =   {'instance_count', 'min_size', 'max_size', 'available_ip_count', 'size_gb'}

            if isinstance(data, list) and self.curr_acct is not None:
                # Build a list first, then send them all in ONE batch call. Different resource
                # types carry different fields (engine, instance_class, etc.) - batch_upsert
                # normalizes to the union of all rows' keys and backfills None for missing
                resource_rows = []
                for resource in data:
                    # Filter to only schema fields
                    filtered_resource               = {k: v for k, v in resource.items() if k in resource_fields}
                    filtered_resource['account_id'] = self.curr_acct['id']

                    for field in numeric_fields:
                        if field in filtered_resource and filtered_resource[field] in ('', None):
                            filtered_resource[field] = None

                    resource_rows.append(filtered_resource)

                if resource_rows:
                    self.db.batch_upsert('service_resources', resource_rows,
                                          ['account_id', 'service_name', 'resource_id'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SERVICE_RESOURCES)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.SERVICE_RESOURCES, msg=e)
            return False
    #Method: UPSERT
    def load_compute_optimizer_data(self, data: List[Dict]) -> bool:
        """Load compute optimizer recommendations with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            optimizer_fields    =   {
                                        'account_id', 'resource_type', 'resource_arn', 'resource_name', 'finding',
                                        'current_instance_type', 'current_memory_size', 'current_volume_type', 'current_volume_size',
                                        'recommended_instance_type', 'recommended_memory_size', 'recommended_volume_type', 'recommended_volume_size',
                                        'savings_opportunity_percentage', 'estimated_monthly_savings_usd', 'performance_risk',
                                        'cpu_utilization_max', 'memory_utilization_avg', 'migration_effort'
                                    }
            
            if isinstance(data, list) and self.curr_acct is not None:
                for recommendation in data:
                    # Filter to only schema fields
                    filtered_rec                = {k: v for k, v in recommendation.items() if k in optimizer_fields}
                    filtered_rec['account_id']  = self.curr_acct['id']
                    
                    # Upsert using unique key (resource_arn is unique for compute optimizer recommendations)
                    self.db.upsert('compute_optimizer', filtered_rec, 'resource_arn', self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COMPUTE_OPTIMIZER)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.COMPUTE_OPTIMIZER, msg=e)
            return False
    #Method: UPSERT
    def load_config_inventory_data(self, data: List[Dict]) -> bool:
        """Load config inventory data with blazing fast upsert"""
        try:
            # Define schema fields to filter JSON data
            inventory_fields    =   {
                                        'account_id', 'resource_type', 'resource_subtype', 'resource_id', 'resource_name', 'region',
                                        'availability_zone', 'state', 'instance_type', 'vpc_id', 'engine',
                                        'instance_class', 'multi_az', 'size_gb', 'volume_type', 'creation_date',
                                        'type', 'scheme', 'instance_count', 'min_size', 'max_size', 'available_ip_count'
                                    }

            if isinstance(data, list) and self.curr_acct is not None:
                for inventory in data:
                    # Filter to only schema fields
                    filtered_inventory                  = {k: v for k, v in inventory.items() if k in inventory_fields}
                    filtered_inventory['account_id']    = self.curr_acct['id']

                    # Upsert using composite unique key (account_id + resource_id)
                    self.db.upsert('config_inventory', filtered_inventory, ['account_id', 'resource_id'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.CONFIG_INVENTORY)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.CONFIG_INVENTORY, msg=e)
            return False
    #Method: UPSERT
    def load_ai_inventory_data(self, data: List[Dict]) -> bool:
        """Load self-hosted AI/ML resource inventory (Security Hub V2 GetResourcesV2).

        Lifecycle: rows in the current payload upsert with status='ACTIVE'; rows in the
        DB but absent from this payload are marked status='INACTIVE' by the NOT IN
        sweep. updated_at moves on every state change (upsert or resolve) so the column
        answers "when did this resource last change state". History is preserved -
        rows are never deleted, so a resource that disappeared last month is still
        queryable via WHERE status='INACTIVE' AND updated_at < ...

        KNOWN GAP: the sender's _get_ai_inventory catches every exception and returns
        []. A transient AWS error therefore looks identical to a genuine zero-resource
        account, and this sweep would incorrectly mark everything INACTIVE. Same
        trade-off as the exposure/threat resolve-close paths
        """
        try:
            if not isinstance(data, list) or self.curr_acct is None:
                return False

            ai_fields = {
                'resource_guid', 'resource_id', 'resource_name', 'resource_type',
                'resource_category', 'resource_sub_category', 'discovery_type',
                'region', 'host_resource_guid', 'host_resource_type', 'canonical_id',
                'model_count', 'agent_count', 'total_ai_count', 'tags', 'created_at'
            }

            _now = datetime.now(timezone.utc)

            rows = []
            for resource in data:
                filtered = {k: v for k, v in resource.items() if k in ai_fields}
                filtered['account_id'] = self.curr_acct['id']
                # Security Hub returns ResourceCreationTimeDt as '' when the resource
                # has no creation timestamp. AWS_TYPECAST_2 casts created_at to
                # timestamp and Postgres rejects '' as invalid syntax (SQLState 22007).
                # Coerce to None so the Data API sends {isNull: true}
                if filtered.get('created_at') == '':
                    filtered['created_at'] = None
                # ACTIVE marks the row as present in this run. NOT IN sweep below flips
                # missing rows to INACTIVE, updating updated_at on the transition
                filtered['status']     = 'ACTIVE'
                filtered['updated_at'] = _now
                rows.append(filtered)

            if rows:
                self.db.batch_upsert(
                    'ai_inventory', rows,
                    ['account_id', 'resource_id'], self.stats
                )

            # Rows in the DB but not in the current payload -> INACTIVE. Runs
            # unconditionally, including when the payload is empty. IS DISTINCT FROM
            # 'INACTIVE' catches both NULL (legacy rows) and 'ACTIVE' rows, while
            # leaving already-INACTIVE rows untouched so their updated_at reflects
            # the day they went inactive, not the day of this run.
            #
            # Keyed on resource_id (not resource_guid) to match the UNIQUE constraint
            # on ai_inventory: the constraint is (account_id, resource_id), and the
            # exposure contributor chain also joins on this column
            present_ids = {r['resource_id'] for r in data if r.get('resource_id')}
            params      = {f'rid{i}': rid for i, rid in enumerate(present_ids)}
            params['account_id'] = self.curr_acct['id']
            not_in = ' AND resource_id NOT IN ({})'.format(
                        ','.join(f':rid{i}' for i in range(len(present_ids)))
                     ) if present_ids else ''

            self.db.execute_statement(
                f"UPDATE ai_inventory SET status = 'INACTIVE', updated_at = now() "  # nosec B608
                f"WHERE account_id = :account_id{not_in} "
                f"AND status IS DISTINCT FROM 'INACTIVE'",
                params
            )

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.AI_INVENTORY)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.AI_INVENTORY, msg=e)
            return False
    #Method: UPSERT
    def load_support_tickets_data(self, data: List[Dict]) -> bool:
        """Load support tickets data with blazing fast upsert"""
        try:
            if not isinstance(data, list) or not self.curr_acct:
                return False
            
            # Define schema fields to filter JSON data
            ticket_fields = {
                'account_id', 'case_id', 'display_id', 'subject', 'status',
                'severity_code', 'service_code', 'category_code', 'time_created',
                'submitted_by', 'language', 'date_from', 'date_to'
            }
            
            for ticket in data:
                # Filter to only schema fields
                filtered_ticket = {k: v for k, v in ticket.items() if k in ticket_fields}
                filtered_ticket['account_id'] = self.curr_acct['id']
                
                # Upsert using unique key (case_id is unique)
                self.db.upsert('support_tickets', filtered_ticket, 'case_id', self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SUPPORT_TICKETS)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.SUPPORT_TICKETS, msg=e)
            return False
    #Method: UPSERT
    def load_ri_sp_savings_data(self, data: List[Dict]) -> bool:
        """Load RI/SP daily savings data with blazing fast upsert"""
        try:
            if not isinstance(data, list) or not self.curr_acct:
                return False
            
            ri_sp_fields = {
                'account_id', 'date_from', 'date_to', 'reservation_type', 'subscription_id', 'offering_id',
                'savings_plan_arn', 'service', 'instance_type', 'instance_count', 'instance_family',
                'instance_tenancy', 'offering_class', 'offering_type', 'product_types', 'region',
                'utilization_percentage', 'on_demand_cost', 'reservation_cost', 'net_savings',
                'commitment', 'upfront_cost', 'recurring_cost', 'recurring_frequency', 'usage_price',
                'currency', 'start_date', 'end_date', 'returnable_until', 'duration_seconds',
                'state', 'description'
            }
            
            for record in data:
                filtered_record = {k: v for k, v in record.items() if k in ri_sp_fields}
                filtered_record['account_id'] = self.curr_acct['id']
                
                # Keys match ri_sp_daily_savings_unique on live: (account_id,
                # subscription_id, date_to, reservation_type). date_from was in the caller
                # here but not in the constraint, so ON CONFLICT would fail
                self.db.upsert('ri_sp_daily_savings', filtered_record,
                              ['account_id', 'subscription_id', 'date_to', 'reservation_type'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.RI_SP_SAVINGS)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.RI_SP_SAVINGS, msg=e)
            return False
    #Method: UPSERT
    def load_logs_data(self, data: Dict) -> bool:
        try:
            if not self.curr_acct:
                print(f"{ERROR} No account loaded")
                return False
            
            # Handle messages - could be list or dict
            messages = data.pop('message', [])
            if not isinstance(messages, list):
                messages = [messages] if messages else []
            
            # Filter out invalid columns
            valid_log_fields    =   {
                                        'account_id', 'date_created', 'account_status', 'cost_status', 
                                        'service_status', 'security_status', 'config_status', 
                                        'inventory_status', 'marketplace_status', 'trusted_advisor_status',
                                        'health_status', 'application_status', 'resilience_hub_status',                        
                                    }
            #'compute_optimizer_status', 'service_resources_status'
            
            # Filter data to only include valid fields
            filtered_data               = {k: v for k, v in data.items() if k in valid_log_fields}
            filtered_data['account_id'] = self.curr_acct['id']
            
            # Ensure date_created exists
            if 'date_created' not in filtered_data:
                filtered_data['date_created'] = datetime.now(timezone.utc)
            
            result = self.db.upsert('logs', filtered_data, ['account_id', 'date_created'], self.stats)
            
            # Load messages (children)
            if messages and result in ['created', 'updated']:
                db_log = self.db.select_one(
                    "SELECT id FROM logs WHERE account_id = :account_id ORDER BY date_created DESC LIMIT 1",
                    {'account_id': self.curr_acct['id']}
                )
                
                if db_log:
                    for message_item in messages:
                        if isinstance(message_item, dict):
                            # Handle dict format: {'type': 'message'}
                            for message_type, message_text in message_item.items():
                                message_data    =   {
                                                        'log_id': db_log['id'],
                                                        'message': str(message_text),
                                                        'message_type': message_type
                                                    }
                                self.db.upsert('log_messages', message_data, ['log_id', 'message_type'], self.stats)
                        else:
                            # Handle string format
                            message_data    =   {
                                                    'log_id': db_log['id'],
                                                    'message': str(message_item),
                                                    'message_type': 'INFO'
                                                }
                            self.db.upsert('log_messages', message_data, ['log_id', 'message_type'], self.stats)
                
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.LOGS)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.LOGS, msg=str(e))
            print(f"{ERROR} Logs load error: {e}")
            return False

    def process_file_data(self, data: Dict, file_name: str) -> Dict:
        """Process and load all data from file with parallel loading"""
        self.stats['TOTAL'] += 1
        
        if not self.validate_data_structure(data):
            print(f"{FAIL} Invalid data structure in {file_name}")
            self.stats['SKIPPED'] += 1
            return self.stats

        # Phase 1: Load account first (required for self.curr_acct)
        if data.get('account'):
            self.load_account_data(data['account'])
        
        # Phase 2: Load all other data in parallel
        loaders = {
            'config'            : self.load_config_data,
            'service'           : self.load_service_data,
            'cost'              : self.load_cost_data,
            'security'          : self.load_security_data,
            'inventory'         : self.load_inventory_data,
            'marketplace'       : self.load_marketplace_data,
            'trusted_advisor'   : self.load_trusted_advisor_data,
            'health'            : self.load_health_data,
            'application'       : self.load_application_data,
            'resilience_hub'    : self.load_resilience_hub_data,
            'service_resources' : self.load_service_resources_data,
            'compute_optimizer' : self.load_compute_optimizer_data,
            'ri_sp_savings'     : self.load_ri_sp_savings_data,
            'config_inventory'  : self.load_config_inventory_data,
            'ai_inventory'      : self.load_ai_inventory_data,
            'support_tickets'   : self.load_support_tickets_data,
            'logs'              : self.load_logs_data
        }
        
        # Per-loader timing when DEBUG is on. The pool's overall duration equals the slowest
        # loader's time, so a hidden bottleneck in one function silently caps the whole run.
        # Wrapping in _wrap when DEBUG is off is a no-op that returns fn unchanged
        import time as _t
        def _wrap(name, fn):
            if not DEBUG:
                return fn
            def _inner(arg):
                _start = _t.time()
                try:
                    return fn(arg)
                finally:
                    print(f"{TIMING} loader {name}: {round(_t.time() - _start, 2)}s")
            return _inner

        # Loaders whose resolve-close step must run even on an empty payload.
        # data.get(attr) is falsy for an empty list, which would skip the loader
        # entirely - but for ai_inventory an empty [] is a meaningful signal that
        # every previously-active resource should flip to INACTIVE. The key must
        # exist in `data` for its .get() to differ from a truly missing key
        _run_when_empty = {'ai_inventory'}

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {
                executor.submit(_wrap(attr, loader), data.get(attr, [])): attr
                for attr, loader in loaders.items()
                if data.get(attr) or (attr in _run_when_empty and attr in data)
            }

            for future in as_completed(futures):
                attr = futures[future]
                try:
                    future.result()
                except Exception as e:
                    #print(f"{ERROR} Error loading {attr}: {e}")
                    print(f"{ERROR}: {e}")
                    continue

        self.stats['LOADED'] += 1
        return self.stats

""" 5. Managing the Data Load Status """
def process_data_status(status):
    status_arr = [0, 0, 0, 0, 0]
    
    if(len(status) > 0):
        status_arr = [
            status['CREATED'],
            status['UPDATED'],
            status['SKIPPED'],
            status['TOTAL'],
            status['LOADED'],
        ]
    
    loaded      = f"{SUCCESS} Loaded: {status_arr[4]} Records"
    not_loaded  = f"{ERROR} Not Loaded: {status_arr[3] - status_arr[4]} Records"
    total       = f"{SUCCESS} Total Processed: {status_arr[3]} Records"

    created     = f"{SUCCESS} Created: {status_arr[0]} Records"
    updated     = f"{FAIL} Updated: {status_arr[1]} Records"
    skipped     = f"{ERROR} Skipped: {status_arr[2]} Records"

    return [total, loaded, not_loaded]

def load_data():
    load_time_start = time.time()
    
    core_s3 = S3Manager(BUCKET or '')
    file_arr= core_s3.list_files(prefix="data/")
    
    core_db = CoreManager()
    #0. checking files to be loaded
    
    result = {}
    try:
        if(len(file_arr) > 0):
            print(f"{INFO} Starting to Load {len(file_arr)} dataset(s)")
            #1. load data
            for file in file_arr:
                name, path = file["file_name"], file["file_path"]
                try:
                    step_start = time.time()
                    print(f"{INFO} Processing {path}", end='', flush=True)
                    data    = core_s3.read_file(file_path=path)
                    if isinstance(data, str):
                        data = json.loads(data)
                    try:
                        result      = core_db.process_file_data(data=data, file_name=name)
                        core_s3.delete_files(file_path=path)
                        step_finish = round(time.time() - step_start, 2)
                        account_id  = core_db.curr_acct['account_id'] if core_db.curr_acct else 'Unknown'
                        print(f"\r{SUCCESS} {account_id}/{REGION}/{name} Data Loaded & File moved to loaded/ folder in {step_finish}s")
                        
                    except Exception as e:
                        print(f"\r{FAIL} Error loading file {name}: {str(e)}")        
                        continue
                except Exception as e:
                    print(f"\r{FAIL} Error reading file {name}: {str(e)}")
                    continue
            load_time_finish            = round(time.time() - load_time_start, 2)
            result['load_time_finish']  = load_time_finish
            return result
        else:
            raise Exception("No files to load")
        
    except Exception as e:
        print(e)
        return result

""" 7. Testing Function, Used to test the script without fetching data from S3 instead uses the sample.json  """

def testing():
    load_time_start = time.time()
    core_db         = CoreManager()
    data_file       = "examples/data.json"

    try:
        step_start = time.time()

        with open(data_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        data = json.loads(file_content)
        if isinstance(data, str):
            data = json.loads(data)

        result = core_db.process_file_data(data=data, file_name=data_file)

        step_finish = round(time.time() - step_start, 2)
        print(f"{SUCCESS} Data Loaded & File moved to loaded/ folder in {step_finish}s")
        
        load_time_finish            = round(time.time() - load_time_start, 2)
        result['load_time_finish']  = load_time_finish
        return result
    
    except FileNotFoundError:
        print(f"{FAIL} {data_file} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"{FAIL} JSON decode error: {e}")
        return {}
    except Exception as e:
        print(f"{FAIL} Error processing {data_file}: {e}")
        return {}

""" 8. MAIN LAMBDA METHOD : This method getsd invoked from the Lambda function """
def lambda_handler(event=None, context=None):
    aws_permission  = AWSBoto3Permissions()
    if context is not None and context == "test":
        print("*"*15, "TESTING", "*"*15)
        print("\n")
    temp = True
    if aws_permission.test():
        print("*"*15,"Connected","*"*15)
        
        if context is not None and context == "test":
            data    = testing()
        else:
            data    = load_data()

        if not data:
            print(f"{INFO} No files to load")
            return True
        
        status  = process_data_status(data)
        
        #testing()
        print(f"{INFO} Finished Loading")
        print("*"*15,"Summary","*"*15) 
        print(status[0])
        print(status[1])
        print(status[2])
        if 'load_time_finish' in data:
            print(f"{TIMING}  Time Taken: {data['load_time_finish']} seconds")
        print("*"*15,"Disconnected","*"*15)
        return True
    else:
        print("*"*15, "Not Connected", "*"*15)
        return False
    
""" 9. You can either use this for Local testing. This is the commadn that woudl also run on the EC2 configuration of the application"""
if __name__ == "__main__":
    
    """ Use the below to use test data """
    #temp = lambda_handler(context="test")

    """ Use the below to use for production """
    temp = lambda_handler()
    