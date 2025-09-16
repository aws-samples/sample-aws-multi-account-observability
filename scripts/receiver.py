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
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from functools import lru_cache
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import re
import time

""" Setting up Logging """
import logging



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
REGION      = os.environ.get("REGION")
BUCKET      = os.environ.get("BUCKET")
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
                                                            'last_changed_date'
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
                                                            'prediction_interval_upper_bound'
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
        # Get current date and 30 days ago for CE
        self.end_date 		= datetime.now()
        self.start_date 	= self.end_date - timedelta(days=30)
        self.aws_services 	= {
                                    'sts'                : {
                                                            'name'      : 'STS',
                                                            'client'    : boto3.client('sts'),
                                                            'action'    : 'get_caller_identity',
                                                            'params'    : params,
                                                            'status'    : False,
                                                        },
                                    'account'            : {
                                                            'name'      : 'Account',
                                                            'client'    : boto3.client('account'),
                                                            'action'    : 'get_contact_information',
                                                            'params'    : params,
                                                            'status'    : False
                                                        },
                                    'rds-data'           : {
                                                            'name'      : 'Aurora RDS',
                                                            'client'    : boto3.client('rds-data', region_name=REGION),
                                                            'action'    : 'close',
                                                            'params'    : params
                                                        },
                                    's3'                : {
                                                            'name'      : 's3',
                                                            'client'    : boto3.client('s3', region_name=REGION),
                                                            'action'    : 'close',
                                                            'params'    : params
                                                        }
                                }

    def _check(self, service):
        try:
            if service["params"]:
                service["client"].__getattribute__(service["action"])(
                    **service["params"]
                )
            else:
                service["client"].__getattribute__(service["action"])()
            service["status"] = True
            print(f"{SUCCESS} Connected to {service['name']}")
        except ClientError as e:
            print(f"{FAIL} Not Connected to {service['name']}: {str(e)}")
            service["status"] = False
        except Exception as e:
            print(f"{ERROR} Error testing {service['name']}: {str(e)}")
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
    COMPUTE_OPTIMIZER   = "Compute Optimnizer"
    SERVICE_RESOURCES   = "Service Resources"
    CONFIG_INVENTORY    = "Config Inventory"
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
            self.move_to_processed(file_path)
        except Exception as e:
            print(f"{ERROR} Failed to delete {file_path}: {e}")
            return False

""" 3. DB MANAGER : Wrapper class that manages the database interactions. Insert, Update, Select Queries """
class DBManager:
    __slots__ = ('database', 'client', 'cluster_arn', 'secret_arn', '_base_params')
    
    def __init__(self, database_name: str, cluster_arn: str = None, secret_arn: str = None):
        self.database       = database_name
        self.client         = boto3.client('rds-data', region_name=REGION)
        self.cluster_arn    = cluster_arn or os.environ['AURORA_CLUSTER_ARN']
        self.secret_arn     = secret_arn or os.environ['AURORA_SECRET_ARN']
        
        # Pre-compute base parameters
        self._base_params = {
            'resourceArn': self.cluster_arn,
            'secretArn': self.secret_arn,
            'database': self.database
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
        
        return bool(re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', identifier))
        

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
        
        return results[0] if single and results else results

    def execute_statement(self, sql: str, params: Optional[Dict] = None) -> Dict:
        """Optimized execution"""
        exec_params = self._base_params.copy()
        exec_params['sql'] = sql
        
        if params:
            exec_params['parameters'] = self._format_parameters(params)
        
        return self.client.execute_statement(**exec_params)

    def select(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Fast select multiple"""
        try:
            response = self.execute_statement(query, params)
            columns = self._extract_columns(query)
            return self._format_results(response, columns)
        except Exception as e:
            print(f"{ERROR} Select error: {e}")
            return []

    def select_one(self, query: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Fast select single"""
        try:
            response = self.execute_statement(query, params)
            columns = self._extract_columns(query)
            return self._format_results(response, columns, single=True)
        except Exception as e:
            print(f"{ERROR} Select one error: {e}")
            return None

    # Update & Insert = Upsert, this is used to update or insert into the Database
    def upsert(self, table: str, data: Dict, unique_keys: Union[str, List[str]], stats: Dict = None) -> str:
        """Generic upsert method with type casting and flexible updated_at"""
        try:
            if not self._validate_sql_identifier(table):
                raise ValueError(f"Invalid table name: {table}")
            
            if isinstance(unique_keys, str):
                unique_keys = [unique_keys]
            
            for key in unique_keys + list(data.keys()):
                if not self._validate_sql_identifier(key):
                    raise ValueError(f"Invalid column name: {key}")
            
            where_conditions = []
            where_params = {}
            
            for key in unique_keys:
                if key in data:
                    pg_type = self._get_postgres_type(key, AWS_TYPECAST_2)
                    if pg_type:
                        where_conditions.append(f"{key} = :{key}::{pg_type}")
                    else:
                        where_conditions.append(f"{key} = :{key}")
                    where_params[key] = data[key]
            
            if not where_conditions:
                return 'error'
            
            where_clause = ' AND '.join(where_conditions)
            
            # Check if record exists
            existing = self.select_one(f"SELECT id FROM {table} WHERE {where_clause}", where_params) # nosec B608
            
            if existing:
                # Update existing - build typed SET clause
                update_fields = []
                for k in data.keys():
                    if k not in ['id', 'created_at']:
                        pg_type = self._get_postgres_type(k, AWS_TYPECAST_2)
                        if pg_type:
                            update_fields.append(f"{k} = :{k}::{pg_type}")
                        else:
                            update_fields.append(f"{k} = :{k}")
                
                if update_fields:
                    # Only add updated_at if table has it (check by trying to describe table)
                    update_query = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {where_clause}" # nosec B608
                    self.execute_statement(update_query, {**data, **where_params})
                    if stats: stats['UPDATED'] += 1
                    return 'updated'
                else:
                    if stats: stats['SKIPPED'] += 1
                    return 'skipped'
            else:
                # Insert new - build typed INSERT
                cols = list(data.keys())
                placeholders = []
                for col in cols:
                    pg_type = self._get_postgres_type(col, AWS_TYPECAST_2)
                    if pg_type:
                        placeholders.append(f":{col}::{pg_type}")
                    else:
                        placeholders.append(f":{col}")
                
                query = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(placeholders)})"# nosec B608
                result = self.execute_statement(query, data)
                
                if result:
                    if stats: stats['CREATED'] += 1
                    return 'created'
                else:
                    if stats: stats['SKIPPED'] += 1
                    return 'error'
                    
        except Exception as e:
            print(f"{ERROR} Upsert error for {table}: {e}")
            if stats: stats['SKIPPED'] += 1
            return 'error'

###END: HELPER CLASSES###

""" 4. CORE MANAGER : Manages the Data Loadign from the JSON File to Aurora Postgres """
class CoreManager:
    def __init__(self):
        self.sts_client = boto3.client('sts')
        self.db         = DBManager(database_name=DB_NAME, cluster_arn=ARN_AURORA, secret_arn=ARN_SECRET)
        self.stats      = {'CREATED': 0, 'UPDATED': 0, 'SKIPPED': 0, 'TOTAL': 0, 'LOADED': 0}
        self.curr_acct  = None  

    def set_log(self, log_type:AWSLogType, topic:AWSResourceType, msg=None):
        message = msg if msg is not None else "Data Loaded"
        if log_type == "WARN":
            print(f"{FAIL} {self.curr_acct['account_id']}/{topic.value} : {message}")
        elif log_type == "ERROR":
            print(f"{ERROR} {self.curr_acct['account_id']}/{topic.value} Error : {message}")
        #else:
        #    print(f"{SUCCESS} {self.curr_acct['account_id']}/{topic.value} : {message}")

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
            'account_name': 'Unknown',
            'account_email': 'unknown@example.com',
            'account_status': 'ACTIVE',
            'account_arn': f"arn:aws:organizations::{account_id}:account",
            'joined_method': 'CREATED',
            'csp': 'AWS',
            'account_type': 'PRODUCTION',
            'joined_timestamp': '1970-01-01T00:00:00Z'
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
                    if k not in ['contact_info', 'alternate_contacts']:
                        account_data[k]                 = v if v is not None else self._get_default_account(k, data.get('account_id'))
                        account_data["csp"]             = self._get_default_account("csp", "AWS")
                        account_data["account_type"]    = self._get_default_account("account_type", "PRODUCTION")
                
                # Handle partner_name and customer_name specifically
                account_data["partner_name"] = data.get('partner_name', 'None')
                account_data["customer_name"] = data.get('customer_name', 'None')

                # Upsert account
                result = self.db.upsert('accounts', account_data, 'account_id', self.stats)
                
                # Get current account for other operations
                if result in ['created', 'updated']:
                    self.curr_acct = self.db.select_one(
                        "SELECT id, account_id FROM accounts WHERE account_id = :account_id",
                        {'account_id': data['account_id']}
                    )
            
            # Process contact info (child)
            contact = data.get('contact_info', {})
            if contact and any(v is not None for v in contact.values()):
                contact['account_id'] = data['account_id']
                self.db.upsert('contact_info', contact, 'account_id', self.stats)
            
            # Process alternate contacts (children)
            alt_contacts = data.get('alternate_contacts', {})
            if alt_contacts:
                for contact_type, contact_data in alt_contacts.items():
                    if contact_data:
                        contact_record = {
                            'account_id'    : data['account_id'],
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
    def load_config_data(self, data: Dict) -> bool:
        """Load config data with parent-child upsert like inventory"""
        try:
            if not self.curr_acct:
                print(f"{ERROR} No account loaded")
                return False
            
            config_map = {}  # Map config_report_id
            non_compliant = data.pop('non_compliant_resources', [])
            
            # Load config report first (parent)
            data['account_id'] = self.curr_acct['id']
            result = self.db.upsert('config_reports', data, ['account_id', 'date_from'], self.stats)
            
            # Get config_report_id for resources - FIX: Add ::date casting
            if result in ['created', 'updated']:
                db_config = self.db.select_one(
                    "SELECT id FROM config_reports WHERE account_id = :account_id AND date_from = :date_from::date",
                    {'account_id': self.curr_acct['id'], 'date_from': data['date_from']}
                )
                if db_config:
                    config_map['config_report_id'] = db_config['id']
            
            # Load non-compliant resources (children)
            if non_compliant and config_map:
                config_report_id = config_map['config_report_id']
                
                for resource in non_compliant:
                    resource.pop('annotation', None)
                    resource.pop('config_rule_invoked_time', None)
                    resource['created_at'] = resource.pop('error_date', None)

                    resource['config_report_id'] = config_report_id
                    self.db.upsert('non_compliant_resources', resource, ['config_report_id', 'resource_id'], self.stats)

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
                for service in data:
                    # Filter to only schema fields
                    filtered_service = {k: v for k, v in service.items() if k in service_fields}
                    filtered_service['account_id'] = self.curr_acct['id']
                    
                    # Convert usage_types array to comma-separated string
                    if 'usage_types' in filtered_service and isinstance(filtered_service['usage_types'], list):
                        filtered_service['usage_types'] = ','.join(filtered_service['usage_types'])
                    
                    # Upsert using composite unique key
                    self.db.upsert('services', filtered_service, ['account_id', 'service', 'date_from'], self.stats)

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
            cost_report = {
                **data,
                'account_id': self.curr_acct['id'],
                'period_start': period.get('start'),
                'period_end': period.get('end'),
                'period_granularity': period.get('granularity')
            }
            
            result = self.db.upsert('cost_reports', cost_report, ['account_id', 'period_start'], self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Cost Reports Loaded")

            # Get cost_report_id for children
            if result in ['created', 'updated']:
                db_cost = self.db.select_one(
                    "SELECT id FROM cost_reports WHERE account_id = :account_id AND period_start = :period_start::date",
                    {'account_id': self.curr_acct['id'], 'period_start': cost_report['period_start']}
                )
                if db_cost:
                    cost_map['cost_report_id'] = db_cost['id']
            
            # Load service costs (children)
            if top_services and cost_map:
                cost_report_id = cost_map['cost_report_id']
                
                for service in top_services:
                    service_data = {
                        'cost_report_id': cost_report_id,
                        'service_name': service['service'],
                        'cost': service['cost']
                    }
                    self.db.upsert('service_costs', service_data, ['cost_report_id', 'service_name'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Service Cost Loaded")

            # Load forecasts (children)
            if forecasts and cost_map:
                cost_report_id = cost_map['cost_report_id']
                
                for forecast in forecasts:
                    forecast_data = {
                        'cost_report_id': cost_report_id,
                        'period_start': forecast['period']['start'],
                        'period_end': forecast['period']['end'],
                        'amount': forecast['amount']
                    }
                    self.db.upsert('cost_forecasts', forecast_data, ['cost_report_id', 'period_start'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.COST, msg="Cost Forecast Loaded")

            
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.COST, msg=e)
            
            return False
    #Method: UPSERT
    def load_security_data(self, data: Dict) -> bool:
        """Load comprehensive security data with blazing fast upserts"""
        try:
            # Define schema fields for each security service
            guard_duty_fields = {
                'account_id', 'detector_id', 'finding_type', 'severity', 
                'title', 'description', 'confidence', 'region'
            }
            
            kms_fields = {
                'account_id', 'key_id', 'arn', 'description', 'key_usage', 
                'key_state', 'creation_date', 'enabled', 'key_rotation_enabled'
            }
            
            waf_fields = {
                'account_id', 'name', 'waf_id', 'arn', 'scope', 'description', 
                'default_action', 'rules_count', 'logging_enabled', 
                'geo_blocking_enabled', 'blocked_countries'
            }
            
            waf_rules_detailed_fields = {
                'account_id', 'web_acl_name', 'rule_name', 'priority', 'action',
                'statement_type', 'is_managed_rule', 'is_custom_rule', 'rate_limit',
                'logging_enabled', 'geo_blocking', 'sql_injection', 'sample_request_enabled',
                'cloudwatch_enabled', 'has_xss_protection', 'waf_version', 'is_compliant', 'scope'
            }
            
            cloudtrail_fields = {
                'account_id', 'name', 'arn', 'is_logging', 'is_multi_region', 
                's3_bucket', 'kms_key_id', 'log_file_validation', 'latest_delivery_time'
            }
            
            secrets_fields = {
                'account_id', 'name', 'arn', 'description', 'created_date', 
                'last_changed_date', 'rotation_enabled'
            }
            
            cert_fields = {
                'account_id', 'arn', 'domain_name', 'status', 'type', 'not_after'
            }
            
            inspector_fields = {
                'account_id', 'finding_arn', 'severity', 'status', 'type', 
                'title', 'description', 'first_observed_at'
            }
             
            finding_fields = {
                'security_id', 'finding_id', 'service', 'title', 'description',
                'severity', 'status', 'resource_type', 'resource_id', 'created_at',
                'updated_at', 'recommendation', 'compliance_status', 'region',
                'workflow_state', 'record_state', 'product_name', 'company_name',
                'product_arn', 'generator_id', 'generator'
            }
            
            security_map = {}  # Load Security Hub summaries first (parent), Map service to security_id Map service to security_id

            # Load Security Hub summaries first (parent)
            if 'security_hub' in data:
                for security_service in data['security_hub']:
                    # Extract severity counts
                    severity_counts = security_service.get('severity_counts', {})
                    
                    # Build security summary record directly
                    filtered_security = {
                        'account_id': self.curr_acct['id'],
                        'service': security_service.get('service'),
                        'total_findings': security_service.get('total_findings', 0),
                        'critical_count': severity_counts.get('CRITICAL', 0),
                        'high_count': severity_counts.get('HIGH', 0),
                        'medium_count': severity_counts.get('MEDIUM', 0),
                        'low_count': severity_counts.get('LOW', 0),
                        'informational_count': severity_counts.get('INFORMATIONAL', 0),
                        'open_findings': security_service.get('open_findings', 0),
                        'resolved_findings': security_service.get('resolved_findings', 0)
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
            # Load findings (children)
            if 'security_hub' in data and security_map:
                for security_service in data['security_hub']:
                    service_name = security_service.get('service')
                    if service_name in security_map and 'findings' in security_service:
                        security_id = security_map[service_name]
                        
                        for finding in security_service['findings']:
                            filtered_finding = {k: v for k, v in finding.items() if k in finding_fields}
                            filtered_finding['security_id'] = security_id
                            
                            self.db.upsert('findings', filtered_finding, 'finding_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Secrity Hub Findings Loaded")
            # Load GuardDuty findings
            if 'guard_duty' in data:
                for finding in data['guard_duty']:
                    filtered_finding = {k: v for k, v in finding.items() if k in guard_duty_fields}
                    filtered_finding['account_id'] = self.curr_acct['id']
                    filtered_finding['detector_id'] = finding.get('id')  # Map 'id' to 'detector_id'
                    filtered_finding['finding_type'] = finding.get('type')  # Map 'type' to 'finding_type'
                    
                    self.db.upsert('guard_duty_findings', filtered_finding, ['account_id', 'detector_id'], self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Guard Duty Loaded")
            # Load KMS keys
            if 'kms' in data:
                for key in data['kms']:
                    filtered_key = {k: v for k, v in key.items() if k in kms_fields}
                    filtered_key['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('kms_keys', filtered_key, 'key_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="KMS Loaded")
            # Load WAF rules
            if 'waf' in data:
                for waf in data['waf']:
                    filtered_waf = {k: v for k, v in waf.items() if k in waf_fields}
                    filtered_waf['account_id'] = self.curr_acct['id']
                    filtered_waf['waf_id'] = waf.get('id')  # Map 'id' to 'waf_id'
                    
                    self.db.upsert('waf_rules', filtered_waf, 'waf_id', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="WAF Loaded")

            # Load WAF rules detailed
            if 'waf_rules' in data:
                for rule in data['waf_rules']:
                    filtered_rule = {k: v for k, v in rule.items() if k in waf_rules_detailed_fields}
                    filtered_rule['account_id'] = self.curr_acct['id']
                    
                    # Convert action dict to JSON string for TEXT field
                    if 'action' in filtered_rule and isinstance(filtered_rule['action'], dict):
                        filtered_rule['action'] = json.dumps(filtered_rule['action'])
                    
                    self.db.upsert('waf_rules_detailed', filtered_rule, ['account_id', 'web_acl_name', 'rule_name'], self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="WAF Rules Detailed Loaded")

            # Load CloudTrail logs
            if 'cloudtrail' in data:
                for trail in data['cloudtrail']:
                    filtered_trail = {k: v for k, v in trail.items() if k in cloudtrail_fields}
                    filtered_trail['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('cloudtrail_logs', filtered_trail, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Cloud Trail Loaded")

            # Load Secrets Manager secrets
            if 'secrets_manager' in data:
                for secret in data['secrets_manager']:
                    filtered_secret = {k: v for k, v in secret.items() if k in secrets_fields}
                    filtered_secret['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('secrets_manager_secrets', filtered_secret, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Secrets Manager Loaded")

            # Load Certificate Manager certificates
            if 'certificate_manager' in data:
                for cert in data['certificate_manager']:
                    filtered_cert = {k: v for k, v in cert.items() if k in cert_fields}
                    filtered_cert['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('certificates', filtered_cert, 'arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Certificate Manager Loaded")
            # Load Inspector findings
            if 'inspector' in data:
                for finding in data['inspector']:
                    filtered_finding = {k: v for k, v in finding.items() if k in inspector_fields}
                    filtered_finding['account_id'] = self.curr_acct['id']
                    
                    self.db.upsert('inspector_findings', filtered_finding, 'finding_arn', self.stats)
            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY, msg="Inspector Loaded")

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.SECURITY)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.COST, msg=e)
            return False
    #Method: UPSERT
    def load_inventory_data(self, data: Dict) -> bool:
        """Load inventory instances, applications, and patches with proper relationships"""
        try:
            instance_map = {}
            
            # Define schema fields
            instance_fields = {
                'account_id', 'instance_id', 'instance_type', 'platform', 
                'ip_address', 'computer_name', 'ping_status', 
                'last_ping_date_time', 'agent_version'
            }
            
            app_fields = {
                'instance_id', 'account_id', 'name', 'version', 'publisher', 'install_time'
            }
            
            patch_fields = {
                'instance_id', 'account_id', 'title', 'classification', 'severity', 
                'state', 'installed_time'
            }
            
            # Load instances first
            if 'instances' in data:
                for instance in data['instances']:
                    filtered_instance = {k: v for k, v in instance.items() if k in instance_fields}
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

            # Load applications
            if 'applications' in data and instance_map:
                first_instance_db_id = next(iter(instance_map.values()))
                
                for app in data['applications']:
                    filtered_app = {k: v for k, v in app.items() if k in app_fields}
                    filtered_app['instance_id'] = first_instance_db_id
                    filtered_app['account_id'] = self.curr_acct['id']  # Add account_id
                    
                    self.db.upsert('inventory_applications', filtered_app, ['instance_id', 'name'], self.stats)
                self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.INVENTORY, msg="Inventory Applications Loaded")

            # Load patches
            if 'patches' in data and instance_map:
                first_instance_db_id = next(iter(instance_map.values()))
                
                for patch in data['patches']:
                    filtered_patch = {k: v for k, v in patch.items() if k in patch_fields}
                    filtered_patch['instance_id'] = first_instance_db_id
                    filtered_patch['account_id'] = self.curr_acct['id']  # Add account_id
                    
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
            
            if isinstance(data, list):
                for item in data:
                    # Filter to only schema fields
                    filtered_item = {k: v for k, v in item.items() if k in marketplace_fields}
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
            advisor_fields = {
                'account_id', 'check_name', 'category', 'severity', 
                'recommendation', 'affected_resources_count', 
                'potential_savings', 'timestamp'
            }
            
            if isinstance(data, list):
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
            health_fields = {
                'account_id', 'arn', 'service', 'event_type_code', 
                'region', 'start_time', 'end_time', 'status_code'
            }
            
            if isinstance(data, list):
                for event in data:
                    # Filter to only schema fields
                    filtered_event = {k: v for k, v in event.items() if k in health_fields}
                    filtered_event['account_id'] = self.curr_acct['id']
                    
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
            app_fields = {
                'account_id', 'service_name', 'namespace', 'key_attributes'
            }
            
            if isinstance(data, list):
                for signal in data:
                    # Filter to only schema fields
                    filtered_signal = {k: v for k, v in signal.items() if k in app_fields}
                    filtered_signal['account_id'] = self.curr_acct['id']
                    
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
            resilience_fields = {
                'account_id', 'app_arn', 'name', 'description', 'creation_time',
                'last_assessment_time', 'compliance_status', 'resiliency_score', 
                'status', 'rpo', 'rto', 'last_drill', 'cost'
            }
            
            if isinstance(data, list):
                for app in data:
                    # Filter to only schema fields
                    filtered_app = {k: v for k, v in app.items() if k in resilience_fields}
                    filtered_app['account_id'] = self.curr_acct['id']
                    
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
            resource_fields = {
                'account_id', 'service_name', 'resource_type', 'resource_id', 'resource_name',
                'region', 'availability_zone', 'state', 'instance_type', 'vpc_id', 'engine',
                'instance_class', 'multi_az', 'size_gb', 'volume_type', 'creation_date',
                'type', 'scheme', 'instance_count', 'min_size', 'max_size', 'available_ip_count'
            }
            
            if isinstance(data, list):
                for resource in data:
                    # Filter to only schema fields
                    filtered_resource = {k: v for k, v in resource.items() if k in resource_fields}
                    filtered_resource['account_id'] = self.curr_acct['id']
                    
                    # Upsert using composite unique key (account_id + resource_id)
                    self.db.upsert('service_resources', filtered_resource, ['account_id', 'resource_id'], self.stats)

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
            optimizer_fields = {
                'account_id', 'resource_type', 'resource_arn', 'resource_name', 'finding',
                'current_instance_type', 'current_memory_size', 'current_volume_type', 'current_volume_size',
                'recommended_instance_type', 'recommended_memory_size', 'recommended_volume_type', 'recommended_volume_size',
                'savings_opportunity_percentage', 'estimated_monthly_savings_usd', 'performance_risk',
                'cpu_utilization_max', 'memory_utilization_avg', 'migration_effort'
            }
            
            if isinstance(data, list):
                for recommendation in data:
                    # Filter to only schema fields
                    filtered_rec = {k: v for k, v in recommendation.items() if k in optimizer_fields}
                    filtered_rec['account_id'] = self.curr_acct['id']
                    
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
            inventory_fields = {
                'account_id', 'resource_type', 'resource_subtype', 'resource_id', 'resource_name', 'region',
                'availability_zone', 'state', 'instance_type', 'vpc_id', 'engine',
                'instance_class', 'multi_az', 'size_gb', 'volume_type', 'creation_date',
                'type', 'scheme', 'instance_count', 'min_size', 'max_size', 'available_ip_count'
            }

            if isinstance(data, list):
                for inventory in data:
                    # Filter to only schema fields
                    filtered_inventory = {k: v for k, v in inventory.items() if k in inventory_fields}
                    filtered_inventory['account_id'] = self.curr_acct['id']

                    # Upsert using composite unique key (account_id + resource_id)
                    self.db.upsert('config_inventory', filtered_inventory, ['account_id', 'resource_id'], self.stats)

            self.set_log(log_type=AWSLogType.SUCCESS, topic=AWSResourceType.CONFIG_INVENTORY)
            return True
        except Exception as e:
            self.set_log(log_type=AWSLogType.ERROR, topic=AWSResourceType.CONFIG_INVENTORY, msg=e)
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
            valid_log_fields = {
                'account_id', 'date_created', 'account_status', 'cost_status', 
                'service_status', 'security_status', 'config_status', 
                'inventory_status', 'marketplace_status', 'trusted_advisor_status',
                'health_status', 'application_status', 'resilience_hub_status',
                
            }
            #'compute_optimizer_status', 'service_resources_status'
            
            # Filter data to only include valid fields
            filtered_data = {k: v for k, v in data.items() if k in valid_log_fields}
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
                                message_data = {
                                    'log_id': db_log['id'],
                                    'message': str(message_text),
                                    'message_type': message_type
                                }
                                self.db.upsert('log_messages', message_data, ['log_id', 'message_type'], self.stats)
                        else:
                            # Handle string format
                            message_data = {
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


    def process_file_data(self, data: Dict, file_name: str) -> None:
        """Process and load all data from file"""
        self.stats['TOTAL'] += 1
        
        if not self.validate_data_structure(data):
            print(f"{FAIL} Invalid data structure in {file_name}")
            self.stats['SKIPPED'] += 1
            return

        loaders = {
            'account'           : self.load_account_data,
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
            'config_inventory'  : self.load_config_inventory_data,
            'logs'              : self.load_logs_data
        }
        
        for attr, loader in loaders.items():
            if data.get(attr):
                loader(data[attr])
        
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

""" 6. Loads the data """
def load_data():
    load_time_start = time.time()
    
    core_s3 = S3Manager(BUCKET)
    file_arr= core_s3.list_files(prefix="data/")
    
    core_db = CoreManager()
    #0. checking files to be loaded
    
    result = []
    try:
        if(len(file_arr) > 0):
            print(f"{INFO} Starting to Load {len(file_arr)} dataset(s)")
            #1. load data
            for file in file_arr:
                name, path = file["file_name"], file["file_path"]
                try:
                    step_start = time.time()
                    
                    data    = core_s3.read_file(file_path=path)
                    if isinstance(data, str):
                        data = json.loads(data)
                    try:
                        result  = core_db.process_file_data(data=data, file_name=name)
                        core_s3.delete_files(file_path=path)
                        step_finish = round(time.time() - step_start, 2)
                        print(f"{SUCCESS} {core_db.curr_acct['account_id']}/{name} Data Loaded & File moved to loaded/ folder in {step_finish}s")
                        
                    except Exception as e:
                        print(f"{FAIL} Error loading file {name}: {str(e)}")        
                        continue
                except Exception as e:
                    print(f"{FAIL} Error reading file {name}: {str(e)}")
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
    core_db = CoreManager()
    try:
        with open('data/2025-09-15_DAILY.json', 'r', encoding='utf-8') as f:
            file_content = f.read()
        print(f"*File Read")    
        data = json.loads(file_content)
        print(f"*Ready to load sample dataset")
        result = core_db.process_file_data(data=data, file_name="data/2025-07-17_MONTHLY.json")

        
    except FileNotFoundError:
        print(f"{FAIL} sample.json not found")
    except json.JSONDecodeError as e:
        print(f"{FAIL} JSON decode error: {e}")
    except Exception as e:
        print(f"{FAIL} Error processing sample.json: {e}")

""" 8. MAIN LAMBDA METHOD : This method getsd invoked from the Lambda function """
def lambda_handler(event=None, context=None):
    aws_permission  = AWSBoto3Permissions()

    if aws_permission.test():
        print("*"*15,"Connected","*"*15)
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
        print(f"{TIMING}  Time Taken: {data['load_time_finish']}")
        print("*"*15,"Disconnected","*"*15)
        return True
    else:
        print("*"*15, "Not Connected", "*"*15)
        return False
    
""" 9. This is only for development testing, Runs on your local machine """
if __name__ == "__main__":
    #testing()
    temp = lambda_handler()
    