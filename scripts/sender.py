"""ONLY FOR DEVELOPMENT REMOVE ON LAMBDA"""
""" from dotenv import load_dotenv, dotenv_values
load_dotenv() """

""" IMPORTS """
import sys
import boto3
import json
import os
import calendar
import time
import random

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime, timedelta, timezone

from calendar import monthrange
from enum import Enum

from concurrent.futures import ThreadPoolExecutor, as_completed


""" GLOBAL VARIABLES """
REGION      = os.environ.get("REGION", "us-east-1") #boto3.client('sts').meta.region_name
BUCKET      = os.environ.get("BUCKET")
KMS_KEY_ID  = os.environ.get("ANALYTICS_KMS_KEY")
CUSTOMER    = os.environ.get("CUSTOMER", None)
PARTNER     = os.environ.get("PARTNER", None)
CATEGORY    = os.environ.get("CATEGORY", None)
ENVIRONMENT = os.environ.get("ENVIRONMENT", None)
PRODUCT     = os.environ.get("PRODUCT", None)

SUCCESS     = "🟢"  
FAIL        = "🟡"  
ERROR       = "🔴"  
INFO        = "🔵"  
TIMING      = "⏱️ "
CALENDAR    = "📅"

""" HELPER CLASSES """
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def upload_to_s3(account, data, interval, end_date):

    end_date    = datetime.now(timezone.utc) if not end_date else end_date
    s3          = boto3.client('s3')
    timestamp   = end_date.strftime("%H%M%S")
    filename    = f'data/{account}/{REGION}/{end_date.year}-{end_date.month:02d}-{end_date.day:02d}_{interval}.json'
    
    try:
        # Check if data is None and handle it
        if data is None:
            print("Warning: Data is None, creating empty JSON object")
            data = {"warning": "No data collected", "timestamp": datetime.now(timezone.utc).isoformat()}
        
        # Convert data to JSON string with datetime handling
        json_data = json.dumps(data, indent=4, cls=DateTimeEncoder)
        
        # Calculate file size
        file_size_bytes = len(json_data.encode('utf-8'))
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        # Upload to S3 with KMS encryption
        put_params = {'Bucket': BUCKET, 'Key': filename, 'Body': json_data}

        if KMS_KEY_ID:
            put_params['ServerSideEncryption'] = 'aws:kms'
            put_params['SSEKMSKeyId'] = KMS_KEY_ID

        s3.put_object(**put_params)
        
        result = {
            "path": f"s3://{BUCKET}/{filename}",
            "date_added": str(end_date.date()),
            "account": account,
            "size": f"{file_size_mb} MB"
        }
        
        return result
    
    except Exception as e:
        print(f"\n✗ Error writing to S3: {str(e)}")
        return {
            "path"      : None,
            "date_added": str(end_date.date()) if end_date else None,
            "account"   : account,
            "error"     : str(e)
        }

"""  1. AWS RESPONSE MANAGER """
# a. AWS Resource Data - To ensure the data format is strictly governed
@dataclass
class AWSResourceData:
    """Data structure for AWS resource information"""
    account			    : Dict[str, Any]        = field(default_factory=dict)
    config			    : List[Dict[str, Any]]  = field(default_factory=list)
    service			    : List[Dict[str, Any]]  = field(default_factory=list)
    cost			    : List[Dict[str, Any]]  = field(default_factory=list)
    security		    : List[Dict[str, Any]]  = field(default_factory=list)
    inventory		    : List[Dict[str, Any]]  = field(default_factory=list)
    marketplace		    : List[Dict[str, Any]]  = field(default_factory=list)
    trusted_advisor	    : List[Dict[str, Any]]  = field(default_factory=list)
    health			    : List[Dict[str, Any]]  = field(default_factory=list)
    application		    : List[Dict[str, Any]]  = field(default_factory=list)
    resilience_hub	    : List[Dict[str, Any]]  = field(default_factory=list)
    compute_optimizer	: List[Dict[str, Any]]  = field(default_factory=list)
    ri_sp_savings       : List[Dict[str, Any]]  = field(default_factory=list)
    service_resources	: List[Dict[str, Any]]  = field(default_factory=list)
    config_inventory	: List[Dict[str, Any]]  = field(default_factory=list)
    support_tickets	    : List[Dict[str, Any]]  = field(default_factory=list)
    logs			    : Dict[str, Any]        = field(default_factory=dict)

class AWSResourceType(str, Enum):
    ACCOUNT             = "account"
    CONFIG              = "config"
    SERVICE             = "service"
    COST                = "cost"
    SECURITY            = "security"
    INVENTORY           = "inventory"
    MARKETPLACE         = "marketplace"
    TRUSTED_ADVISOR     = "trusted_advisor"
    HEALTH              = "health"
    APPLICATION         = "application"
    RESILIENCE_HUB      = "resilience_hub"
    COMPUTE_OPTIMIZER   = "compute_optimizer"
    RI_SP_SAVINGS       = "ri_sp_savings"
    CONFIG_INVENTORY    = "config_inventory"
    SERVICE_RESOURCES   = "service_resources"
    SUPPORT_TICKETS     = "support_tickets"
    LOGS                = "logs"

# b. AWS Resource Interface - To ensure the data format is strictly governed
class AWSResourceInterface:
    def __init__(self):
        self.data = AWSResourceData()

    def set_data(self, attr: AWSResourceType, data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        current_attr = getattr(self.data, attr.value)
        if isinstance(data, list):
            current_attr.extend(data)
        else:
            setattr(self.data, attr.value, data)

    def get_all_data(self) -> Dict[str, Any]:
        """Get all data in the specified format"""
        result = {
            "account"			: self.data.account,
            "config"			: self.data.config,
            "service"			: self.data.service,
            "cost"				: self.data.cost,
            "security"			: self.data.security,
            "inventory"			: self.data.inventory,
            "marketplace"		: self.data.marketplace,
            "trusted_advisor"	: self.data.trusted_advisor,
            "health"			: self.data.health,
            "application"		: self.data.application,
            "resilience_hub"	: self.data.resilience_hub,
            "service_resources"	: self.data.service_resources,
            "compute_optimizer"	: self.data.compute_optimizer,
            "ri_sp_savings"	    : self.data.ri_sp_savings,
            "config_inventory"	: self.data.config_inventory,
            "support_tickets"	: self.data.support_tickets,
            "logs"				: self.data.logs
        }

        return result

# c. AWS Response Structure
@dataclass
class AWSResponse:
    _raw_response: Dict[str, Any]

    @property
    def request_id(self) -> str:
        return self._raw_response.get("ResponseMetadata", {}).get("RequestId", "")

    @property
    def status(self) -> int:
        return self._raw_response.get("ResponseMetadata", {}).get("HTTPStatusCode", 500)

    @property
    def retry_attempts(self) -> int:
        return self._raw_response.get("ResponseMetadata", {}).get("RetryAttempts", 0)

    @property
    def data(self) -> Dict[str, Any]:
        return {k: v for k, v in self._raw_response.items() if k != "ResponseMetadata"}

""" 2. TEST PERMISSIONS FOR AWS SERVICES """
class AWSBoto3Permissions:
    def __init__(self, params=None):
        self.boto3_config   = Config(connect_timeout=5,read_timeout=10,retries={'max_attempts': 2})
        # Get current date and 30 days ago for CE
        self.end_date 		= datetime.now(timezone.utc)
        self.start_date 	= self.end_date - timedelta(days=30)
        self.aws_services 	= {
            "sts": {
                "name": "STS",
                "client": boto3.client("sts", region_name=REGION, config=self.boto3_config),
                "action": "get_caller_identity",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "account_contact": {
                "name": "Account Contact",
                "client": boto3.client("account", region_name=REGION, config=self.boto3_config),
                "action": "get_contact_information",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "account": {
                "name": "Account",
                "client": boto3.client("account", region_name=REGION, config=self.boto3_config),
                "action": "get_account_information",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "ce": {
                "name": "Cost Explorer",
                "client": boto3.client("ce", config=self.boto3_config),
                "action": "get_cost_and_usage",
                "params": {
                    "TimePeriod": {
                        "Start": self.start_date.strftime("%Y-%m-%d"),
                        "End": self.end_date.strftime("%Y-%m-%d"),
                    },
                    "Granularity": "MONTHLY",
                    "Metrics": ["UnblendedCost"],
                    "Filter": {"Dimensions": {"Key": "USAGE_TYPE", "Values": ["*"]}},
                },
                "status": False,
                "reqd"  : True
            },
            "securityhub": {
                "name": "Security Hub",
                "client": boto3.client("securityhub", region_name=REGION, config=self.boto3_config),
                "action": "describe_hub",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "resiliencehub": {
                "name": "Resilience Hub",
                "client": boto3.client("resiliencehub", region_name=REGION, config=self.boto3_config),
                "action": "list_apps",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "config": {
                "name": "AWS Config",
                "client": boto3.client("config", region_name=REGION, config=self.boto3_config),
                "action": "describe_configuration_recorders",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "iam": {
                "name": "IAM",
                "client": boto3.client("iam", config=self.boto3_config),
                "action": "list_users",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "ec2": {
                "name": "EC2",
                "client": boto3.client("ec2", region_name=REGION, config=self.boto3_config),
                "action": "describe_regions",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "application-signals": {
                "name": "Application Signals",
                "client": boto3.client("application-signals", region_name=REGION, config=self.boto3_config),
                "action": "close",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "ssm": {
                "name": "Systems Manager",
                "client": boto3.client("ssm", region_name=REGION, config=self.boto3_config),
                "action": "describe_instance_information",
                "params": params,
                "status": False,
                "reqd"  : True
            },
            "inspector2": {
                "name": "Inspector",
                "client": boto3.client("inspector2", region_name=REGION, config=self.boto3_config),
                "action": "list_findings",
                "params": {},
                "status": False,
                "reqd"  : True
            },
            "wafv2": {
                "name": "WAF v2",
                "client": boto3.client("wafv2", region_name=REGION, config=self.boto3_config),
                "action": "list_web_acls",
                "params": {"Scope": "REGIONAL"},
                "status": False,
                "reqd"  : True
            },
            "rds": {
                "name": "RDS",
                "client": boto3.client("rds", region_name=REGION, config=self.boto3_config),
                "action": "describe_db_instances",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "s3": {
                "name": "S3",
                "client": boto3.client("s3", region_name=REGION, config=self.boto3_config),
                "action": "list_buckets",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "elbv2": {
                "name": "ELB v2",
                "client": boto3.client("elbv2", region_name=REGION, config=self.boto3_config),
                "action": "describe_load_balancers",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "autoscaling": {
                "name": "Auto Scaling",
                "client": boto3.client("autoscaling", region_name=REGION, config=self.boto3_config),
                "action": "describe_auto_scaling_groups",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "lambda": {
                "name": "Lambda",
                "client": boto3.client("lambda", region_name=REGION, config=self.boto3_config),
                "action": "list_functions",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "compute-optimizer": {
                "name": "Compute Optimizer",
                "client": boto3.client("compute-optimizer", region_name=REGION, config=self.boto3_config),
                "action": "get_ec2_instance_recommendations",
                "params": params,
                "status": False,
                "reqd"  : False
            },
            "savingsplans": {
                "name": "Savings Plans",
                "client": boto3.client("savingsplans", region_name=REGION, config=self.boto3_config),
                "action": "describe_savings_plans",
                "params": params,
                "status": False,
                "reqd": False
            },
            
            "ce-ri": {
                "name": "Cost Explorer - RI Utilization",
                "client": boto3.client("ce", region_name=REGION, config=self.boto3_config),
                "action": "get_reservation_utilization",
                "params": {
                    "TimePeriod": {
                        "Start" : self.start_date.strftime("%Y-%m-%d"),
                        "End"   : self.end_date.strftime("%Y-%m-%d"),
                    },
                    "Granularity": "DAILY"
                },
                "status": False,
                "reqd": False
            },
            "support": {
                "name": "Trusted Advisor & Support Tickets",
                "client": boto3.client("support", region_name="us-east-1", config=self.boto3_config),
                "action": "describe_trusted_advisor_checks",
                "params": {'language':'en'},
                "status": False,
                "reqd"  : False
            },
            "health": {
                "name": "AWS Health",
                "client": boto3.client("health", region_name="us-east-1", config=self.boto3_config),
                "action": "describe_events",
                "params": params,
                "status": False,
                "reqd"  : False
            }            
        }

    def _is_optional(self, reqd):
        if not reqd:
            return "O"
        else:
            return "M"

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
            print(f"{SUCCESS} [{is_opt}] Connected to {service['name']}")
        except ClientError as e:
            print(f"{FAIL} [{is_opt}] Not Connected to {service['name']}: {str(e)}")
            service["status"] = False
        except Exception as e:
            print(f"{ERROR} [{is_opt}] Error testing {service['name']}: {str(e)}")
            service["status"] = None

    def test(self):
        print("Testing Connectivity to AWS Service Clients")
        print("*" * 43)
        print("Key: [M]-Mandatory, [O]-Optional")
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

""" 2. RESOURCE MANAGER """
class AWSResourceManager:
    def __init__(self, account_id, account=None, start_date=None, end_date=None, interval="DAILY", region="ap-southeast-1"):
        self.data		= AWSResourceInterface()
        self.account	= account
        self.account_id	= account_id
        self.start_date	= start_date
        self.end_date	= end_date
        self.interval	= interval
        self.region		= region
        self.days		= 1
        self.log		= 	{
                                "account_status" 		    : "Pass",			
                                "config_status" 		    : "Pass",
                                "service_status" 		    : "Pass",
                                "cost_status" 			    : "Pass",	
                                "security_status" 		    : "Pass",		
                                "inventory_status" 		    : "Pass",				
                                "marketplace_status" 	    : "Pass",			
                                "trusted_advisor_status"    : "Pass",
                                "health_status" 		    : "Pass",			
                                "application_status" 	    : "Pass",	
                                "resilience_hub_status"     : "Pass",
                                "compute_optimizer_status"  : "Pass",
                                "ri_sp_savings_status"      : "Pass",
                                "service_resources_status"  : "Pass",
                                "config_inventory_status"   : "Pass",
                                "support_tickets_status"    : "Pass",
                                'message'			        : []
                            }
        # Default to 1 days ago since that's the maximum for detailed data
        #self.start_date = self.start_date.strftime('%Y-%m-%d')
        #self.end_date   = self.end_date.strftime('%Y-%m-%d')
        
    # Setting the Date Range
    def get_date(self):
        
        if not self.end_date:
            self.end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
        if(self.interval == "YEARLY"):
            self.start_date = self.end_date.replace(month=1, day=1)
            self.end_date   = self.end_date.replace(month=12, day=31)
            self.days       = 366 if calendar.isleap(self.end_date.year) else 365
            #self.days       = 365

        elif(self.interval  == "MONTHLY"):
            self.start_date = self.end_date.replace(day=1)
            last_day_num    = calendar.monthrange(self.end_date.year, self.end_date.month)[1]
            self.end_date   = self.end_date.replace(day=last_day_num)
            self.days       = last_day_num
            #self.days = 30

        elif(self.interval  == "WEEKLY"):
            self.start_date = self.end_date - timedelta(days=self.end_date.weekday())
            self.end_date   = self.start_date + timedelta(days=6)
            self.days       = 7

        else:
            self.days = 1
            self.start_date = (self.end_date - timedelta(days=self.days)).replace(hour=0, minute=0, second=0, microsecond=0)
            # Default to 1 days ago since that's the maximum for detailed data
            
        #self.start_date = self.start_date.strftime('%Y-%m-%d')
        #self.end_date   = self.end_date.strftime('%Y-%m-%d')
        

        return True

    def _get_timezone_aware_dates(self):
        """Helper method to get timezone-aware start and end dates"""
        
        # Ensure dates are set
        if not self.start_date or not self.end_date:
            self.get_date()
        
        # Make dates timezone-aware for comparison
        start_date_aware    = self.start_date.replace(tzinfo=timezone.utc) if self.start_date and self.start_date.tzinfo is None else self.start_date
        end_date_aware      = self.end_date.replace(tzinfo=timezone.utc) if self.end_date and self.end_date.tzinfo is None else self.end_date
        
        return start_date_aware, end_date_aware

    # Update Logs
    def set_log(self, def_type:AWSResourceType, status="Pass", value=None):
        attr = def_type.value + "_status"  
        self.log[attr] = status    
        # Ensure message is a list
        if not isinstance(self.log['message'], list):
            self.log['message'] = []
            
        if value:
            try:
                self.log['message'].append(value)
            except AttributeError as e:
                print(f"Error: message must be a list. Current type: {type(self.log['message'])}")
                self.log['message'] = [value]
        
        self.data.set_data(attr=AWSResourceType.LOGS, data=self.log)
    
    #1. Fetching Account Data
    def get_account_details(self):
        account_client  = boto3.client('account')
        acc             = None
        try:
            acc             = AWSResponse(account_client.get_account_information())
        except Exception as e:
            print(f"Warning: Could not retrieve full account information: {str(e)}")

        sts_client  = boto3.client('sts')
        identity    = AWSResponse(sts_client.get_caller_identity())
        account_id  = identity.data.get('Account')

        result = {
            'account_id'        : self.account_id,
            'account_name'      : acc.data.get("AccountName") if acc is not None else account_id,
            'account_email'     : None,
            'account_status'    : "ACTIVE",
            'account_arn'       : None,
            'partner_name'      : PARTNER if PARTNER else 'None',
            'customer_name'     : CUSTOMER if CUSTOMER else 'None',
            'category'          : CATEGORY if CATEGORY else 'None',
            'account_type'      : ENVIRONMENT if ENVIRONMENT else 'None',
            'joined_method'     : None,
            'joined_timestamp'  : acc.data.get("AccountCreatedDate") if acc is not None else None,
            'region'            : REGION,
            'product'           : PRODUCT if PRODUCT else 'None',
            'contact_info'      : {},
            'alternate_contacts': {}
        }

        # Get Contact Information
        try:
            contact_info            = AWSResponse(account_client.get_contact_information())
            contact_data            = contact_info.data.get('ContactInformation', {})
            result['contact_info']  = {field: contact_data.get(key) for field, key in [
                ('address_line1', 'AddressLine1'), ('address_line2', 'AddressLine2'),
                ('address_line3', 'AddressLine3'), ('city', 'City'),
                ('country_code', 'CountryCode'), ('postal_code', 'PostalCode'),
                ('state_or_region', 'StateOrRegion'), ('company_name', 'CompanyName'),
                ('phone_number', 'PhoneNumber'), ('website_url', 'WebsiteUrl'),
                ('full_name', 'FullName')
            ]}
        except Exception as e:
            print(f"Error getting contact information: {str(e)}")

        # Get alternate contacts
        try:
            for contact_type in ['BILLING', 'OPERATIONS', 'SECURITY']:
                try:
                    alternate_contact   = AWSResponse(account_client.get_alternate_contact(AlternateContactType=contact_type))
                    contact_data        = alternate_contact.data.get('AlternateContact', {})

                    result['alternate_contacts'][contact_type.lower()] = {
                        'name': contact_data.get('Name'),
                        'title': contact_data.get('Title'),
                        'email': contact_data.get('EmailAddress'),
                        'phone': contact_data.get('PhoneNumber')
                    }
                except account_client.exceptions.ResourceNotFoundException:
                    result['alternate_contacts'][contact_type.lower()] = None
        except Exception as e:
            print(f"Error getting alternate contacts: {str(e)}")

        self.data.set_data(attr=AWSResourceType.ACCOUNT, data=result)

        self.set_log(def_type=AWSResourceType.ACCOUNT)
        return result

    #2. Fetching Services Data
    def get_services(self): 
        try:
            if not self.get_date():
                return None
            
            response = AWSResponse(boto3.client('ce').get_cost_and_usage(
                TimePeriod  =   {'Start': self.start_date.strftime('%Y-%m-%d') if self.start_date else '', 'End': self.end_date.strftime('%Y-%m-%d') if self.end_date else ''},
                Granularity =   self.interval,
                Metrics     =   ['UnblendedCost'], #REMOVED ['BlendedCost', 'NetUnblendedCost', 'AmortizedCost', 'UsageQuantity'] # NOT USED
                GroupBy     =   [{'Type': 'DIMENSION', 'Key': 'SERVICE'}], #REMOVED {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'} #this gives too much data
                #Filter      =   {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [self.account_id]}}
                Filter      =   {
                                    'And': [
                                        {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [self.account_id]}},
                                        {'Dimensions': {'Key': 'REGION', 'Values': [self.region]}}
                                    ]
                                }

            ))

            result_data = []

            for result in response.data.get('ResultsByTime', []):
                time_period = result['TimePeriod']
                for group in result.get('Groups', []):
                    service             = group['Keys'][0]
                    usage_type          = "Aggregated" #REMOVED: Detailed Datasets, Customer can opt to switch on #group['Keys'][1]
                    metrics             = group['Metrics']
                    unblended           = float(metrics['UnblendedCost']['Amount'])
                    utilization         = None #REMOVED: Detailed Datasets, Customer can opt to switch on #float(metrics['UsageQuantity']['Amount']) or None
                    utilization_unit    = None #REMOVED: Detailed Datasets, Customer can opt to switch on #str(metrics['UsageQuantity']['Unit']) or None
                    
                    result_data.append({
                        'service'               : service,
                        'usage_types'           : usage_type,
                        'date_from'             : time_period['Start'],
                        'date_to'               : time_period['End'],
                        'cost'                  : unblended,
                        'currency'              : metrics['UnblendedCost']['Unit'],
                        'utilization'           : utilization,
                        'utilization_unit'      : utilization_unit
                    })

            result_data = sorted(result_data, key=lambda x: x['cost'], reverse=True)

            self.data.set_data(attr=AWSResourceType.SERVICE, data=result_data)
            self.set_log(def_type=AWSResourceType.SERVICE)
            return result_data
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SERVICE, status="Fail", value={'services_data': str(e)})
            return None
    
    #3. Fetching Config Data
    def get_config(self):
        try:
            if not self.get_date():
                return None
            
            config_client = boto3.client('config', region_name=REGION)
            
            # Step 0: Convert dates to compare
            if not self.start_date or not self.end_date:
                return None
            
            # Use start_date for both start and end to get single day range
            start_datetime  = datetime.combine(self.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_datetime    = datetime.combine(self.start_date, datetime.min.time()).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

            # Step 1: Build Conformance Mapping
            rule_to_pack_mapping    = {}
            try:
                for pack in config_client.describe_conformance_packs()['ConformancePackDetails']:
                    pack_name = pack['ConformancePackName']
                    
                    try:
                        pack_compliance = config_client.describe_conformance_pack_compliance(
                            ConformancePackName=pack_name
                        )
                        
                        for rule_compliance in pack_compliance['ConformancePackRuleComplianceList']:
                            if rule_name := rule_compliance.get('ConfigRuleName'):
                                rule_to_pack_mapping[rule_name] = pack_name
                                
                    except Exception as e:
                        self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Conformance Pack: " + str(e)})
                        pass
                        
            except Exception as e:
                self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Conformance Pack: " + str(e)})
                pass

            # Step 2: Get all compliance data
            compliant_count         = 0
            non_compliant_count     = 0
            non_compliant_resources = []
            curr_non_compliant      = 0 # Non-Compliant rules on the date this script is run
            curr_compliant          = 0 # Compliant rules on the date this script is run

            paginator = config_client.get_paginator('describe_compliance_by_config_rule')
            
            for page in paginator.paginate(ComplianceTypes=['COMPLIANT', 'NON_COMPLIANT']):
                for rule in page.get('ComplianceByConfigRules', []):
                    compliance_type = rule.get('Compliance', {}).get('ComplianceType')
                    
                    if compliance_type in ('COMPLIANT', 'NON_COMPLIANT'):

                        if compliance_type == 'COMPLIANT':
                            compliant_count += 1
                        elif compliance_type == 'NON_COMPLIANT':
                            non_compliant_count += 1

                        rule_name           = rule['ConfigRuleName']
                        conformance_pack    = rule_to_pack_mapping.get(rule_name, 'Standalone')
                        has_matching_result = False

                        try:
                            details = config_client.get_compliance_details_by_config_rule(
                                ConfigRuleName=rule_name,
                                ComplianceTypes=[compliance_type],
                                Limit=50
                            )

                            for eval_result in details['EvaluationResults']:
                                #config_rule_invoked_time = eval_result.get('ConfigRuleInvokedTime')
                                result_time = eval_result.get('ResultRecordedTime')

                                # Convert result_time to UTC for comparison
                                if result_time:
                                    result_time_utc = result_time.astimezone(timezone.utc)
                                    
                                    if start_datetime <= result_time_utc <= end_datetime:
                                        has_matching_result = True
                                        qualifier   = eval_result['EvaluationResultIdentifier']['EvaluationResultQualifier']
                                        non_compliant_resources.append({
                                                                        'rule_name'                 : rule_name,
                                                                        'resource_id'               : qualifier.get('ResourceId'),
                                                                        'resource_type'             : qualifier.get('ResourceType'),
                                                                        'config_rule_invoked_time'  : result_time,
                                                                        'conformance_pack'          : conformance_pack,
                                                                        'compliance_type'           : eval_result.get('ComplianceType'),
                                                                        'annotation'                : eval_result.get('Annotation'),
                                                                        'evaluation_mode'           : qualifier.get('EvaluationMode')
                                                                        })
                            if has_matching_result:
                                
                                if compliance_type == 'COMPLIANT':
                                    curr_compliant += 1 # Compliant rules on the date this script is run
                                elif compliance_type == 'NON_COMPLIANT':
                                    curr_non_compliant += 1 # Non-Compliant rules on the date this script is run
                                 
                        except Exception as e:
                            self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': "Compliance rules: "+str(e)})


                    
                        rule_name           = rule['ConfigRuleName']
                        conformance_pack    = rule_to_pack_mapping.get(rule_name, 'Standalone')
                        has_matching_result = False
                        
                        

            # Step 3: Calculate totals and score
            
            total_rules     = compliant_count + non_compliant_count
            compliance_score= round((compliant_count / max(total_rules, 1)) * 100, 2) if total_rules > 0 else 0
            config_data     = {
                                'date_from'                 : self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
                                'date_to'                   : self.end_date.strftime('%Y-%m-%d') if self.end_date else '',
                                'compliance_score'          : compliance_score,
                                'total_rules'               : total_rules,
                                'compliant_rules'           : compliant_count,
                                'non_compliant_rules'       : non_compliant_count,
                                'curr_non_compliant'        : curr_non_compliant,
                                'curr_compliant'            : curr_compliant,
                                'non_compliant_resources'   : non_compliant_resources
                              }
            #print({'curr_non_compliant': curr_non_compliant,'curr_compliant': curr_compliant,})
            self.data.set_data(attr=AWSResourceType.CONFIG, data=config_data)
            self.set_log(def_type=AWSResourceType.CONFIG)

            return config_data
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': str(e)})
            return None

    #4. Fetching Cost Data
    def get_cost(self):
        cost_filter =   {
                            'And': [
                                {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [self.account_id]}},
                                {'Dimensions': {'Key': 'REGION', 'Values': [self.region]}}
                            ]
                        }
        try:
            if not self.get_date():
                return None
                
            ce_client   = boto3.client('ce')
            start_date  = self.start_date.strftime('%Y-%m-%d') if self.start_date else ''
            end_date    = self.end_date.strftime('%Y-%m-%d') if self.end_date else '' # takes for the current date
            
            # Get all cost metrics
            current_costs = AWSResponse(ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity=self.interval,
                Metrics=['UnblendedCost'], #, 'BlendedCost', 'NetUnblendedCost', 'AmortizedCost'
                Filter=cost_filter
            ))
            
            # Get service breakdown
            service_costs = AWSResponse(ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity=self.interval,
                Metrics=['UnblendedCost'], #, 'BlendedCost', 'NetUnblendedCost', 'AmortizedCost'
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
                Filter=cost_filter
            ))
            
            prev_end    = self.start_date.strftime('%Y-%m-%d') if self.start_date else ''
            prev_start  = (self.start_date - timedelta(days=self.days)).strftime('%Y-%m-%d') if self.start_date else ''
            
            previous_costs = AWSResponse(ce_client.get_cost_and_usage(
                TimePeriod={'Start': prev_start, 'End': prev_end},
                Granularity=self.interval,
                Metrics=['UnblendedCost'], #, 'BlendedCost', 'NetUnblendedCost', 'AmortizedCost'
                Filter=cost_filter
            ))
            
            # Calculate totals for all metrics - always sum for consistency
            def extract_costs(response):
                return {
                    'unblended'     : sum(float(r['Total']['UnblendedCost']['Amount']) for r in response.data['ResultsByTime']),
                    'blended'       : 0, #sum(float(r['Total']['BlendedCost']['Amount']) for r in response.data['ResultsByTime']),
                    'net_unblended' : 0, #sum(float(r['Total']['NetUnblendedCost']['Amount']) for r in response.data['ResultsByTime']),
                    'amortized'     : 0, #sum(float(r['Total']['AmortizedCost']['Amount']) for r in response.data['ResultsByTime'])
                }
            
            current     = extract_costs(current_costs)
            previous    = extract_costs(previous_costs)
            
            # Get top services
            top_services = []
            if service_costs.data['ResultsByTime']:
                latest_period = service_costs.data['ResultsByTime'][-1]
                top_services = [{
                    'service'           : s['Keys'][0],
                    'cost'              : float(s['Metrics']['UnblendedCost']['Amount']),
                    #'unblended_cost'   : float(s['Metrics']['UnblendedCost']['Amount']),
                    #'blended_cost'     : float(s['Metrics']['BlendedCost']['Amount']),
                    #'net_unblended_cost': float(s['Metrics']['NetUnblendedCost']['Amount']),
                    #'amortized_cost'   : float(s['Metrics']['AmortizedCost']['Amount'])
                } for s in sorted(latest_period['Groups'], key=lambda x: float(x['Metrics']['UnblendedCost']['Amount']), reverse=True)[:5]]
            
            forecast_data = []
            try:
                forecast_end = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                forecast = AWSResponse(ce_client.get_cost_forecast(
                    TimePeriod={'Start': end_date, 'End': forecast_end},
                    Metric='UNBLENDED_COST',
                    Granularity="MONTHLY",
                    Filter=cost_filter
                ))
                forecast_data = [{'period': {'start': p['TimePeriod']['Start'], 'end': p['TimePeriod']['End']}, 'amount': float(p['MeanValue'])}
                                for p in forecast.data.get('ForecastResultsByTime', [])]
            except Exception as e:
                self.set_log(def_type=AWSResourceType.COST, status="Fail", value={'Forecast unavailable': str(e)})
            
            summary =   {
                            'account_id'                    : self.account_id,
                            'current_period_cost'           : current['unblended'],
                            'previous_period_cost'          : previous['unblended'],
                            #'unblended_cost'                : current['unblended'],
                            #'blended_cost'                  : current['blended'],
                            #'net_unblended_cost'            : current['net_unblended'],
                            #'amortized_cost'                : current['amortized'],
                            #'credits_refunds'               : current['unblended'] - current['net_unblended'],
                            #'previous_unblended_cost'       : previous['unblended'],
                            #'previous_blended_cost'         : previous['blended'],
                            #'previous_net_unblended_cost'   : previous['net_unblended'],
                            #'previous_amortized_cost'       : previous['amortized'],
                            'cost_difference'               : current['unblended'] - previous['unblended'],
                            'cost_difference_percentage'    : ((current['unblended'] - previous['unblended']) / previous['unblended'] * 100) if previous['unblended'] > 0 else 0,
                            'top_services'                  : top_services,
                            'period'                        : {'start': start_date, 'end': end_date, 'granularity': self.interval},
                            'forecast'                      : forecast_data
                        }
            
            self.data.set_data(attr=AWSResourceType.COST, data=summary)
            self.set_log(def_type=AWSResourceType.COST)
            return summary
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.COST, status="Fail", value={'cost_analysis': str(e)})
            return None

    def get_patch_details(self, instance_id):
        """Get detailed patch information using Patch Manager API"""
        try:
            ssm = boto3.client('ssm', region_name=REGION)
            patches = []
            
            # Get individual patches for this instance directly
            patch_response = AWSResponse(ssm.describe_instance_patches(InstanceId=instance_id))
            
            # Get timezone-aware dates for comparison
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()

            for patch in patch_response.data.get('Patches', []):
                installed_time = patch.get('InstalledTime')

                if installed_time and start_date_aware <= installed_time <= end_date_aware:
                    patches.append({
                                    'instance_id'   : instance_id,
                                    'title'         : patch.get('Title'),
                                    'classification': patch.get('Classification') or "Normal",
                                    'severity'      : patch.get('Severity') or "None",
                                    'state'         : patch.get('State'),
                                    'installed_time': patch.get('InstalledTime')
                                })
                
            return patches
        except Exception as e:
            print(f"Error getting patch details for {instance_id}: {str(e)}")
            return []

    #5. Fetching Inventory Data from Systems Manager
    def get_inventory(self):
        try:
            ssm = boto3.client('ssm', region_name=REGION)
            security_inventory = {
                'instances'     : [],
                'applications'  : [],
                'patches'       : [],
                'services'      : [],
                'users'         : [],
                'processes'     : [],
                'network_ports' : [],
                'certificates'  : []
            }
            
            instances   = AWSResponse(ssm.describe_instance_information())
            # Write to JSON file
            #print(json.dumps(instances.data.get('InstanceInformationList', []), indent=2, cls=DateTimeEncoder))

            for instance in instances.data.get('InstanceInformationList', []):
                instance_id = instance['InstanceId']
                
                # Add instance info
                security_inventory['instances'].append({
                    'instance_id'                   : instance_id,
                    'platform'                      : instance.get('PlatformName'),
                    'platform_type'                 : instance.get('PlatformType'),
                    'platform_version'              : instance.get('PlatformVersion'),
                    'agent_version'                 : instance.get('AgentVersion'),
                    'is_latest_version'             : instance.get('IsLatestVersion'),
                    'last_ping'                     : instance.get('LastPingDateTime'),
                    'computer_name'                 : instance.get('ComputerName'),
                    'instance_type'                 : instance.get('ResourceType'),
                    'ip_address'                    : instance.get('IPAddress'),
                    'ping_status'                   : instance.get('PingStatus'),
                    'last_ping_date_time'           : instance.get('LastPingDateTime'),
                    'association_status'            : instance.get('AssociationStatus'),
                    'association_execution_date'    : instance.get('LastAssociationExecutionDate'),
                    'association_success_date'      : instance.get('LastSuccessfulAssociationExecutionDate')
                })
                
                # Get security-relevant inventory types (only supported ones)
                for inv_type, key in [('AWS:PatchSummary', 'patches')]:
                    try:
                        resp = AWSResponse(ssm.get_inventory(
                            Filters=[{'Key': 'AWS:InstanceInformation.InstanceId', 'Values': [instance_id]}],
                            ResultAttributes=[{'TypeName': inv_type}]
                        ))
                                                
                        for entity in resp.data.get('Entities', []):
                            for data_item in entity.get('Data', {}).values():
                                for item in data_item.get('Content', []):
                                    if inv_type == 'AWS:PatchSummary':
                                        detailed_patches = self.get_patch_details(instance_id)
                                        security_inventory['patches'].extend(detailed_patches)
                    except Exception as e:
                        print(f"Error processing inventory type {inv_type} for instance {instance_id}: {str(e)}")
                        continue
            
            self.data.set_data(attr=AWSResourceType.INVENTORY, data=security_inventory)
            self.set_log(def_type=AWSResourceType.INVENTORY)
            return security_inventory
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.INVENTORY, status="Fail", value={'inventory': str(e)})
            return None

    #6.Fetching Security data across Security hub, Guard Duty, IAM, KMS, WAF, Inspector and Trusted Advisor.
    def get_security(self):
        try:
            result  =   {
                            'security_hub'          : [],
                            'guard_duty'            : [],
                            'kms'                   : [],
                            'waf'                   : [],
                            'waf_rules'             : [],
                            'cloudtrail'            : [],
                            'secrets_manager'       : [],
                            'certificate_manager'   : [],
                            'inspector'             : []
                        }
            
            # Fetch all security services in parallel
            security_tasks  =   {
                                    'security_hub'          : self.get_security_hub,
                                    'guard_duty'            : self.get_guard_duty_security,
                                    'kms'                   : self.get_kms_security,
                                    'waf'                   : self.get_waf_security,
                                    'waf_rules'             : self.get_waf_rules,
                                    'cloudtrail'            : self.get_cloudtrail_security,
                                    'secrets_manager'       : self.get_secrets_security,
                                    'certificate_manager'   : self.get_certificate_security,
                                    'inspector'             : self.get_inspector
                                }
            
            with ThreadPoolExecutor(max_workers=9) as executor:
                futures = {executor.submit(func): key for key, func in security_tasks.items()}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        result[key] = future.result() or []
                    except Exception as e:
                        #print(f"Error fetching {key}: {str(e)}")
                        result[key] = []
            
            self.data.set_data(attr=AWSResourceType.SECURITY, data=result)
            self.set_log(def_type=AWSResourceType.SECURITY, status="Pass")
            return result
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'security_all': str(e)})
            return None
        
    #Getting from Security hub
    def get_security_hub(self):
        try:
            if not self.get_date():
                return None
                
            securityhub = boto3.client('securityhub', region_name=REGION)
            service_findings = {}
            
            # Query 1: Get NEW findings Created today
            next_token = None
            params = {
                'Filters'   : {
                                'CreatedAt'     :   [{'Start': self.start_date.isoformat() if self.start_date else '', 'End': self.end_date.isoformat() if self.end_date else ''}],
                                'RecordState'   :   [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
                                'AwsAccountId'  :   [{'Value': self.account_id, 'Comparison': 'EQUALS'}],
                                'SeverityLabel' :   [
                                                        {'Value': 'CRITICAL', 'Comparison': 'EQUALS'},
                                                        {'Value': 'HIGH', 'Comparison': 'EQUALS'},
                                                        {'Value': 'MEDIUM', 'Comparison': 'EQUALS'},
                                                        {'Value': 'LOW', 'Comparison': 'EQUALS'}
                                                    ],
                                'WorkflowStatus':   [
                                                        {'Value': 'NEW', 'Comparison': 'EQUALS'}
                                                    ],
                            },
                'MaxResults': 100
            }

            for query_type in ['created', 'updated']:
                # Query 2: Get findings UPDATED today whichw as either, RESOLVED, NOTIFIED or SUPPRESSED
                if query_type == 'updated':
                    params['Filters'].pop('CreatedAt')
                    params['Filters']['UpdatedAt']      = [ {'Start': self.start_date.isoformat() if self.start_date else '', 'End': self.end_date.isoformat() if self.end_date else ''}]
                    params['Filters']['WorkflowStatus'] = [
                                                            {'Value': 'RESOLVED', 'Comparison': 'EQUALS'},
                                                            {'Value': 'NOTIFIED', 'Comparison': 'EQUALS'},
                                                            {'Value': 'SUPPRESSED', 'Comparison': 'EQUALS'}
                                                          ]
                
                params.pop('NextToken', None)
                next_token = None

                while True:
                    if next_token:
                        params['NextToken'] = next_token
                
                    response = AWSResponse(securityhub.get_findings(**params))
                    if response.status != 200:
                        break
                    
                    for finding in response.data['Findings']:
                        self._process_finding(finding, service_findings)
                
                    next_token = response.data.get('NextToken')
                    if not next_token:
                        break
            

            
            result = sorted(service_findings.values(), key=lambda x: x['total_findings'], reverse=True)
            self.set_log(def_type=AWSResourceType.SECURITY)
            
            """ TROUBLESHOOTING ONLY """
            #print(f"from: {self.start_date} to: {self.end_date}")
            #print(f"Total Findings:{result}")
            
            return result
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'security_hub': str(e)})
            return None

    def _process_finding(self, finding, service_findings):
        finding_id = finding.get('Id')
        
        # Skip if already processed
        for service_data in service_findings.values():
            if any(f['finding_id'] == finding_id for f in service_data['findings']):
                return
        
        service = finding.get('ProductName', '')
        if service not in service_findings:
            service_findings[service]   =   {
                                                'service'           : service,
                                                'total_findings'    : 0,
                                                'severity_counts'   : {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFORMATIONAL': 0},
                                                'open_findings'     : 0,
                                                'resolved_findings' : 0,
                                                'findings'          : []
                                            }
        
        service_findings[service]['total_findings'] += 1
        severity = finding.get('Severity', {}).get('Label', 'UNKNOWN')
        
        if severity in service_findings[service]['severity_counts']:
            service_findings[service]['severity_counts'][severity] += 1
        
        workflow_status = finding.get('Workflow', {}).get('Status')
        if workflow_status == 'RESOLVED':
            service_findings[service]['resolved_findings'] += 1
        else:
            service_findings[service]['open_findings'] += 1
        
        resource = finding.get('Resources', [{}])[0]
        service_findings[service]['findings'].append({
                                                        'finding_id'        : finding.get('Id'),
                                                        'service'           : resource.get('Type'),
                                                        'title'             : finding.get('Title'),
                                                        'description'       : finding.get('Description'),
                                                        'severity'          : severity,
                                                        'status'            : workflow_status or 'OPEN',
                                                        'resource_type'     : resource.get('Type'),
                                                        'resource_id'       : resource.get('Id'),
                                                        'created_at'        : finding.get('CreatedAt'),
                                                        'updated_at'        : finding.get('UpdatedAt'),
                                                        'recommendation'    : finding.get('Remediation', {}).get('Recommendation', {}).get('Text'),
                                                        'compliance_status' : finding.get('Compliance', {}).get('Status'),
                                                        'region'            : finding.get('Region'),
                                                        'workflow_state'    : finding.get('WorkflowState', ''),
                                                        'record_state'      : finding.get('RecordState', 'ACTIVE'),
                                                        'product_name'      : finding.get('ProductName'),
                                                        'company_name'      : finding.get('CompanyName'),
                                                        'product_arn'       : finding.get('ProductArn'),
                                                        'generator_id'      : finding.get('GeneratorId'),
                                                        'generator'         : finding.get('ProductName', '')
                                                    })
       
    #Getting from Guard Duty
    def get_guard_duty_security(self):
        """Get GuardDuty threat findings within date range"""
        try:
            guardduty = boto3.client('guardduty', region_name=REGION)
            findings = []
            
            # Ensure dates are set
            if not self.start_date or not self.end_date:
                self.get_date()
            
            detectors = AWSResponse(guardduty.list_detectors())
            for detector_id in detectors.data.get('DetectorIds', []):
                # Add date range filter to list_findings
                finding_criteria = {
                    'Criterion': {
                        'updatedAt': {
                            'Gte': int(self.start_date.timestamp() * 1000) if self.start_date else 0,  # Convert to milliseconds
                            'Lte': int(self.end_date.timestamp() * 1000) if self.end_date else 0
                        }
                    }
                }
                
                finding_ids = AWSResponse(guardduty.list_findings(
                    DetectorId=detector_id,
                    FindingCriteria=finding_criteria
                ))
                
                if finding_ids.data.get('FindingIds'):
                    finding_details = AWSResponse(guardduty.get_findings(
                        DetectorId=detector_id,
                        FindingIds=finding_ids.data['FindingIds'][:50]
                    ))
                    for finding in finding_details.data.get('Findings', []):
                        findings.append({
                                            'id'            : finding.get('Id'),
                                            'type'          : finding.get('Type'),
                                            'severity'      : finding.get('Severity'),
                                            'title'         : finding.get('Title'),
                                            'description'   : finding.get('Description'),
                                            'created_at'    : finding.get('CreatedAt'),
                                            'updated_at'    : finding.get('UpdatedAt'),
                                            'confidence'    : finding.get('Confidence'),
                                            'region'        : finding.get('Region')
                                        })
            return findings
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'guard_duty': str(e)})
            return []

    #Getting IAM data
    def get_iam_security(self):
        """Get IAM security posture within date range"""
        try:
            iam = boto3.client('iam')
            iam_data = {
                        'users'         : [],
                        'roles'         : [],
                        'policies'      : [],
                        'access_keys'   : [],
                        'mfa_devices'   : []
                    }
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            # Get users with security details (filter by creation date)
            users = AWSResponse(iam.list_users())
            for user in users.data.get('Users', []):
                user_created        = user.get('CreateDate')
                password_last_used  = user.get('PasswordLastUsed')
                
                # Filter users created or with password used within date range
                if (user_created and start_date_aware and end_date_aware and start_date_aware <= user_created <= end_date_aware) or (password_last_used and start_date_aware and end_date_aware and start_date_aware <= password_last_used <= end_date_aware):
                    
                    username = user.get('UserName')
                    iam_data['users'].append({
                                                'username'          : username,
                                                'created_date'      : user.get('CreateDate'),
                                                'password_last_used': password_last_used,
                                                'mfa_enabled'       : len(AWSResponse(iam.list_mfa_devices(UserName=username)).data.get('MFADevices', [])) > 0,
                                                'access_keys_count' : len(AWSResponse(iam.list_access_keys(UserName=username)).data.get('AccessKeyMetadata', []))
                                            })
            
            return iam_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'iam': str(e)})
            return {}

    #Getting Key Managment System data
    def get_kms_security(self):
        """Get KMS key security information within date range"""
        try:
            kms = boto3.client('kms', region_name=REGION)
            kms_data = []
            
            # Ensure dates are set
            if not self.start_date or not self.end_date:
                self.get_date()
            
            keys = AWSResponse(kms.list_keys())
            for key in keys.data.get('Keys', []):
                key_id = key.get('KeyId')
                try:
                    key_details     = AWSResponse(kms.describe_key(KeyId=key_id))
                    key_metadata    = key_details.data.get('KeyMetadata', {})
                    creation_date   = key_metadata.get('CreationDate')
                    
                    # Filter keys created within date range
                    #if creation_date and self.start_date <= creation_date.replace(tzinfo=None) <= self.end_date:
                    try:
                        rotation_enabled = AWSResponse(kms.get_key_rotation_status(KeyId=key_id)).data.get('KeyRotationEnabled', False)
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'AccessDeniedException':
                            rotation_enabled = True  # Mark as unknown
                        else:
                            raise

                    kms_data.append({
                                        'key_id'                : key_id,
                                        'arn'                   : key_metadata.get('Arn'),
                                        'description'           : key_metadata.get('Description'),
                                        'key_usage'             : key_metadata.get('KeyUsage'),
                                        'key_state'             : key_metadata.get('KeyState'),
                                        'creation_date'         : creation_date,
                                        'enabled'               : key_metadata.get('Enabled'),
                                        'key_rotation_enabled'  : rotation_enabled
                                    })
                except Exception as e:
                    print(f"Error processing KMS key {key_id}: {str(e)}")
                    continue
            return kms_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'kms': str(e)})
            return []

    #Getting Waf configuration
    def get_waf_security(self):
        try:
            waf_data = []
             
            # Check all scopes: REGIONAL, CLOUDFRONT, and GLOBAL
            for scope in ['REGIONAL', 'CLOUDFRONT']:
                try:
                    # Use us-east-1 for CLOUDFRONT scope, current region for others
                    region  = 'us-east-1' if scope == 'CLOUDFRONT' else REGION
                    waf     = boto3.client('wafv2', region_name=region)
                    
                    web_acls = AWSResponse(waf.list_web_acls(Scope=scope))
                    for acl in web_acls.data.get('WebACLs', []):
                        acl_details = AWSResponse(waf.get_web_acl(Name=acl.get('Name'), Scope=scope, Id=acl.get('Id')))
                        web_acl     = acl_details.data.get('WebACL', {})
                        rules       = web_acl.get('Rules', [])
                        
                        # Get resources and logging
                        try:
                            resources = AWSResponse(waf.list_resources_for_web_acl(
                                WebACLArn=web_acl.get('ARN'),
                                ResourceType='APPLICATION_LOAD_BALANCER' if scope == 'REGIONAL' else 'CLOUDFRONT'
                            )).data.get('ResourceArns', [])
                            logging_config                      = AWSResponse(waf.get_logging_configuration(ResourceArn=web_acl.get('ARN')))
                            logging_enabled, log_destination    = True, logging_config.data.get('LoggingConfiguration', {}).get('LogDestinationConfigs', [])
                        except:
                            resources, logging_enabled, log_destination = [], False, []
                        
                        # Analyze rules
                        rule_types = {'managed': 0, 'custom': 0, 'rate_limit': 0}
                        blocked_countries, ip_sets = [], []
                        
                        for rule in rules:
                            statement = rule.get('Statement', {})
                            if 'ManagedRuleGroupStatement' in statement:
                                rule_types['managed'] += 1
                            elif 'RateBasedStatement' in statement:
                                rule_types['rate_limit'] += 1
                            else:
                                rule_types['custom'] += 1
                            
                            if 'GeoMatchStatement' in statement:
                                blocked_countries.extend(statement['GeoMatchStatement'].get('CountryCodes', []))
                            if 'IPSetReferenceStatement' in statement:
                                ip_sets.append(statement['IPSetReferenceStatement'].get('ARN'))
                        
                        waf_data.append({
                                            'name'                      : acl.get('Name'), 
                                            'id'                        : acl.get('Id'), 
                                            'arn'                       : web_acl.get('ARN'),
                                            'scope'                     : scope, 
                                            'description'               : acl.get('Description', ''),
                                            'default_action'            : web_acl.get('DefaultAction'), 
                                            'rules_count'               : len(rules),
                                            'capacity'                  : web_acl.get('Capacity', 0),
                                            'managed_rules_count'       : rule_types['managed'], 
                                            'custom_rules_count'        : rule_types['custom'],
                                            'rate_limit_rules_count'    : rule_types['rate_limit'],
                                            'associated_resources'      : resources, 
                                            'associated_resources_count': len(resources),
                                            'logging_enabled'           : logging_enabled, 
                                            'log_destinations'          : log_destination,
                                            'geo_blocking_enabled'      : len(blocked_countries) > 0, 
                                            'blocked_countries'         : blocked_countries,
                                            'ip_sets'                   : ip_sets, 
                                            'created_date'              : web_acl.get('CreationDate'),
                                            'last_modified'             : web_acl.get('LastModifiedTime'), 
                                            'tags'                      : web_acl.get('Tags', []),
                                            'sampled_requests_enabled'  : any(rule.get('VisibilityConfig', {}).get('SampledRequestsEnabled', False) for rule in rules),
                                            'cloudwatch_metrics_enabled': any(rule.get('VisibilityConfig', {}).get('CloudWatchMetricsEnabled', False) for rule in rules)
                                        })
                except Exception as e:
                    print(f"Error processing WAF scope {scope}: {str(e)}")
                    continue
            return waf_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'waf': str(e)})
            return []
    
    #Fetching data from Waf Rules
    def get_waf_rules(self):
        waf_rules = []
        
        try:
            # Check both REGIONAL and CLOUDFRONT scopes
            scopes_to_check = ['REGIONAL', 'CLOUDFRONT']
            
            for scope in scopes_to_check:
                try:
                    wafv2       = boto3.client('wafv2', region_name='us-east-1' if scope == 'CLOUDFRONT' else REGION)
                    web_acls    = wafv2.list_web_acls(Scope=scope)['WebACLs']
                    
                    for acl in web_acls:
                        acl_details = wafv2.get_web_acl(Name=acl['Name'], Scope=scope, Id=acl['Id'])
                        
                        # Check ACL-level logging
                        try:
                            wafv2.get_logging_configuration(ResourceArn=acl_details['WebACL']['ARN'])
                            logging_enabled = True
                        except:
                            logging_enabled = False
                        
                        for rule in acl_details['WebACL']['Rules']:
                            statement       = rule.get('Statement', {})
                            statement_type  = list(statement.keys())[0] if statement else 'Unknown'
                            visibility      = rule.get('VisibilityConfig', {})
                            
                            # Handle missing Action field - use OverrideAction if Action is missing
                            action = rule.get('Action')
                            if not action:
                                action = rule.get('OverrideAction', {'None': {}})
                            
                            # Analyze rule properties
                            is_managed          = statement_type == 'ManagedRuleGroupStatement'
                            is_rate_limit       = statement_type == 'RateBasedStatement'
                            has_geo_blocking    = 'GeoMatchStatement' in str(statement)
                            has_sql_injection   = 'SqliMatchStatement' in str(statement) or (is_managed and 'SQLi' in statement.get('ManagedRuleGroupStatement', {}).get('Name', ''))
                            has_xss_protection  = 'XssMatchStatement' in str(statement) or (is_managed and 'XSS' in statement.get('ManagedRuleGroupStatement', {}).get('Name', ''))

                            waf_rules.append({
                                                'web_acl_name'          : acl['Name'],
                                                'rule_name'             : rule['Name'],
                                                'priority'              : rule['Priority'],
                                                'action'                : action,
                                                'statement_type'        : statement_type,
                                                'is_managed_rule'       : is_managed,
                                                'is_custom_rule'        : not is_managed,
                                                'rate_limit'            : is_rate_limit,
                                                'logging_enabled'       : logging_enabled,
                                                'geo_blocking'          : has_geo_blocking,
                                                'sql_injection'         : has_sql_injection,
                                                'sample_request_enabled': visibility.get('SampledRequestsEnabled', False),
                                                'cloudwatch_enabled'    : visibility.get('CloudWatchMetricsEnabled', False),
                                                'has_xss_protection'    : has_xss_protection,
                                                'waf_version'           : 'v2',
                                                'is_compliant'          : self._check_waf_rule_compliance(statement_type, statement),
                                                'scope'                 : scope
                                            })
                except Exception as e:
                    print(f"Error checking {scope} scope: {str(e)}")
                    continue
                            
        except Exception as e:
            print(f"WAF v2 failed: {str(e)}")
            # Fallback to WAF v1
            try:
                waf = boto3.client('waf')
                web_acls = waf.list_web_acls()['WebACLs']
                
                for acl in web_acls:
                    acl_details = waf.get_web_acl(WebACLId=acl['WebACLId'])
                    
                    for rule_ref in acl_details['WebACL']['Rules']:
                        rule = waf.get_rule(RuleId=rule_ref['RuleId'])
                        
                        waf_rules.append({
                                            'web_acl_name'          : acl['Name'],
                                            'rule_name'             : rule['Rule']['Name'],
                                            'priority'              : rule_ref['Priority'],
                                            'action'                : rule_ref['Action'],
                                            'statement_type'        : 'WAFv1_Rule',
                                            'is_managed_rule'       : False,
                                            'is_custom_rule'        : True,
                                            'rate_limit'            : False,
                                            'logging_enabled'       : False,
                                            'geo_blocking'          : False,
                                            'sql_injection'         : False,
                                            'sample_request_enabled': False,
                                            'cloudwatch_enabled'    : False,
                                            'has_xss_protection'    : False,
                                            'waf_version'           : 'v1',
                                            'is_compliant'          : False
                                        })
            except Exception as e:
                print(f"WAF v1 also failed: {str(e)}")
        
        return waf_rules

    def _check_waf_rule_compliance(self, statement_type, statement):
        """Check if a WAF rule meets compliance requirements"""
        # Compliant rule types
        compliant_types =   [
                                'RateBasedStatement',
                                'ManagedRuleGroupStatement', 
                                'SqliMatchStatement',
                                'XssMatchStatement',
                                'GeoMatchStatement',
                                'IPSetReferenceStatement',
                                'RuleGroupReferenceStatement'
                            ]
        
        # Additional checks for managed rule groups
        if statement_type == 'ManagedRuleGroupStatement':
            vendor = statement.get('ManagedRuleGroupStatement', {}).get('VendorName', '')
            return vendor in ['AWS', 'Amazon']
        
        return statement_type in compliant_types
      
    #3. Fetching data from Cloudtrail logs
    def get_cloudtrail_security(self):
        """Get CloudTrail security events within date range"""
        try:
            cloudtrail = boto3.client('cloudtrail', region_name=REGION)
            trail_data = []
            
            # Make dates timezone-aware for comparison
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            trails = AWSResponse(cloudtrail.describe_trails())
            for trail in trails.data.get('trailList', []):
                status = AWSResponse(cloudtrail.get_trail_status(Name=trail.get('TrailARN')))
                
                # Get recent events from this trail to check activity
                try:
                    events = AWSResponse(cloudtrail.lookup_events(
                        StartTime=start_date_aware,
                        EndTime=end_date_aware,
                        MaxItems=5
                    ))
                    recent_events = events.data.get('Events', [])
                except Exception:
                    recent_events = []
                
                trail_data.append({
                                    'name'                  : trail.get('Name'),
                                    'arn'                   : trail.get('TrailARN'),
                                    'is_logging'            : status.data.get('IsLogging'),
                                    'is_multi_region'       : trail.get('IsMultiRegionTrail'),
                                    'include_global_events' : trail.get('IncludeGlobalServiceEvents'),
                                    's3_bucket'             : trail.get('S3BucketName'),
                                    'kms_key_id'            : trail.get('KMSKeyId'),
                                    'log_file_validation'   : trail.get('LogFileValidationEnabled'),
                                    'recent_events_count'   : len(recent_events),
                                    'latest_delivery_time'  : status.data.get('LatestDeliveryTime'),
                                    'start_logging_time'    : status.data.get('StartLoggingTime'),
                                    'stop_logging_time'     : status.data.get('StopLoggingTime')
                                })
            return trail_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'cloudtrail': str(e)})
            return []

    #4. Fetching data from Secrets Manager
    def get_secrets_security(self):
        """Get Secrets Manager security information within date range"""
        try:
            secrets = boto3.client('secretsmanager', region_name=REGION)
            secrets_data = []
            
            # Make dates timezone-aware for comparison
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            secret_list = AWSResponse(secrets.list_secrets())
            for secret in secret_list.data.get('SecretList', []):
                created_date        = secret.get('CreatedDate')
                last_changed_date   = secret.get('LastChangedDate')
                last_accessed_date  = secret.get('LastAccessedDate')
                # Filter secrets created, changed, or accessed within date range

                secrets_data.append({
                    'name'                  : secret.get('Name'),
                    'arn'                   : secret.get('ARN'),
                    'description'           : secret.get('Description'),
                    'created_date'          : created_date,
                    'last_changed_date'     : last_changed_date,
                    'last_accessed_date'    : last_accessed_date,
                    'rotation_enabled'      : secret.get('RotationEnabled'),
                    'rotation_lambda_arn'   : secret.get('RotationLambdaARN'),
                    'kms_key_id'            : secret.get('KmsKeyId'),
                    'tags'                  : secret.get('Tags', [])
                })

            return secrets_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'secrets_manager': str(e)})
            return []

    #5. Fetching data from Certificate Manager
    def get_certificate_security(self):
        """Get Certificate Manager security information within date range"""
        try:
            acm = boto3.client('acm', region_name=REGION)
            cert_data = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            certificates = AWSResponse(acm.list_certificates())
            for cert in certificates.data.get('CertificateSummaryList', []):
                cert_details    = AWSResponse(acm.describe_certificate(CertificateArn=cert.get('CertificateArn')))
                cert_info       = cert_details.data.get('Certificate', {})
                
                created_at = cert_info.get('CreatedAt')
                issued_at = cert_info.get('IssuedAt')
                
                # Filter certificates created or issued within date range
                #if (created_at and start_date_aware <= created_at <= end_date_aware) or (issued_at and start_date_aware <= issued_at <= end_date_aware):
                    
                cert_data.append({
                                    'arn'                       : cert.get('CertificateArn'),
                                    'domain_name'               : cert.get('DomainName'),
                                    'subject_alternative_names' : cert_info.get('SubjectAlternativeNames', []),
                                    'status'                    : cert_info.get('Status'),
                                    'type'                      : cert_info.get('Type'),
                                    'key_algorithm'             : cert_info.get('KeyAlgorithm'),
                                    'signature_algorithm'       : cert_info.get('SignatureAlgorithm'),
                                    'created_at'                : created_at,
                                    'issued_at'                 : issued_at,
                                    'not_before'                : cert_info.get('NotBefore'),
                                    'not_after'                 : cert_info.get('NotAfter'),
                                    'renewal_eligibility'       : cert_info.get('RenewalEligibility'),
                                    'key_usages'                : cert_info.get('KeyUsages', []),
                                    'extended_key_usages'       : cert_info.get('ExtendedKeyUsages', [])
                                })
            return cert_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'certificate_manager': str(e)})
            return []
    
    #6. Fetching data from Inspector
    def get_inspector(self):
        try:
            inspector = boto3.client('inspector2', region_name=REGION)
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            response            = AWSResponse(inspector.list_findings())
            filtered_findings   = []
            
            for finding in response.data.get('findings', []):
                first_observed  = finding.get('firstObservedAt')
                last_observed   = finding.get('lastObservedAt')
                updated_at      = finding.get('updatedAt')
                
                # Filter findings observed or updated within date range
                if (first_observed and start_date_aware <= first_observed <= end_date_aware) or \
                   (last_observed and start_date_aware <= last_observed <= end_date_aware) or \
                   (updated_at and start_date_aware <= updated_at <= end_date_aware):
                    
                    filtered_findings.append({
                                                'finding_arn'       : finding.get('findingArn'),
                                                'severity'          : finding.get('severity'),
                                                'status'            : finding.get('status'),
                                                'type'              : finding.get('type'),
                                                'title'             : finding.get('title'),
                                                'description'       : finding.get('description'),
                                                'first_observed_at' : first_observed,
                                                'last_observed_at'  : last_observed,
                                                'updated_at'        : updated_at
                                            })
            
            return filtered_findings
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'inspector': str(e)})
            return []

    #7. Fetching data from Trusted Advisor
    def get_trusted_advisor(self):
        try:
            support         = boto3.client('support', region_name='us-east-1')
            recommendations = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            checks = AWSResponse(support.describe_trusted_advisor_checks(language='en'))
            
            try:
                for check in checks.data.get('checks', []):
                    try:
                        result = AWSResponse(support.describe_trusted_advisor_check_result(
                            checkId=check.get('id'), language='en'
                        ))
                        
                        check_result        = result.data.get('result', {})
                        flagged_resources   = check_result.get('flaggedResources', [])
                        timestamp           = check_result.get('timestamp')
                        
                        # Filter by timestamp and only include checks with issues
                        if check_result.get('status') in ['warning', 'error'] and flagged_resources:
                            if timestamp and isinstance(timestamp, str):
                                try:
                                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    # If conversion fails, include the check anyway
                                    timestamp = None

                            if not timestamp or (start_date_aware and end_date_aware and timestamp and start_date_aware <= timestamp <= end_date_aware):
                                recommendations.append({
                                                        'check_name'                : check.get('name'),
                                                        'category'                  : check.get('category'),
                                                        'severity'                  : check_result.get('status'),
                                                        'recommendation'            : check.get('description'),
                                                        'affected_resources_count'  : len(flagged_resources),
                                                        'potential_savings'         : check_result.get('categorySpecificSummary', {}).get('costOptimizing', {}).get('estimatedMonthlySavings'),
                                                        'timestamp'                 : timestamp
                                                    })
                    except Exception as e:
                        print(f"Error processing Trusted Advisor check {check.get('id', 'unknown')}: {str(e)}")
                        continue

            except ClientError as e:
               raise e                    
            
            self.data.set_data(attr=AWSResourceType.TRUSTED_ADVISOR, data=recommendations)
            self.set_log(def_type=AWSResourceType.TRUSTED_ADVISOR, status="Pass")
            return recommendations
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.TRUSTED_ADVISOR, status="Fail", value={'trusted_advisor': str(e)})
            return []

    #8. Fetching data from Application Signals
    def get_application_signals(self):
        try:
            signals                             = boto3.client('application-signals', region_name=REGION)
            start_date_aware, end_date_aware    = self._get_timezone_aware_dates()
            
            # Application Signals has a 24-hour limit, so adjust the time range
            if start_date_aware and end_date_aware:
                time_diff = end_date_aware - start_date_aware

                if time_diff.total_seconds() > 24 * 3600:  # More than 24 hours

                    end_date_aware      = datetime.now(timezone.utc)
                    start_date_aware    = end_date_aware - timedelta(hours=23)  # 23 hours to be safe
            
            # Use list_services with proper parameters
            response = AWSResponse(signals.list_services(
                StartTime=start_date_aware,
                EndTime=end_date_aware,
                MaxResults=100
            ))
            
            result  = [{
                        'service_name'      : service.get('ServiceName'),
                        'namespace'         : service.get('Namespace'),
                        'key_attributes'    : service.get('KeyAttributes', {}),
                        'attribute_map'     : service.get('AttributeMap', {}),
                        'metric_references' : service.get('MetricReferences', [])
                    } for service in response.data.get('ServiceSummaries', [])]

            self.data.set_data(attr=AWSResourceType.APPLICATION, data=result)
            self.set_log(def_type=AWSResourceType.APPLICATION, status="Pass")
            return result
        
        except Exception as e:
            self.set_log(def_type=AWSResourceType.APPLICATION, status="Fail", value={'application_signals': str(e)})
            return []

    #9. Fetching Data from Resilience Hub
    def get_resilience_hub_apps(self):
        try:
            resilience  = boto3.client('resiliencehub', region_name=REGION)
            response    = AWSResponse(resilience.list_apps())
            apps_data   = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            for app in response.data.get('appSummaries', []):
                creation_time = app.get('creationTime')
                last_assessment_time = app.get('lastAssessmentTime')
                
                # Filter apps created or assessed within date range
                if (creation_time and start_date_aware <= creation_time <= end_date_aware) or \
                   (last_assessment_time and start_date_aware <= last_assessment_time <= end_date_aware):
                    
                    app_arn     = app.get('appArn') #earlier was appArn
                    app_data    = {
                                    'app_arn'               : app_arn,
                                    'name'                  : app.get('name'),
                                    'description'           : app.get('description'),
                                    'creation_time'         : creation_time,
                                    'last_assessment_time'  : last_assessment_time,
                                    'compliance_status'     : app.get('complianceStatus'),
                                    'resiliency_score'      : app.get('resiliencyScore'),
                                    'status'                : app.get('status'),
                                    'rpo'                   : None,
                                    'rto'                   : None,
                                    'last_drill'            : None,
                                    'cost'                  : None
                                }
                    
                    try:
                        # Get app details for RPO/RTO
                        app_details = AWSResponse(resilience.describe_app(appArn=app_arn))
                        policy      = app_details.data.get('app', {}).get('resiliencyPolicyArn')
                        if policy:
                            policy_details  = AWSResponse(resilience.describe_resiliency_policy(policyArn=policy))
                            policy_data     = policy_details.data.get('policy', {}).get('policy', {})
                            if policy_data:
                                app_data['rpo'] = policy_data.get('AZ', {}).get('rpoInSecs')
                                app_data['rto'] = policy_data.get('AZ', {}).get('rtoInSecs')
                        
                        # Get last test recommendation
                        tests = AWSResponse(resilience.list_test_recommendations(appArn=app_arn))
                        if tests.data.get('testRecommendations'):
                            app_data['last_drill'] = tests.data['testRecommendations'][0].get('creationTime')
                        
                        # Get cost estimate
                        cost_estimate       = AWSResponse(resilience.describe_app_version_resources_resolution_status(appArn=app_arn, appVersion='release'))
                        app_data['cost']    = cost_estimate.data.get('costEstimate', {}).get('cost')
                        
                    except Exception as e:
                        print(f"Error getting additional app details for {app_arn}: {str(e)}")
                    
                    apps_data.append(app_data)

            self.data.set_data(attr=AWSResourceType.RESILIENCE_HUB, data=apps_data)
            self.set_log(def_type=AWSResourceType.RESILIENCE_HUB, status="Pass")
            return apps_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.RESILIENCE_HUB, status="Fail", value={'resilience_hub': str(e)})
            return []

    #10. Fetching Data from AWS Health
    def get_health(self):
        try:
            health      = boto3.client('health', region_name='us-east-1')  # Health is global
            health_data = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            # Get health events within date range
            response = AWSResponse(health.describe_events(
                filter={
                    'startTimes': [
                        {
                            'from': start_date_aware,
                            'to': end_date_aware
                        }
                    ]
                }
            ))
            
            for event in response.data.get('events', []):
                health_data.append({
                                    'arn'                   : event.get('arn'),
                                    'service'               : event.get('service'),
                                    'event_type_code'       : event.get('eventTypeCode'),
                                    'event_type_category'   : event.get('eventTypeCategory'),
                                    'region'                : event.get('region'),
                                    'availability_zone'     : event.get('availabilityZone'),
                                    'start_time'            : event.get('startTime'),
                                    'end_time'              : event.get('endTime'),
                                    'last_updated_time'     : event.get('lastUpdatedTime'),
                                    'status_code'           : event.get('statusCode'),
                                    'event_scope_code'      : event.get('eventScopeCode')
                                })
            
            self.data.set_data(attr=AWSResourceType.HEALTH, data=health_data)
            self.set_log(def_type=AWSResourceType.HEALTH, status="Pass")
            return health_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.HEALTH, status="Fail", value={'health': str(e)})
            return []

    #11. Fetching Data from AWS Marketplace
    def get_marketplace(self):
        try:
            # Use only valid marketplace services
            marketplace_entitlement = boto3.client('marketplace-entitlement', region_name=REGION)
            ce_client               = boto3.client('ce')  # Cost Explorer for marketplace costs
            
            marketplace_data                = []
            start_date_aware, end_date_aware= self._get_timezone_aware_dates()
            
            try:
                # Get marketplace costs from Cost Explorer
                cost_response = AWSResponse(ce_client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date_aware.strftime('%Y-%m-%d') if start_date_aware else '',
                        'End': end_date_aware.strftime('%Y-%m-%d') if end_date_aware else ''
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                    ],
                    Filter={
                        'Dimensions': {
                            'Key': 'SERVICE',
                            'Values': ['AWS Marketplace']
                        }
                    }
                ))
                
                total_cost = 0
                daily_costs = []
                
                for result in cost_response.data.get('ResultsByTime', []):
                    period_start = result.get('TimePeriod', {}).get('Start')
                    period_cost = 0
                    
                    for group in result.get('Groups', []):
                        if 'AWS Marketplace' in group.get('Keys', []):
                            cost_amount = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                            period_cost += cost_amount
                            total_cost  += cost_amount
                    
                    if period_cost > 0:
                        daily_costs.append({
                                                'date': period_start,
                                                'cost': period_cost
                                            })
                
                # Try to get entitlements (may fail if no marketplace products)
                try:
                    entitlements_response = AWSResponse(marketplace_entitlement.get_entitlements())
                    
                    for entitlement in entitlements_response.data.get('Entitlements', []):
                        marketplace_data.append({
                                                    'product_code'          : entitlement.get('ProductCode'),
                                                    'dimension'             : entitlement.get('Dimension'),
                                                    'customer_identifier'   : entitlement.get('CustomerIdentifier'),
                                                    'value'                 : entitlement.get('Value'),
                                                    'expiration_date'       : entitlement.get('ExpirationDate'),
                                                    'cost_consumed'         : total_cost,
                                                    'currency'              : 'USD',
                                                    'period_start'          : start_date_aware.strftime('%Y-%m-%d') if start_date_aware else '',
                                                    'period_end'            : end_date_aware.strftime('%Y-%m-%d') if end_date_aware else '',
                                                    'daily_costs'           : daily_costs,
                                                    'status'                : 'ACTIVE'
                                                })
                
                except Exception:
                    # If no entitlements but there are costs, create a generic entry
                    if total_cost > 0:
                        marketplace_data.append({
                                                    'product_code'          : 'MARKETPLACE_USAGE',
                                                    'product_name'          : 'AWS Marketplace Products',
                                                    'dimension'             : 'Usage',
                                                    'customer_identifier'   : None,
                                                    'value'                 : None,
                                                    'expiration_date'       : None,
                                                    'cost_consumed'         : total_cost,
                                                    'currency'              : 'USD',
                                                    'period_start'          : start_date_aware.strftime('%Y-%m-%d') if start_date_aware else '',
                                                    'period_end'            : end_date_aware.strftime('%Y-%m-%d') if end_date_aware else '',
                                                    'daily_costs'           : daily_costs,
                                                    'status'                : 'CONSUMED'
                                                })
            
            except Exception as e:
                print(f"Error getting marketplace costs: {str(e)}")
            
            self.data.set_data(attr=AWSResourceType.MARKETPLACE, data=marketplace_data)
            self.set_log(def_type=AWSResourceType.MARKETPLACE, status="Pass")
            return marketplace_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.MARKETPLACE, status="Fail", value={'marketplace': str(e)})
            return []

    #12. Fetching Data from Compute Optimizer
    def get_compute_optimizer(self):
        try:
            recommendations = []
            compute_optimizer = boto3.client('compute-optimizer', region_name=REGION)
            
            def create_standard_recommendation(account_id, resource_type, resource_arn, resource_name, finding, **kwargs):
                return  {
                            'account_id'                    : account_id,
                            'resource_type'                 : resource_type,
                            'resource_arn'                  : resource_arn,
                            'resource_name'                 : resource_name,
                            'finding'                       : finding,
                            'current_instance_type'         : kwargs.get('current_instance_type'),
                            'current_memory_size'           : kwargs.get('current_memory_size'),
                            'current_volume_type'           : kwargs.get('current_volume_type'),
                            'current_volume_size'           : kwargs.get('current_volume_size'),
                            'recommended_instance_type'     : kwargs.get('recommended_instance_type'),
                            'recommended_memory_size'       : kwargs.get('recommended_memory_size'),
                            'recommended_volume_type'       : kwargs.get('recommended_volume_type'),
                            'recommended_volume_size'       : kwargs.get('recommended_volume_size'),
                            'savings_opportunity_percentage': kwargs.get('savings_opportunity_percentage'),
                            'estimated_monthly_savings_usd' : kwargs.get('estimated_monthly_savings_usd'),
                            'performance_risk'              : kwargs.get('performance_risk'),
                            'cpu_utilization_max'           : kwargs.get('cpu_utilization_max'),
                            'memory_utilization_avg'        : kwargs.get('memory_utilization_avg'),
                            'migration_effort'              : kwargs.get('migration_effort')
                        }
            
            # Get EC2 recommendations
            try:
                ec2_resp = AWSResponse(compute_optimizer.get_ec2_instance_recommendations())
                for rec in ec2_resp.data.get('instanceRecommendations', []):
                    recommendations.append(create_standard_recommendation(
                        self.account_id, 'EC2', rec.get('instanceArn'), rec.get('instanceName'),
                        rec.get('finding'),
                        current_instance_type=rec.get('currentInstanceType'),
                        recommended_instance_type=rec.get('recommendationOptions', [{}])[0].get('instanceType') if rec.get('recommendationOptions') else None,
                        savings_opportunity_percentage=rec.get('recommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('savingsOpportunityPercentage') if rec.get('recommendationOptions') else None,
                        estimated_monthly_savings_usd=rec.get('recommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('estimatedMonthlySavings', {}).get('value') if rec.get('recommendationOptions') else None,
                        performance_risk=rec.get('recommendationOptions', [{}])[0].get('performanceRisk') if rec.get('recommendationOptions') else None,
                        cpu_utilization_max=max([u.get('maximum', 0) for u in rec.get('utilizationMetrics', []) if u.get('name') == 'Cpu'], default=0),
                        memory_utilization_avg=sum([u.get('maximum', 0) for u in rec.get('utilizationMetrics', []) if u.get('name') == 'Memory']) / len([u for u in rec.get('utilizationMetrics', []) if u.get('name') == 'Memory']) if [u for u in rec.get('utilizationMetrics', []) if u.get('name') == 'Memory'] else 0
                    ))
            except Exception as e:
                print(f"Error getting EC2 recommendations: {str(e)}")
            
            # Get EBS recommendations
            try:
                ebs_resp = AWSResponse(compute_optimizer.get_ebs_volume_recommendations())
                for rec in ebs_resp.data.get('volumeRecommendations', []):
                    recommendations.append(create_standard_recommendation(
                        self.account_id, 'EBS', rec.get('volumeArn'), None,
                        rec.get('finding'),
                        current_volume_type=rec.get('currentConfiguration', {}).get('volumeType'),
                        current_volume_size=rec.get('currentConfiguration', {}).get('volumeSize'),
                        recommended_volume_type=rec.get('volumeRecommendationOptions', [{}])[0].get('configuration', {}).get('volumeType') if rec.get('volumeRecommendationOptions') else None,
                        recommended_volume_size=rec.get('volumeRecommendationOptions', [{}])[0].get('configuration', {}).get('volumeSize') if rec.get('volumeRecommendationOptions') else None,
                        savings_opportunity_percentage=rec.get('volumeRecommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('savingsOpportunityPercentage') if rec.get('volumeRecommendationOptions') else None,
                        estimated_monthly_savings_usd=rec.get('volumeRecommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('estimatedMonthlySavings', {}).get('value') if rec.get('volumeRecommendationOptions') else None,
                        performance_risk=rec.get('volumeRecommendationOptions', [{}])[0].get('performanceRisk') if rec.get('volumeRecommendationOptions') else None
                    ))
            except Exception as e:
                print(f"Error getting EBS recommendations: {str(e)}")
            
            # Get Lambda recommendations
            try:
                lambda_resp = AWSResponse(compute_optimizer.get_lambda_function_recommendations())
                for rec in lambda_resp.data.get('lambdaFunctionRecommendations', []):
                    recommendations.append(create_standard_recommendation(
                        self.account_id, 'Lambda', rec.get('functionArn'), rec.get('functionName'),
                        rec.get('finding'),
                        current_memory_size=rec.get('currentMemorySize'),
                        recommended_memory_size=rec.get('memorySizeRecommendationOptions', [{}])[0].get('memorySize') if rec.get('memorySizeRecommendationOptions') else None,
                        savings_opportunity_percentage=rec.get('memorySizeRecommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('savingsOpportunityPercentage') if rec.get('memorySizeRecommendationOptions') else None,
                        estimated_monthly_savings_usd=rec.get('memorySizeRecommendationOptions', [{}])[0].get('savingsOpportunity', {}).get('estimatedMonthlySavings', {}).get('value') if rec.get('memorySizeRecommendationOptions') else None
                    ))
            except Exception as e:
                print(f"Error getting Lambda recommendations: {str(e)}")
            
            self.data.set_data(attr=AWSResourceType.COMPUTE_OPTIMIZER, data=recommendations)
            self.set_log(def_type=AWSResourceType.COMPUTE_OPTIMIZER)
            return recommendations
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.COMPUTE_OPTIMIZER, status="Fail", value={'compute_optimizer': str(e)})
            return None

    #13. Fetching data from Service Resources
    def get_services_resources(self):
        try:
            resources = []
            
            def create_standard_resource(service_name, resource_type, resource_id, resource_name, region, availability_zone, state, **kwargs):
                return  {
                            'service_name'      : service_name,
                            'resource_type'     : resource_type,
                            'resource_id'       : resource_id,
                            'resource_name'     : resource_name,
                            'region'            : region,
                            'availability_zone' : availability_zone,
                            'state'             : state,
                            'instance_type'     : kwargs.get('instance_type'),
                            'vpc_id'            : kwargs.get('vpc_id'),
                            'engine'            : kwargs.get('engine'),
                            'instance_class'    : kwargs.get('instance_class'),
                            'multi_az'          : kwargs.get('multi_az'),
                            'size_gb'           : kwargs.get('size_gb'),
                            'volume_type'       : kwargs.get('volume_type'),
                            'creation_date'     : kwargs.get('creation_date'),
                            'type'              : kwargs.get('type'),
                            'scheme'            : kwargs.get('scheme'),
                            'instance_count'    : kwargs.get('instance_count'),
                            'min_size'          : kwargs.get('min_size'),
                            'max_size'          : kwargs.get('max_size'),
                            'available_ip_count': kwargs.get('available_ip_count')
                        }
            
            # EC2 Instances
            def fetch_ec2():
                ec2 = boto3.client('ec2', region_name=REGION)
                resp = AWSResponse(ec2.describe_instances())
                for reservation in resp.data.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        resources.append(create_standard_resource(
                            'EC2', 'Instance', instance.get('InstanceId'),
                            next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), ''),
                            REGION, instance.get('Placement', {}).get('AvailabilityZone'),
                            instance.get('State', {}).get('Name'),
                            instance_type=instance.get('InstanceType'),
                            vpc_id=instance.get('VpcId')
                        ))
            
            # RDS Instances
            def fetch_rds():
                rds = boto3.client('rds', region_name=REGION)
                resp = AWSResponse(rds.describe_db_instances())
                for db in resp.data.get('DBInstances', []):
                    resources.append(create_standard_resource(
                        'RDS', 'DBInstance', db.get('DBInstanceIdentifier'),
                        db.get('DBInstanceIdentifier'), REGION, db.get('AvailabilityZone'),
                        db.get('DBInstanceStatus'),
                        engine=db.get('Engine'),
                        instance_class=db.get('DBInstanceClass'),
                        multi_az=db.get('MultiAZ')
                    ))
            
            # EBS Volumes
            def fetch_ebs():
                ec2 = boto3.client('ec2', region_name=REGION)
                resp = AWSResponse(ec2.describe_volumes())
                for volume in resp.data.get('Volumes', []):
                    resources.append(create_standard_resource(
                        'EBS', 'Volume', volume.get('VolumeId'),
                        next((tag['Value'] for tag in volume.get('Tags', []) if tag['Key'] == 'Name'), ''),
                        REGION, volume.get('AvailabilityZone'), volume.get('State'),
                        size_gb=volume.get('Size', 0),
                        volume_type=volume.get('VolumeType')
                    ))
            
            # S3 Buckets
            def fetch_s3():
                s3 = boto3.client('s3', region_name=REGION)
                resp = AWSResponse(s3.list_buckets())
                for bucket in resp.data.get('Buckets', []):
                    resources.append(create_standard_resource(
                        'S3', 'Bucket', bucket.get('Name'), bucket.get('Name'),
                        REGION, None, 'Active',
                        creation_date=bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                    ))
            
            # Load Balancers
            def fetch_elb():
                elb = boto3.client('elbv2', region_name=REGION)
                resp = AWSResponse(elb.describe_load_balancers())
                for lb in resp.data.get('LoadBalancers', []):
                    az_list = [az.get('ZoneName') for az in lb.get('AvailabilityZones', [])]
                    resources.append(create_standard_resource(
                        'ELB', 'LoadBalancer', lb.get('LoadBalancerName'),
                        lb.get('LoadBalancerName'), REGION, ','.join(az_list),
                        lb.get('State', {}).get('Code'),
                        type=lb.get('Type'),
                        scheme=lb.get('Scheme')
                    ))
            
            # Auto Scaling Groups
            def fetch_asg():
                asg = boto3.client('autoscaling', region_name=REGION)
                resp = AWSResponse(asg.describe_auto_scaling_groups())
                for group in resp.data.get('AutoScalingGroups', []):
                    resources.append(create_standard_resource(
                        'AutoScaling', 'AutoScalingGroup', group.get('AutoScalingGroupName'),
                        group.get('AutoScalingGroupName'), REGION,
                        ','.join(group.get('AvailabilityZones', [])),
                        'Active' if group.get('Instances') else 'Inactive',
                        instance_count=len(group.get('Instances', [])),
                        min_size=group.get('MinSize'),
                        max_size=group.get('MaxSize')
                    ))
            
            # Subnets
            def fetch_subnets():
                ec2 = boto3.client('ec2', region_name=REGION)
                resp = AWSResponse(ec2.describe_subnets())
                for subnet in resp.data.get('Subnets', []):
                    resources.append(create_standard_resource(
                        'VPC', 'Subnet', subnet.get('SubnetId'),
                        next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), ''),
                        REGION, subnet.get('AvailabilityZone'), subnet.get('State'),
                        available_ip_count=subnet.get('AvailableIpAddressCount', 0),
                        vpc_id=subnet.get('VpcId')
                    ))
            
            # Lambda Functions
            def fetch_lambda():
                result = []
                lambda_client = boto3.client('lambda', region_name=REGION)
                paginator = lambda_client.get_paginator('list_functions')
                for page in paginator.paginate():
                    for func in page.get('Functions', []):
                        vpc_config = func.get('VpcConfig', {})
                        vpc_id = vpc_config.get('VpcId', '') if vpc_config else ''

                        result.append(create_standard_resource(
                            service_name='Lambda', 
                            resource_type='Function', 
                            resource_id=func.get('FunctionArn'),
                            resource_name=func.get('FunctionName'), 
                            region=REGION,
                            availability_zone='Generic',
                            state=func.get('State'),
                            instance_type=func.get('Runtime'),
                            vpc_id=vpc_id,
                            engine=func.get('Runtime'),
                            instance_class="",
                            multi_az=True,
                            size_gb=func.get('MemorySize', 128)/1024,
                            volume_type="EphemeralStorage",
                            creation_date=func.get('LastModified'),
                            type=func.get('PackageType'),
                            scheme=func.get('Architectures', ['x86_64'])[0],
                            instance_count=1,
                            min_size="",
                            max_size=func.get('EphemeralStorage', {}).get('Size', 512),
                            available_ip_count=None
                        ))
                return result

            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    executor.submit(fetch_ec2),
                    executor.submit(fetch_rds),
                    executor.submit(fetch_ebs),
                    executor.submit(fetch_s3),
                    executor.submit(fetch_elb),
                    executor.submit(fetch_asg),
                    executor.submit(fetch_subnets),
                    executor.submit(fetch_lambda)
                ]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        resources.extend(result)
            
            self.data.set_data(attr=AWSResourceType.SERVICE_RESOURCES, data=resources)
            self.set_log(def_type=AWSResourceType.SERVICE_RESOURCES)
            
            return resources
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SERVICE_RESOURCES, status="Fail", value={'service_resources': str(e)})
            return None

    #14. Fetching Inventory from Config
    # REMOVED:get_config_resource_inventory()  as it replicates the service_resources
    #15. Fetching support tickets raised
    def get_support_tickets(self):
        try:
            if not self.get_date():
                return None
                
            support_client = boto3.client('support', region_name='us-east-1')  # Support API only available in us-east-1
            
            tickets = []
            paginator = support_client.get_paginator('describe_cases')
            
            for page in paginator.paginate():
                for case in page.get('cases', []):
                    time_created = case.get('timeCreated')
                    
                    # Filter by date range if time_created exists
                    if time_created and self.start_date <= time_created.replace(tzinfo=None) <= self.end_date:
                        tickets.append({
                            'case_id': case.get('caseId'),
                            'display_id': case.get('displayId'),
                            'subject': case.get('subject'),
                            'status': case.get('status'),
                            'severity_code': case.get('severityCode'),
                            'service_code': case.get('serviceCode'),
                            'category_code': case.get('categoryCode'),
                            'time_created': time_created,
                            'submitted_by': case.get('submittedBy'),
                            'language': case.get('language', 'en'),
                            'date_from': self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
                            'date_to': self.end_date.strftime('%Y-%m-%d') if self.end_date else ''
                        })
            
            support_data = {
                'date_from': self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
                'date_to': self.end_date.strftime('%Y-%m-%d') if self.end_date else '',
                'total_tickets': len(tickets),
                'tickets': tickets
            }
            
            self.data.set_data(attr=AWSResourceType.SUPPORT_TICKETS, data=tickets)
            self.set_log(def_type=AWSResourceType.SUPPORT_TICKETS)
            return tickets
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SUPPORT_TICKETS, status="Fail", value={'support_tickets': str(e)})
            return None
    
    #16. Fetching RI/SP Daily Savings
    def get_ri_sp_savings(self):
        try:
            ce_client       = boto3.client('ce', region_name=REGION)
            daily_savings   = []
            
            start_date_aware, end_date_aware    = self._get_timezone_aware_dates()
            start_str                           = start_date_aware.strftime('%Y-%m-%d') if start_date_aware else ''
            end_str                             = end_date_aware.strftime('%Y-%m-%d') if end_date_aware else ''
            
            # Helper functions for parallel execution
            def get_ec2_ris():
                ri_details = {}
                try:
                    ec2     = boto3.client('ec2', region_name=REGION)
                    ec2_ris = ec2.describe_reserved_instances(Filters=[{'Name': 'state', 'Values': ['active']}])
                    for ri in ec2_ris.get('ReservedInstances', []):
                        ri_details[ri.get('ReservedInstancesId')] = {
                                                                        'service'       : 'Amazon EC2',
                                                                        'instance_type' : ri.get('InstanceType'),
                                                                        'instance_count': ri.get('InstanceCount'),
                                                                        'date_from'     : ri.get('Start'),
                                                                        'date_to'       : ri.get('End'),
                                                                        'offering_type' : ri.get('OfferingType')
                                                                    }
                except Exception as e:
                    self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={'ri_sp_savings': f'Error getting EC2 RIs - {str(e)}'})
                    print(f"Error getting EC2 RIs: {str(e)}")
                return ri_details
            
            def get_rds_ris():
                ri_details = {}
                try:
                    rds     = boto3.client('rds', region_name=REGION)
                    rds_ris = rds.describe_reserved_db_instances()
                    for ri in rds_ris.get('ReservedDBInstances', []):
                        ri_details[ri.get('ReservedDBInstanceId')] ={
                                                                        'service'       : 'Amazon RDS',
                                                                        'instance_type' : ri.get('DBInstanceClass'),
                                                                        'instance_count': ri.get('DBInstanceCount'),
                                                                        'date_from'     : ri.get('StartTime'),
                                                                        'offering_type' : ri.get('OfferingType')
                                                                    }
                except Exception as e:
                    self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={'ri_sp_savings': f'Error getting RDS RIs - {str(e)}'})
                    print(f"Error getting RDS RIs: {str(e)}")
                return ri_details
            
            def get_savings_plans():
                sp_details = {}
                try:
                    savingsplans    = boto3.client('savingsplans', region_name=REGION)
                    sps             = savingsplans.describe_savings_plans()
                    for sp in sps.get('savingsPlans', []):
                        sp_id               = sp.get('savingsPlanId')
                        sp_details[sp_id]   = {
                                                'savings_plan_type' : sp.get('savingsPlanType'),
                                                'date_from'         : sp.get('start'),
                                                'date_to'           : sp.get('end')
                                              }
                except Exception as e:
                    self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={'ri_sp_savings': f'Error getting Savings Plans - {str(e)}'})
                    print(f"Error getting Savings Plans: {str(e)}")
                return sp_details
            
            def get_ri_utilization(subscription_id, details):
                results = []
                try:
                    ri_util = ce_client.get_reservation_utilization(
                        TimePeriod  = {'Start': start_str, 'End': end_str},
                        Granularity = 'DAILY',
                        Filter      = {'Dimensions': {'Key': 'SUBSCRIPTION_ID', 'Values': [subscription_id]}}
                    )
                    
                    for time_period in ri_util.get('UtilizationsByTime', []):
                        util = time_period.get('Total', {})
                        if float(util.get('UtilizationPercentage', '0')) > 0:
                            results.append({
                                            'date'                  : time_period.get('TimePeriod', {}).get('Start'),
                                            'reservation_type'      : 'Reserved Instance',
                                            'subscription_id'       : subscription_id,
                                            'service'               : details.get('service'),
                                            'instance_type'         : details.get('instance_type'),
                                            'instance_count'        : details.get('instance_count'),
                                            'utilization_percentage': round(float(util.get('UtilizationPercentage', '0')), 2),
                                            'on_demand_cost'        : round(float(util.get('OnDemandCostOfRIHoursUsed', '0')), 2),
                                            'reservation_cost'      : round(float(util.get('TotalAmortizedFee', '0')), 2),
                                            'net_savings'           : round(float(util.get('NetRISavings', '0')), 2),
                                            'date_from'             : details.get('date_from'),
                                            'date_to'               : details.get('date_to'),
                                            'offering_type'         : details.get('offering_type')
                                        })
                except Exception as e:
                    if 'DataUnavailableException' not in str(e):
                        self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={f'ri_sp_savings': f'Error getting RI util for {subscription_id} - {str(e)}'})
                        print(f"Error getting RI util for {subscription_id}: {str(e)}")
                return results
            
            def get_sp_utilization(sp_id, details):
                results = []
                try:
                    sp_util = ce_client.get_savings_plans_utilization(
                        TimePeriod  = {'Start': start_str, 'End': end_str},
                        Granularity = 'DAILY',
                        Filter      = {'Dimensions': {'Key': 'SAVINGS_PLAN_ARN', 'Values': [sp_id]}}
                    )
                    
                    for time_period in sp_util.get('SavingsPlansUtilizationsByTime', []):
                        total = time_period.get('Total', {})
                        if total:
                            util = total.get('Utilization', {})
                            savings = total.get('Savings', {})
                            results.append({
                                                'date'                  : time_period.get('TimePeriod', {}).get('Start'),
                                                'reservation_type'      : 'Savings Plan',
                                                'subscription_id'       : sp_id,
                                                'service'               : 'AWS Savings Plans',
                                                'instance_type'         : details.get('savings_plan_type'),
                                                'utilization_percentage': round(float(util.get('UtilizationPercentage', '0')), 2),
                                                'on_demand_cost'        : round(float(savings.get('OnDemandCostEquivalent', '0')), 2),
                                                'reservation_cost'      : round(float(util.get('UsedCommitment', '0')), 2),
                                                'net_savings'           : round(float(savings.get('NetSavings', '0')), 2),
                                                'date_from'             : details.get('date_from'),
                                                'date_to'               : details.get('date_to')
                                            })
                except Exception as e:
                    if 'DataUnavailableException' not in str(e):
                        self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={f'ri_sp_savings': f'Error getting RI util for {sp_id} - {str(e)}'})
                        print(f"Error getting SP util for {sp_id}: {str(e)}")
                return results
            
            # Step 1: Get RI and SP details in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                ec2_future  = executor.submit(get_ec2_ris)
                rds_future  = executor.submit(get_rds_ris)
                sp_future   = executor.submit(get_savings_plans)
                
                ec2_ris     = ec2_future.result()
                rds_ris     = rds_future.result()
                sp_details  = sp_future.result()
            
            # Combine RI details
            ri_details = {**ec2_ris, **rds_ris}
            
            # Step 2: Get utilization for all RIs in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                ri_futures = [executor.submit(get_ri_utilization, sub_id, details) 
                             for sub_id, details in ri_details.items()]
                
                for future in as_completed(ri_futures):
                    try:
                        results = future.result()
                        daily_savings.extend(results)
                    except Exception as e:
                        self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={f'ri_sp_savings': f'Error processing RI future - {str(e)}'})
                        print(f"Error processing RI future: {str(e)}")
            
            # Step 3: Get utilization for all SPs in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                sp_futures = [executor.submit(get_sp_utilization, sp_id, details) 
                             for sp_id, details in sp_details.items()]
                
                for future in as_completed(sp_futures):
                    try:
                        results = future.result()
                        daily_savings.extend(results)
                    except Exception as e:
                        self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={f'ri_sp_savings': f'Error processing SP future - {str(e)}'})
                        print(f"Error processing SP future: {str(e)}")
            
            self.data.set_data(attr=AWSResourceType.RI_SP_SAVINGS, data=daily_savings)
            self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Pass")
            return daily_savings
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.RI_SP_SAVINGS, status="Fail", value={'ri_sp_savings': str(e)})
            return []



def get_data(interval="DAILY", start_date=None, end_date=None):
    start_time      = time.time()
    process_times   = {}
    
    sts_client      = boto3.client('sts')
    identity        = AWSResponse(sts_client.get_caller_identity())
    account         = identity.data['Account']
    
    aws             = AWSResourceManager(account_id=account, interval=interval, start_date=start_date, end_date=end_date, region=REGION)
    
    def timed_call(name, func):
        step_start          = time.time()
        func()
        process_times[name] = round(time.time() - step_start, 2)
    
    # Run all data fetches in parallel
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
                    executor.submit(timed_call, 'account_details', aws.get_account_details): 'account_details',
                    executor.submit(timed_call, 'services', aws.get_services): 'services',
                    executor.submit(timed_call, 'config', aws.get_config): 'config',
                    executor.submit(timed_call, 'cost', aws.get_cost): 'cost',
                    executor.submit(timed_call, 'inventory', aws.get_inventory): 'inventory',
                    executor.submit(timed_call, 'security', aws.get_security): 'security',
                    executor.submit(timed_call, 'trusted_advisor', aws.get_trusted_advisor): 'trusted_advisor',
                    executor.submit(timed_call, 'resilience_hub', aws.get_resilience_hub_apps): 'resilience_hub',
                    executor.submit(timed_call, 'health', aws.get_health): 'health',
                    executor.submit(timed_call, 'compute_optimizer', aws.get_compute_optimizer): 'compute_optimizer',
                    executor.submit(timed_call, 'ri_sp_savings', aws.get_ri_sp_savings): 'ri_sp_savings',
                    executor.submit(timed_call, 'services_resources', aws.get_services_resources): 'services_resources',
                    executor.submit(timed_call, 'support_tickets', aws.get_support_tickets): 'support_tickets'
                  }
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in {futures[future]}: {e}")
    
    process_times['application_signals']    = 0
    process_times['marketplace']            = 0
    
    # Get all data
    step_start                      = time.time()
    data                            = aws.data.get_all_data()
    process_times['get_all_data']   = round(time.time() - step_start, 2)
    
    if data is None:
        data    = {
                    "account": {"account_id": account},
                    "error": "No data collected",
                    "timestamp": datetime.now().isoformat()
                  }
    
    step_start                      = time.time()
    result                          = upload_to_s3(data=data, account=account, end_date=end_date, interval=interval)
    process_times['upload_to_s3']   = round(time.time() - step_start, 2)
    
    total_time                      = round(time.time() - start_time, 2)
    process_times['total_time']     = total_time
    
    if isinstance(result, dict):
        result['processing_times'] = process_times
    
    return result

def load_current_data(interval="DAILY", end_date=None):
    start_time      = time.time()
    data            = get_data(interval=interval, end_date=end_date)
    processing_time = round(time.time() - start_time, 2)
    
    print(f"{TIMING} Current data load ({interval}) completed in {processing_time}s")
    
    # Add timing info to result if it's a dict
    if isinstance(data, dict) and 'processing_times' not in data:
        data['processing_times'] = {'total_time': processing_time}
    
    return data

def load_historical_data(start_date=None, end_date=None):
 
    overall_start_time = time.time()
    
    # Convert string dates to datetime objects
    def parse_date(date_str):
        if isinstance(date_str, str):
            try:
                # Parse format like "2-4-2025" (day-month-year)
                day, month, year = map(int, date_str.split('-'))
                return datetime(year, month, day)
            except:
                print(f"{ERROR} Invalid date format: {date_str}. Expected format: d-m-yyyy")
                return None
        return date_str
    
    # Set default dates
    if end_date:
        till_date = parse_date(end_date)
        if till_date is None:
            till_date = datetime.now()
    else:
        till_date = datetime.now()
    
    if start_date:
        start_date = parse_date(start_date)
        if start_date is None:
            start_date = datetime(till_date.year, 1, 1)
    else:
        start_date = datetime(till_date.year, 1, 1)  # January 1st of current year
    
    interval = "DAILY"
    
    print(f"{CALENDAR}  Processing daily data from {start_date.strftime('%d-%m-%Y')} to {till_date.strftime('%d-%m-%Y')}")

    current                 = start_date
    count                   = 0
    total_processing_time   = 0
    processing_times        = []
    
    while current <= till_date:
        formatted_date = current.strftime('%d-%m-%Y')
        day_start_time = time.time()
        
        try:
            interval_start          = time.time()
            data                    = get_data(interval=interval, end_date=current)
            interval_time           = round(time.time() - interval_start, 2)
            
            day_total_time          = round(time.time() - day_start_time, 2)
            total_processing_time   += day_total_time
            
            # Ensure data is a dict before accessing get method
            if isinstance(data, dict):
                processing_times.append({
                                            'date'              : formatted_date,
                                            'interval'          : interval,
                                            'processing_time'   : day_total_time,
                                            'details'           : data.get('processing_times', {})
                                        })
            else:
                processing_times.append({
                                            'date'              : formatted_date,
                                            'interval'          : interval,
                                            'processing_time'   : day_total_time,
                                            'details'           : {'error': 'No data returned'}
                                        })
            
            size = data.get('size', 'Unknown') if isinstance(data, dict) else 'Unknown'
            print(f"{SUCCESS} {interval} : {formatted_date} Loaded Size: {size} (took {interval_time}s)")

        except Exception as e:
            print(f"{ERROR} {interval} : {formatted_date} Not Loaded - {str(e)}")
            continue
        
        finally:
            # Move to next day
            current += timedelta(days=1)
            count   += 1

    overall_time    = round(time.time() - overall_start_time, 2)
    avg_time        = round(total_processing_time / count if count > 0 else 0, 2)
    
    print(f"Historical data processing complete:")
    print(f"{TIMING} Total time: {overall_time}s")
    print(f"{TIMING} Average time per day: {avg_time}s")
    print(f"{CALENDAR} Days processed: {count}")
    
    return  {
                "from"              : start_date.strftime('%d-%m-%Y'), 
                "to"                : till_date.strftime('%d-%m-%Y'), 
                "loaded"            : count,
                "total_time"        : overall_time,
                "avg_time"          : avg_time,
                "processing_times"  : processing_times
            }

def process_data_status(has_daily, has_monthly, has_history, daily_data, monthly_data, history_data, load_time=None):
    daily_status    = f"{ERROR} No Daily Data"
    monthly_status  = f"{ERROR} No Monthly Data"
    history_status  = f"{ERROR} No Historical Data"
    
    if(has_daily and daily_data is not None):
        size            = daily_data.get('size', 'Unknown')
        daily_status    = f"{SUCCESS} Daily Data - {daily_data.get('path', 'Unknown')} Size: {size} Time: {load_time.get('daily_load_time', 0) if load_time else 0}s"

    if(has_monthly and monthly_data is not None):
        size            = monthly_data.get('size', 'Unknown')
        monthly_status  = f"{SUCCESS} Monthly Data - {monthly_data.get('path', 'Unknown')} Size: {size} Time: {load_time.get('daily_load_time', 0) if load_time else 0}s"

    if(has_history and history_data is not None):
        history_status = f"{SUCCESS} {history_data.get('loaded', 0)} Historical Data Loaded between {history_data.get('from', '')} - {history_data.get('to', '')} Time: {load_time.get('historical_load_time', 0) if load_time else 0}s"
    
    return [daily_status, monthly_status, history_status]

def lambda_handler(event=None, context=None):
    start_time = time.time()
    
    #1. AWS Boto3 Permission Test
    aws_permission  = AWSBoto3Permissions()
    
    has_daily       = False
    has_monthly     = False
    has_history     = False
    daily_data      = None
    monthly_data    = None
    history_data    = None
    status          = []
    timing_info     = {}

    if aws_permission.test():
        print("*"*15,"Connected","*"*15)
        if (event is not None and isinstance(event, dict) and "history" in event and (event['history'] == True or event['history'] == "True")):
            print("Loading Historical Data")
            history_start       = time.time()
            history_data_start  = event['start'] if("start" in event) else None
            history_data_end    = event['end'] if("end" in event) else None
            history_data        = load_historical_data(start_date=history_data_start, end_date=history_data_end)
            history_time        = round(time.time() - history_start, 2)
            has_history         = True

            timing_info['historical_load_time'] = history_time
            
            print(f"{SUCCESS if(has_history) else ERROR} History Data (took {history_time}s)")
        else:
            print(f"{INFO} Loading Daily Data")
            daily_start                     = time.time()
            daily_data                      = load_current_data(interval="DAILY")
            daily_time                      = round(time.time() - daily_start, 2)
            timing_info['daily_load_time']  = daily_time
            
            if(daily_data and daily_data is not None and 'path' in daily_data):
                has_daily = True
         
            status = process_data_status(has_daily, has_monthly, has_history, daily_data, monthly_data, history_data, load_time=timing_info)
            print(status[0])
            print(status[1])
            print(status[2])

        total_time                          = round(time.time() - start_time, 2)
        timing_info['total_execution_time'] = total_time

        print(f"{TIMING} Total execution time: {total_time}s")
        print("*"*14,"Disconnected","*"*13)
        
        # Add timing info to status response
        if isinstance(status, list):
            status.append(f"Execution time: {total_time}s")
        
        # If returning a dict instead of status list
        result =    {
                        'status': status,
                        'timing': timing_info
                    }
        
        return result

if __name__ == "__main__":
    
    """ 
    1. Run Historical Data Sets 
    - This will allow you to run data for a given period of time.
    """
    start   = None
    end     = None

    start   = "01-01-2026"  # January 14, 2026
    end     = "21-01-2026"  # January 21, 2026

    #result  = lambda_handler({"history":True, "start":start, "end":end})
    
    """ 2. Run Daily Data Sets """
    result  = lambda_handler({"history":False})

