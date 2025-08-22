"""ONLY FOR DEVELOPMENT REMOVE ON LAMBDA"""
""" from dotenv import load_dotenv, dotenv_values
load_dotenv()
 """
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
from datetime import datetime, timedelta, timezone

from calendar import monthrange
from enum import Enum

""" GLOBAL VARIABLES """
REGION      = os.environ.get("REGION", "ap-southeast-1")
BUCKET      = os.environ.get("BUCKET")
KMS_KEY_ID  = os.environ.get("ANALYTICS_KMS_KEY")

SUCCESS     = "🟢"  
FAIL        = "🟡"  
ERROR       = "🔴"  
INFO        = "🔵"  
TIMING      = "⏱️ "
CALENDAR    = "📅"

""" HELPER CLASSES """
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def upload_to_s3(account, data, interval, end_date):

    end_date    = datetime.now(timezone.utc) if not end_date else end_date
    s3          = boto3.client('s3')
    timestamp   = end_date.strftime("%H%M%S")
    filename    = f'data/{account}/{end_date.year}-{end_date.month:02d}-{end_date.day:02d}_{interval}.json'
    
    try:
        # Check if data is None and handle it
        if data is None:
            print("Warning: Data is None, creating empty JSON object")
            data = {"warning": "No data collected", "timestamp": datetime.now(timezone.utc).isoformat()}
        
        # Convert data to JSON string with datetime handling
        json_data = json.dumps(data, indent=4, cls=DateTimeEncoder)

        # Upload to S3 with KMS encryption
        put_params = {'Bucket': BUCKET, 'Key': filename, 'Body': json_data}

        if KMS_KEY_ID:
            put_params['ServerSideEncryption'] = 'aws:kms'
            put_params['SSEKMSKeyId'] = KMS_KEY_ID

        s3.put_object(**put_params)
        
        result = {
            "path": f"s3://{BUCKET}/{filename}",
            "date_added": str(end_date.date()),
            "account": account
        }
        
        return result
    
    except Exception as e:
        print(f"\n✗ Error writing to S3: {str(e)}")
        # Return a minimal result instead of None to avoid further errors
        return {
            "path": None,
            "date_added": str(end_date.date()) if end_date else None,
            "account": account,
            "error": str(e)
        }

"""  1. AWS RESPONSE MANAGER """
# a. AWS Resource Data - To ensure the data format is strictly governed
@dataclass
class AWSResourceData:
    """Data structure for AWS resource information"""
    account			: Dict[str, Any]        = field(default_factory=dict)
    config			: List[Dict[str, Any]]  = field(default_factory=list)
    service			: List[Dict[str, Any]]  = field(default_factory=list)
    cost			: List[Dict[str, Any]]  = field(default_factory=list)
    security		: List[Dict[str, Any]]  = field(default_factory=list)
    inventory		: List[Dict[str, Any]]  = field(default_factory=list)
    marketplace		: List[Dict[str, Any]]  = field(default_factory=list)
    trusted_advisor	: List[Dict[str, Any]]  = field(default_factory=list)
    health			: List[Dict[str, Any]]  = field(default_factory=list)
    application		: List[Dict[str, Any]]  = field(default_factory=list)
    resilience_hub	: List[Dict[str, Any]]  = field(default_factory=list)
    logs			: Dict[str, Any] = field(default_factory=dict)

class AWSResourceType(str, Enum):
    ACCOUNT         = "account"
    CONFIG          = "config"
    SERVICE         = "service"
    COST            = "cost"
    SECURITY        = "security"
    INVENTORY       = "inventory"
    MARKETPLACE     = "marketplace"
    TRUSTED_ADVISOR = "trusted_advisor"
    HEALTH          = "health"
    APPLICATION     = "application"
    RESILIENCE_HUB  = "resilience_hub"
    LOGS            = "logs"

# b. AWS Resource Interface - To ensure the data format is strictly governed
class AWSResourceInterface:
    def __init__(self):
        self.data = AWSResourceData()

    def set_data(self, attr: AWSResourceType, data: Dict[str, Any]):
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
        # Get current date and 30 days ago for CE
        self.end_date 		= datetime.now(timezone.utc)
        self.start_date 	= self.end_date - timedelta(days=30)
        self.aws_services 	= {
            "sts": {
                "name": "STS",
                "client": boto3.client("sts"),
                "action": "get_caller_identity",
                "params": params,
                "status": False,
            },
            "account_contact": {
                "name": "Account Contact",
                "client": boto3.client("account"),
                "action": "get_contact_information",
                "params": params,
                "status": False,
            },
            "account": {
                "name": "Account",
                "client": boto3.client("account"),
                "action": "get_account_information",
                "params": params,
                "status": False,
            },
            "ce": {
                "name": "Cost Explorer",
                "client": boto3.client("ce"),
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
            },
            "securityhub": {
                "name": "Security Hub",
                "client": boto3.client("securityhub", region_name=REGION),
                "action": "describe_hub",
                "params": params,
                "status": False,
            },
            "resiliencehub": {
                "name": "Resilience Hub",
                "client": boto3.client("resiliencehub", region_name=REGION),
                "action": "list_apps",
                "params": params,
                "status": False,
            },
            "config": {
                "name": "AWS Config",
                "client": boto3.client("config", region_name=REGION),
                "action": "describe_configuration_recorders",
                "params": params,
                "status": False,
            },
            "iam": {
                "name": "IAM",
                "client": boto3.client("iam"),
                "action": "list_users",
                "params": params,
                "status": False,
            },
            "ec2": {
                "name": "EC2",
                "client": boto3.client("ec2"),
                "action": "describe_regions",
                "params": params,
                "status": False,
            },
            "application-signals": {
                "name": "Application Signals",
                "client": boto3.client("application-signals", region_name=REGION),
                "action": "close",
                "params": params,
                "status": False,
            },
            "ssm": {
                "name": "Systems Manager",
                "client": boto3.client("ssm", region_name=REGION),
                "action": "describe_instance_information",
                "params": params,
                "status": False,
            },
            "inspector2": {
                "name": "Inspector",
                "client": boto3.client("inspector2", region_name=REGION),
                "action": "list_findings",
                "params": {},
                "status": False,
            },
            "wafv2": {
                "name": "WAF v2",
                "client": boto3.client("wafv2"),
                "action": "list_web_acls",
                "params": {"Scope": "REGIONAL"},
                "status": False,
            },
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
                                'message'			        : []
                            }
        # Default to 1 days ago since that's the maximum for detailed data
        #self.start_date = self.start_date.strftime('%Y-%m-%d')
        #self.end_date   = self.end_date.strftime('%Y-%m-%d')
        
    # Setting the Date Range
    def get_date(self):
        if not self.end_date:
            self.end_date = datetime.now()
    
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
            self.start_date = self.end_date - timedelta(days=self.days)
        
            # Default to 1 days ago since that's the maximum for detailed data
            
        #self.start_date = self.start_date.strftime('%Y-%m-%d')
        #self.end_date   = self.end_date.strftime('%Y-%m-%d')
        

        return True

    def _get_timezone_aware_dates(self):
        """Helper method to get timezone-aware start and end dates"""
        from datetime import timezone
        
        # Ensure dates are set
        if not self.start_date or not self.end_date:
            self.get_date()
        
        # Make dates timezone-aware for comparison
        start_date_aware = self.start_date.replace(tzinfo=timezone.utc) if self.start_date.tzinfo is None else self.start_date
        end_date_aware = self.end_date.replace(tzinfo=timezone.utc) if self.end_date.tzinfo is None else self.end_date
        
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
            'account_id': self.account_id,
            'account_name': acc.data.get("AccountName") if acc is not None else account_id,
            'account_email': None,
            'account_status': "ACTIVE",
            'account_arn': None,
            'joined_method': None,
            'joined_timestamp': acc.data.get("AccountCreatedDate") if acc is not None else None,
            'contact_info': {},
            'alternate_contacts': {}
        }

        # Get Contact Information
        try:
            contact_info = AWSResponse(account_client.get_contact_information())
            contact_data = contact_info.data.get('ContactInformation', {})
            result['contact_info'] = {field: contact_data.get(key) for field, key in [
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
                    alternate_contact = AWSResponse(account_client.get_alternate_contact(AlternateContactType=contact_type))
                    contact_data = alternate_contact.data.get('AlternateContact', {})
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
                TimePeriod  =   {'Start': self.start_date.strftime('%Y-%m-%d'), 'End': self.end_date.strftime('%Y-%m-%d')},
                Granularity =   self.interval,
                Metrics     =   ['UnblendedCost', 'UsageQuantity'],
                GroupBy     =   [{'Type': 'DIMENSION', 'Key': 'SERVICE'}, {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}],
                Filter      =   {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [self.account_id]}}
            ))

            aggregated_data = {}
            for result in response.data.get('ResultsByTime', []):
                time_period = result['TimePeriod']
                for group in result.get('Groups', []):
                    service, usage_type = group['Keys']
                    metrics     = group['Metrics']
                    cost        = float(metrics['UnblendedCost']['Amount'])
                    utilization = float(metrics['UsageQuantity']['Amount']) or None
                    
                    if service not in aggregated_data:
                        aggregated_data[service] = {
                            'service'       : service,
                            'date_from'     : time_period['Start'],
                            'date_to'       : time_period['End'],
                            'cost'          : cost,
                            'currency'      : metrics['UnblendedCost']['Unit'],
                            'utilization'   : utilization,
                            'utilization_unit'  : usage_type.split('-')[-1] if '-' in usage_type else None,
                            'usage_types'       : [usage_type]
                        }
                    else:
                        aggregated_data[service]['cost'] += cost
                        if utilization:
                            aggregated_data[service]['utilization'] = (aggregated_data[service]['utilization'] or 0) + utilization
                        if usage_type not in aggregated_data[service]['usage_types']:
                            aggregated_data[service]['usage_types'].append(usage_type)

            result_data = sorted(aggregated_data.values(), key=lambda x: x['cost'], reverse=True)

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
            non_compliant_rules = []
            total_rules = 0
            
            config_rules = AWSResponse(config_client.describe_config_rules())
            for rule in config_rules.data.get('ConfigRules', []):
                rule_name = rule.get('ConfigRuleName')
                total_rules += 1
                try:
                    compliance = AWSResponse(config_client.get_compliance_details_by_config_rule(
                        ConfigRuleName=rule_name,
                        ComplianceTypes=['NON_COMPLIANT']
                    ))
                    for result in compliance.data.get('EvaluationResults', []):
                        result_time = result.get('ResultRecordedTime')
                        start_date_aware, end_date_aware = self._get_timezone_aware_dates()
                        if result_time and start_date_aware <= result_time <= end_date_aware:
                            qualifier = result.get('EvaluationResultIdentifier', {}).get('EvaluationResultQualifier', {})
                            non_compliant_rules.append({
                                'rule_name'                 : rule_name,
                                'resource_id'               : qualifier.get('ResourceId'),
                                'resource_type'             : qualifier.get('ResourceType'),
                                'error_date'                : result_time.isoformat() if result_time else None,
                                'config_rule_invoked_time'  : result.get('ConfigRuleInvokedTime').isoformat() if result.get('ConfigRuleInvokedTime') else None
                            })
                except Exception as e:
                    print(f"Error checking rule {rule_name}: {str(e)}")
                    self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={f'rule_{rule_name}': str(e)})
            
            # Calculate compliance score
            non_compliant_count = len(set(rule['rule_name'] for rule in non_compliant_rules))
            compliance_score = ((total_rules - non_compliant_count) / max(total_rules, 1)) * 100
            
            config_data = {
                'date_from': self.start_date.strftime('%Y-%m-%d'),
                'date_to': self.end_date.strftime('%Y-%m-%d'),
                'compliance_score': round(compliance_score, 2),
                'total_rules': total_rules,
                'compliant_rules': total_rules - non_compliant_count,
                'non_compliant_rules': non_compliant_count,
                'non_compliant_resources': non_compliant_rules
            }
            
            self.data.set_data(attr=AWSResourceType.CONFIG, data=config_data)
            self.set_log(def_type=AWSResourceType.CONFIG)
            return config_data
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.CONFIG, status="Fail", value={'config': str(e)})
            return None

    #4. Fetching Cost Data
    def get_cost(self):
        try:
            if not self.get_date():
                return None
                
            ce_client = boto3.client('ce')
            start_date = self.start_date.strftime('%Y-%m-%d')
            end_date = self.end_date.strftime('%Y-%m-%d')
            account_filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [self.account_id]}}
            
            # Get current and previous costs
            current_costs = AWSResponse(ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity=self.interval,
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
                Filter=account_filter
            ))
            
            prev_start = (self.start_date - timedelta(days=self.days)).strftime('%Y-%m-%d')
            previous_costs = AWSResponse(ce_client.get_cost_and_usage(
                TimePeriod={'Start': prev_start, 'End': start_date},
                Granularity=self.interval,
                Metrics=['UnblendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}],
                Filter=account_filter
            ))
            
            # Calculate totals
            current_total = sum(float(group['Metrics']['UnblendedCost']['Amount'])
                               for result in current_costs.data['ResultsByTime']
                               for group in result['Groups'])
            
            previous_total = sum(float(group['Metrics']['UnblendedCost']['Amount'])
                                for result in previous_costs.data['ResultsByTime']
                                for group in result['Groups'])
            
            # Get top services and forecast
            top_services = []
            if current_costs.data['ResultsByTime']:
                latest_period = current_costs.data['ResultsByTime'][-1]
                top_services = [{'service': service['Keys'][0], 'cost': float(service['Metrics']['UnblendedCost']['Amount'])}
                               for service in sorted(latest_period['Groups'], 
                                                   key=lambda x: float(x['Metrics']['UnblendedCost']['Amount']), 
                                                   reverse=True)[:5]]
            
            forecast_data = []
            try:
                forecast_end = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                forecast = AWSResponse(ce_client.get_cost_forecast(
                    TimePeriod={'Start': end_date, 'End': forecast_end},
                    Metric='UNBLENDED_COST',
                    Granularity=self.interval,
                    Filter=account_filter
                ))
                forecast_data = [{'period': {'start': point['TimePeriod']['Start'], 'end': point['TimePeriod']['End']}, 
                                 'amount': float(point['MeanValue'])}
                                for point in forecast.data.get('ForecastResultsByTime', [])]
            except Exception as e:
                self.set_log(def_type=AWSResourceType.COST, status="Fail", value={'Forecast unavailable': str(e)})
            
            cost_difference = current_total - previous_total
            summary = {
                'account_id': self.account_id,
                'current_period_cost': current_total,
                'previous_period_cost': previous_total,
                'cost_difference': cost_difference,
                'cost_difference_percentage': (cost_difference / previous_total * 100) if previous_total > 0 else 0,
                'top_services': top_services,
                'period': {'start': start_date, 'end': end_date, 'granularity': self.interval},
                'forecast': forecast_data
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
            patch_response = AWSResponse(ssm.describe_instance_patches(
                InstanceId=instance_id
            ))
            
            for patch in patch_response.data.get('Patches', []):
                patches.append({
                    'instance_id': instance_id,
                    'title': patch.get('Title'),
                    'classification': patch.get('Classification'),
                    'severity': patch.get('Severity'),
                    'state': patch.get('State'),
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
                'instances': [],
                'applications': [],
                'patches': [],
                'services': [],
                'users': [],
                'processes': [],
                'network_ports': [],
                'certificates': []
            }
            
            instances = AWSResponse(ssm.describe_instance_information())
            
            for instance in instances.data.get('InstanceInformationList', []):
                instance_id = instance['InstanceId']
                
                # Add instance info
                security_inventory['instances'].append({
                    'instance_id': instance_id,
                    'platform': instance.get('PlatformName'),
                    'platform_version': instance.get('PlatformVersion'),
                    'agent_version': instance.get('AgentVersion'),
                    'last_ping': instance.get('LastPingDateTime'),
                    'computer_name': instance.get('ComputerName'),
                    'instance_type': instance.get('InstanceType')
                })
                
                # Get security-relevant inventory types (only supported ones)
                for inv_type, key in [
                    ('AWS:PatchSummary', 'patches')
                ]:
                    try:
                        resp = AWSResponse(ssm.get_inventory(
                            Filters=[{'Key': 'AWS:InstanceInformation.InstanceId', 'Values': [instance_id]}],
                            ResultAttributes=[{'TypeName': inv_type}]
                        ))
                        
                        for entity in resp.data.get('Entities', []):
                            for data_item in entity.get('Data', {}).values():
                                for item in data_item.get('Content', []):
                                    if inv_type == 'AWS:Application':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'name': item.get('Name'),
                                            'version': item.get('Version'),
                                            'publisher': item.get('Publisher')
                                        })
                                    elif inv_type == 'AWS:PatchSummary':
                                        detailed_patches = self.get_patch_details(instance_id)
                                        security_inventory['patches'].extend(detailed_patches)

                                    elif inv_type == 'AWS:Service':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'name': item.get('Name'),
                                            'status': item.get('Status'),
                                            'startup_type': item.get('StartType')
                                        })
                                    elif inv_type == 'Custom:Users':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'username': item.get('Username'),
                                            'is_admin': item.get('IsAdmin', False),
                                            'last_login': item.get('LastLogin')
                                        })
                                    elif inv_type == 'Custom:Processes':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'name': item.get('Name'),
                                            'path': item.get('ExecutablePath'),
                                            'user': item.get('User')
                                        })
                                    elif inv_type == 'Custom:NetworkPorts':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'port': item.get('Port'),
                                            'protocol': item.get('Protocol'),
                                            'state': item.get('State')
                                        })
                                    elif inv_type == 'Custom:Certificates':
                                        security_inventory[key].append({
                                            'instance_id': instance_id,
                                            'subject': item.get('Subject'),
                                            'issuer': item.get('Issuer'),
                                            'not_after': item.get('NotAfter'),
                                            'is_expired': item.get('IsExpired')
                                        })
                    except Exception as e:
                        print(f"Error processing inventory type {inv_type} for instance {instance_id}: {str(e)}")
                        continue
            
            self.data.set_data(attr=AWSResourceType.INVENTORY, data=security_inventory)
            self.set_log(def_type=AWSResourceType.INVENTORY)
            return security_inventory
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.INVENTORY, status="Fail", value={'inventory': str(e)})
            return None

    #6.Fetching Security data across Security hub, Guard Duty, IAM, KMS, WAF, Inspector, Trusted Advisor
    def get_security(self):
        try:
            result = {
                'security_hub'          : [],
                'guard_duty'            : [],
                'iam'                   : [],
                'kms'                   : [],
                'waf'                   : [],
                'waf_rules'             : [],
                'cloudtrail'            : [],
                'secrets_manager'       : [],
                'certificate_manager'   : [],
                'trusted_advisor'       : [],
                'inspector'             : []
            }
            
            # 1. Security Hub (existing)
            result['security_hub'] = self.get_security_hub()
            
            # 2. GuardDuty
            result['guard_duty'] = self.get_guard_duty_security()
            
            # 3. IAM Security
            #result['iam'] = self.get_iam_security()
            
            # 4. KMS Keys
            result['kms'] = self.get_kms_security()
            
            # 5. WAF Rules
            result['waf'] = self.get_waf_security()

            result['waf_rules'] = self.get_waf_rules()
            
            # 6. CloudTrail Events
            result['cloudtrail'] = self.get_cloudtrail_security()
            
            # 7. Secrets Manager
            result['secrets_manager'] = self.get_secrets_security()
            
            # 8. Certificate Manager
            result['certificate_manager'] = self.get_certificate_security()
            
            # 9. X Ray
            result['inspector'] = self.get_inspector()
            
            # 10. Trusted Advisor
            #result['trusted_advisor'] = self.get_trusted_advisor()
            
            
            
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
            next_token = None
            
            while True:
                params = {
                    'Filters': {
                        'CreatedAt'     : [{'Start': self.start_date.isoformat(), 'End': self.end_date.isoformat()}],
                        'AwsAccountId'  : [{'Value': self.account_id, 'Comparison': 'EQUALS'}],
                        'SeverityLabel': [
                        {'Value': 'CRITICAL', 'Comparison': 'EQUALS'},
                        {'Value': 'HIGH', 'Comparison': 'EQUALS'},
                        {'Value': 'MEDIUM', 'Comparison': 'EQUALS'},
                        {'Value': 'LOW', 'Comparison': 'EQUALS'}
                    ]
                    },
                    'MaxResults': 100
                }
                
                if next_token:
                    params['NextToken'] = next_token
            
                response = AWSResponse(securityhub.get_findings(**params))
                if response.status != 200:
                    return None
                
                for finding in response.data['Findings']:
                    generator_id = finding.get('GeneratorId', '')
                    service = generator_id.split('/')[0] if '/' in generator_id else 'Unknown'
                    generator = generator_id.split('/')[1].split('.')[0] if '/' in generator_id else 'Unknown'
                    
                    if service not in service_findings:
                        service_findings[service] = {
                            'service': service,
                            'total_findings': 0,
                            'severity_counts': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFORMATIONAL': 0},
                            'open_findings': 0,
                            'resolved_findings': 0,
                            'findings': []
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
                        'finding_id': finding.get('Id'),
                        'service': finding.get('Id').split("/")[1].split('.')[0] if finding.get('Id') and '/' in finding.get('Id') else 'Unknown',
                        'title': finding.get('Title'),
                        'description': finding.get('Description'),
                        'severity': severity,
                        'status': workflow_status or 'OPEN',
                        'resource_type': resource.get('Type'),
                        'resource_id': resource.get('Id'),
                        'created_at': finding.get('CreatedAt'),
                        'updated_at': finding.get('UpdatedAt'),
                        'recommendation': finding.get('Remediation', {}).get('Recommendation', {}).get('Text'),
                        'compliance_status': finding.get('Compliance', {}).get('Status'),
                        'region': finding.get('Region'),
                        'workflow_state': finding.get('Workflow', {}).get('Status', 'NEW'),
                        'record_state': finding.get('RecordState', 'ACTIVE'),
                        'product_name': finding.get('ProductName'),
                        'company_name': finding.get('CompanyName'),
                        'product_arn': finding.get('ProductArn'),
                        'generator_id': finding.get('GeneratorId'),
                        'generator': generator
                    })
            
                next_token = response.data.get('NextToken')
                if not next_token:
                    break
            
            result = sorted(service_findings.values(), key=lambda x: x['total_findings'], reverse=True)

            self.set_log(def_type=AWSResourceType.SECURITY)
            return result
            
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'security_hub': str(e)})
            return None

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
                            'Gte': int(self.start_date.timestamp() * 1000),  # Convert to milliseconds
                            'Lte': int(self.end_date.timestamp() * 1000)
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
                            'id': finding.get('Id'),
                            'type': finding.get('Type'),
                            'severity': finding.get('Severity'),
                            'title': finding.get('Title'),
                            'description': finding.get('Description'),
                            'created_at': finding.get('CreatedAt'),
                            'updated_at': finding.get('UpdatedAt'),
                            'confidence': finding.get('Confidence'),
                            'region': finding.get('Region')
                        })
            return findings
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'guard_duty': str(e)})
            return []

    #Getting IAM data
    def get_iam_security(self):
        """Get IAM security posture within date range"""
        try:
            from datetime import timezone
            iam = boto3.client('iam')
            iam_data = {
                'users': [],
                'roles': [],
                'policies': [],
                'access_keys': [],
                'mfa_devices': []
            }
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            # Get users with security details (filter by creation date)
            users = AWSResponse(iam.list_users())
            for user in users.data.get('Users', []):
                user_created        = user.get('CreateDate')
                password_last_used  = user.get('PasswordLastUsed')
                
                # Filter users created or with password used within date range
                if (user_created and start_date_aware <= user_created <= end_date_aware) or (password_last_used and start_date_aware <= password_last_used <= end_date_aware):
                    
                    username = user.get('UserName')
                    iam_data['users'].append({
                        'username': username,
                        'created_date': user.get('CreateDate'),
                        'password_last_used': password_last_used,
                        'mfa_enabled': len(AWSResponse(iam.list_mfa_devices(UserName=username)).data.get('MFADevices', [])) > 0,
                        'access_keys_count': len(AWSResponse(iam.list_access_keys(UserName=username)).data.get('AccessKeyMetadata', []))
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
                    key_details = AWSResponse(kms.describe_key(KeyId=key_id))
                    key_metadata = key_details.data.get('KeyMetadata', {})
                    creation_date = key_metadata.get('CreationDate')
                    
                    # Filter keys created within date range
                    if creation_date and self.start_date <= creation_date.replace(tzinfo=None) <= self.end_date:
                        kms_data.append({
                            'key_id': key_id,
                            'arn': key_metadata.get('Arn'),
                            'description': key_metadata.get('Description'),
                            'key_usage': key_metadata.get('KeyUsage'),
                            'key_state': key_metadata.get('KeyState'),
                            'creation_date': creation_date,
                            'enabled': key_metadata.get('Enabled'),
                            'key_rotation_enabled': AWSResponse(kms.get_key_rotation_status(KeyId=key_id)).data.get('KeyRotationEnabled', False)
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
                    region = 'us-east-1' if scope == 'CLOUDFRONT' else REGION
                    waf = boto3.client('wafv2', region_name=region)
                    
                    web_acls = AWSResponse(waf.list_web_acls(Scope=scope))
                    for acl in web_acls.data.get('WebACLs', []):
                        acl_details = AWSResponse(waf.get_web_acl(Name=acl.get('Name'), Scope=scope, Id=acl.get('Id')))
                        web_acl = acl_details.data.get('WebACL', {})
                        rules = web_acl.get('Rules', [])
                        
                        # Get resources and logging
                        try:
                            resources = AWSResponse(waf.list_resources_for_web_acl(
                                WebACLArn=web_acl.get('ARN'),
                                ResourceType='APPLICATION_LOAD_BALANCER' if scope == 'REGIONAL' else 'CLOUDFRONT'
                            )).data.get('ResourceArns', [])
                            logging_config = AWSResponse(waf.get_logging_configuration(ResourceArn=web_acl.get('ARN')))
                            logging_enabled, log_destination = True, logging_config.data.get('LoggingConfiguration', {}).get('LogDestinationConfigs', [])
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
                            'name': acl.get('Name'), 'id': acl.get('Id'), 'arn': web_acl.get('ARN'),
                            'scope': scope, 'description': acl.get('Description', ''),
                            'default_action': web_acl.get('DefaultAction'), 'rules_count': len(rules),
                            'capacity': web_acl.get('Capacity', 0),
                            'managed_rules_count': rule_types['managed'], 'custom_rules_count': rule_types['custom'],
                            'rate_limit_rules_count': rule_types['rate_limit'],
                            'associated_resources': resources, 'associated_resources_count': len(resources),
                            'logging_enabled': logging_enabled, 'log_destinations': log_destination,
                            'geo_blocking_enabled': len(blocked_countries) > 0, 'blocked_countries': blocked_countries,
                            'ip_sets': ip_sets, 'created_date': web_acl.get('CreationDate'),
                            'last_modified': web_acl.get('LastModifiedTime'), 'tags': web_acl.get('Tags', []),
                            'sampled_requests_enabled': any(rule.get('VisibilityConfig', {}).get('SampledRequestsEnabled', False) for rule in rules),
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
                    wafv2 = boto3.client('wafv2', region_name='us-east-1' if scope == 'CLOUDFRONT' else REGION)
                    web_acls = wafv2.list_web_acls(Scope=scope)['WebACLs']
                    
                    for acl in web_acls:
                        acl_details = wafv2.get_web_acl(
                            Name=acl['Name'], Scope=scope, Id=acl['Id']
                        )
                        
                        # Check ACL-level logging
                        try:
                            wafv2.get_logging_configuration(ResourceArn=acl_details['WebACL']['ARN'])
                            logging_enabled = True
                        except:
                            logging_enabled = False
                        
                        for rule in acl_details['WebACL']['Rules']:
                            statement = rule.get('Statement', {})
                            statement_type = list(statement.keys())[0] if statement else 'Unknown'
                            visibility = rule.get('VisibilityConfig', {})
                            
                            # Handle missing Action field - use OverrideAction if Action is missing
                            action = rule.get('Action')
                            if not action:
                                action = rule.get('OverrideAction', {'None': {}})
                            
                            # Analyze rule properties
                            is_managed = statement_type == 'ManagedRuleGroupStatement'
                            is_rate_limit = statement_type == 'RateBasedStatement'
                            has_geo_blocking = 'GeoMatchStatement' in str(statement)
                            has_sql_injection = 'SqliMatchStatement' in str(statement) or (
                                is_managed and 'SQLi' in statement.get('ManagedRuleGroupStatement', {}).get('Name', '')
                            )
                            has_xss_protection = 'XssMatchStatement' in str(statement) or (
                                is_managed and 'XSS' in statement.get('ManagedRuleGroupStatement', {}).get('Name', '')
                            )

                            waf_rules.append({
                                'web_acl_name': acl['Name'],
                                'rule_name': rule['Name'],
                                'priority': rule['Priority'],
                                'action': action,
                                'statement_type': statement_type,
                                'is_managed_rule': is_managed,
                                'is_custom_rule': not is_managed,
                                'rate_limit': is_rate_limit,
                                'logging_enabled': logging_enabled,
                                'geo_blocking': has_geo_blocking,
                                'sql_injection': has_sql_injection,
                                'sample_request_enabled': visibility.get('SampledRequestsEnabled', False),
                                'cloudwatch_enabled': visibility.get('CloudWatchMetricsEnabled', False),
                                'has_xss_protection': has_xss_protection,
                                'waf_version': 'v2',
                                'is_compliant': self._check_waf_rule_compliance(statement_type, statement),
                                'scope': scope
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
                            'web_acl_name': acl['Name'],
                            'rule_name': rule['Rule']['Name'],
                            'priority': rule_ref['Priority'],
                            'action': rule_ref['Action'],
                            'statement_type': 'WAFv1_Rule',
                            'is_managed_rule': False,
                            'is_custom_rule': True,
                            'rate_limit': False,
                            'logging_enabled': False,
                            'geo_blocking': False,
                            'sql_injection': False,
                            'sample_request_enabled': False,
                            'cloudwatch_enabled': False,
                            'has_xss_protection': False,
                            'waf_version': 'v1',
                            'is_compliant': False
                        })
            except Exception as e:
                print(f"WAF v1 also failed: {str(e)}")
        
        return waf_rules

    def _check_waf_rule_compliance(self, statement_type, statement):
        """Check if a WAF rule meets compliance requirements"""
        # Compliant rule types
        compliant_types = [
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
            from datetime import timezone
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
                    'name': trail.get('Name'),
                    'arn': trail.get('TrailARN'),
                    'is_logging': status.data.get('IsLogging'),
                    'is_multi_region': trail.get('IsMultiRegionTrail'),
                    'include_global_events': trail.get('IncludeGlobalServiceEvents'),
                    's3_bucket': trail.get('S3BucketName'),
                    'kms_key_id': trail.get('KMSKeyId'),
                    'log_file_validation': trail.get('LogFileValidationEnabled'),
                    'recent_events_count': len(recent_events),
                    'latest_delivery_time': status.data.get('LatestDeliveryTime'),
                    'start_logging_time': status.data.get('StartLoggingTime'),
                    'stop_logging_time': status.data.get('StopLoggingTime')
                })
            return trail_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'cloudtrail': str(e)})
            return []

    #4. Fetching data from Secrets Manager
    def get_secrets_security(self):
        """Get Secrets Manager security information within date range"""
        try:
            from datetime import timezone
            secrets = boto3.client('secretsmanager', region_name=REGION)
            secrets_data = []
            
            # Make dates timezone-aware for comparison
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            secret_list = AWSResponse(secrets.list_secrets())
            for secret in secret_list.data.get('SecretList', []):
                created_date = secret.get('CreatedDate')
                last_changed_date = secret.get('LastChangedDate')
                last_accessed_date = secret.get('LastAccessedDate')
                
                # Filter secrets created, changed, or accessed within date range
                if (created_date and start_date_aware <= created_date <= end_date_aware) or \
                   (last_changed_date and start_date_aware <= last_changed_date <= end_date_aware) or \
                   (last_accessed_date and start_date_aware <= last_accessed_date <= end_date_aware):
                    
                    secrets_data.append({
                        'name': secret.get('Name'),
                        'arn': secret.get('ARN'),
                        'description': secret.get('Description'),
                        'created_date': created_date,
                        'last_changed_date': last_changed_date,
                        'last_accessed_date': last_accessed_date,
                        'rotation_enabled': secret.get('RotationEnabled'),
                        'rotation_lambda_arn': secret.get('RotationLambdaARN'),
                        'kms_key_id': secret.get('KmsKeyId'),
                        'tags': secret.get('Tags', [])
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
                cert_details = AWSResponse(acm.describe_certificate(CertificateArn=cert.get('CertificateArn')))
                cert_info = cert_details.data.get('Certificate', {})
                
                created_at = cert_info.get('CreatedAt')
                issued_at = cert_info.get('IssuedAt')
                
                # Filter certificates created or issued within date range
                if (created_at and start_date_aware <= created_at <= end_date_aware) or \
                   (issued_at and start_date_aware <= issued_at <= end_date_aware):
                    
                    cert_data.append({
                        'arn': cert.get('CertificateArn'),
                        'domain_name': cert.get('DomainName'),
                        'subject_alternative_names': cert_info.get('SubjectAlternativeNames', []),
                        'status': cert_info.get('Status'),
                        'type': cert_info.get('Type'),
                        'key_algorithm': cert_info.get('KeyAlgorithm'),
                        'signature_algorithm': cert_info.get('SignatureAlgorithm'),
                        'created_at': created_at,
                        'issued_at': issued_at,
                        'not_before': cert_info.get('NotBefore'),
                        'not_after': cert_info.get('NotAfter'),
                        'renewal_eligibility': cert_info.get('RenewalEligibility'),
                        'key_usages': cert_info.get('KeyUsages', []),
                        'extended_key_usages': cert_info.get('ExtendedKeyUsages', [])
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
            
            response = AWSResponse(inspector.list_findings())
            filtered_findings = []
            
            for finding in response.data.get('findings', []):
                first_observed = finding.get('firstObservedAt')
                last_observed = finding.get('lastObservedAt')
                updated_at = finding.get('updatedAt')
                
                # Filter findings observed or updated within date range
                if (first_observed and start_date_aware <= first_observed <= end_date_aware) or \
                   (last_observed and start_date_aware <= last_observed <= end_date_aware) or \
                   (updated_at and start_date_aware <= updated_at <= end_date_aware):
                    
                    filtered_findings.append({
                        'finding_arn': finding.get('findingArn'),
                        'severity': finding.get('severity'),
                        'status': finding.get('status'),
                        'type': finding.get('type'),
                        'title': finding.get('title'),
                        'description': finding.get('description'),
                        'first_observed_at': first_observed,
                        'last_observed_at': last_observed,
                        'updated_at': updated_at
                    })
            
            return filtered_findings
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'inspector': str(e)})
            return []

    def get_trusted_advisor_security(self):
        """Get Trusted Advisor security recommendations within date range"""
        try:
            support = boto3.client('support', region_name='us-east-1')
            advisor_data = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            # Test if premium support is available
            try:
                checks = AWSResponse(support.describe_trusted_advisor_checks(language='en'))
                for check in checks.data.get('checks', []):
                    if 'security' in check.get('category', '').lower():
                        check_result = AWSResponse(support.describe_trusted_advisor_check_result(
                            checkId=check.get('id'),
                            language='en'
                        ))
                        
                        result_data = check_result.data.get('result', {})
                        timestamp = result_data.get('timestamp')
                        
                        if timestamp and isinstance(timestamp, str):
                            try:
                                from datetime import timezone
                                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                # If conversion fails, include the check anyway
                                timestamp = None
                                
                        # Filter by timestamp if available, otherwise include all
                        if not timestamp or (start_date_aware <= timestamp <= end_date_aware):
                            advisor_data.append({
                                'check_id': check.get('id'),
                                'name': check.get('name'),
                                'description': check.get('description'),
                                'category': check.get('category'),
                                'status': result_data.get('status'),
                                'resources_summary': result_data.get('resourcesSummary'),
                                'flagged_resources': len(result_data.get('flaggedResources', [])),
                                'timestamp': timestamp
                            })
            except ClientError as e:
                raise e 
                    
            return advisor_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.SECURITY, status="Fail", value={'trusted_advisor_security': str(e)})
            return []

    #7. Fetching data from Trusted Advisor
    def get_trusted_advisor(self):
        try:
            support = boto3.client('support', region_name='us-east-1')
            recommendations = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            checks = AWSResponse(support.describe_trusted_advisor_checks(language='en'))
            
            try:
                for check in checks.data.get('checks', []):
                    try:
                        result = AWSResponse(support.describe_trusted_advisor_check_result(
                            checkId=check.get('id'), language='en'
                        ))
                        
                        check_result = result.data.get('result', {})
                        flagged_resources = check_result.get('flaggedResources', [])
                        timestamp = check_result.get('timestamp')
                        
                        # Filter by timestamp and only include checks with issues
                        if check_result.get('status') in ['warning', 'error'] and flagged_resources:
                            if timestamp and isinstance(timestamp, str):
                                try:
                                    from datetime import timezone
                                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    # If conversion fails, include the check anyway
                                    timestamp = None

                            if not timestamp or (start_date_aware <= timestamp <= end_date_aware):
                                recommendations.append({
                                    'check_name': check.get('name'),
                                    'category': check.get('category'),
                                    'severity': check_result.get('status'),
                                    'recommendation': check.get('description'),
                                    'affected_resources_count': len(flagged_resources),
                                    'potential_savings': check_result.get('categorySpecificSummary', {}).get('costOptimizing', {}).get('estimatedMonthlySavings'),
                                    'timestamp': timestamp
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
            from datetime import timezone
            signals = boto3.client('application-signals', region_name=REGION)
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            # Application Signals has a 24-hour limit, so adjust the time range
            time_diff = end_date_aware - start_date_aware
            if time_diff.total_seconds() > 24 * 3600:  # More than 24 hours
                # Use last 24 hours instead
                end_date_aware = datetime.now(timezone.utc)
                start_date_aware = end_date_aware - timedelta(hours=23)  # 23 hours to be safe
            
            # Use list_services with proper parameters
            response = AWSResponse(signals.list_services(
                StartTime=start_date_aware,
                EndTime=end_date_aware,
                MaxResults=100
            ))
            
            result = [{
                'service_name': service.get('ServiceName'),
                'namespace': service.get('Namespace'),
                'key_attributes': service.get('KeyAttributes', {}),
                'attribute_map': service.get('AttributeMap', {}),
                'metric_references': service.get('MetricReferences', [])
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
            resilience = boto3.client('resiliencehub', region_name=REGION)
            response = AWSResponse(resilience.list_apps())
            apps_data = []
            
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            for app in response.data.get('appSummaries', []):
                creation_time = app.get('creationTime')
                last_assessment_time = app.get('lastAssessmentTime')
                
                # Filter apps created or assessed within date range
                if (creation_time and start_date_aware <= creation_time <= end_date_aware) or \
                   (last_assessment_time and start_date_aware <= last_assessment_time <= end_date_aware):
                    
                    app_arn = app.get('appArn') #earlier was appArn
                    app_data = {
                        'app_arn': app_arn,
                        'name': app.get('name'),
                        'description': app.get('description'),
                        'creation_time': creation_time,
                        'last_assessment_time': last_assessment_time,
                        'compliance_status': app.get('complianceStatus'),
                        'resiliency_score': app.get('resiliencyScore'),
                        'status': app.get('status'),
                        'rpo': None,
                        'rto': None,
                        'last_drill': None,
                        'cost': None
                    }
                    
                    try:
                        # Get app details for RPO/RTO
                        app_details = AWSResponse(resilience.describe_app(appArn=app_arn))
                        policy = app_details.data.get('app', {}).get('resiliencyPolicyArn')
                        if policy:
                            policy_details = AWSResponse(resilience.describe_resiliency_policy(policyArn=policy))
                            policy_data = policy_details.data.get('policy', {}).get('policy', {})
                            if policy_data:
                                app_data['rpo'] = policy_data.get('AZ', {}).get('rpoInSecs')
                                app_data['rto'] = policy_data.get('AZ', {}).get('rtoInSecs')
                        
                        # Get last test recommendation
                        tests = AWSResponse(resilience.list_test_recommendations(appArn=app_arn))
                        if tests.data.get('testRecommendations'):
                            app_data['last_drill'] = tests.data['testRecommendations'][0].get('creationTime')
                        
                        # Get cost estimate
                        cost_estimate = AWSResponse(resilience.describe_app_version_resources_resolution_status(appArn=app_arn, appVersion='release'))
                        app_data['cost'] = cost_estimate.data.get('costEstimate', {}).get('cost')
                        
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
            health = boto3.client('health', region_name='us-east-1')  # Health is global
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
                    'arn': event.get('arn'),
                    'service': event.get('service'),
                    'event_type_code': event.get('eventTypeCode'),
                    'event_type_category': event.get('eventTypeCategory'),
                    'region': event.get('region'),
                    'availability_zone': event.get('availabilityZone'),
                    'start_time': event.get('startTime'),
                    'end_time': event.get('endTime'),
                    'last_updated_time': event.get('lastUpdatedTime'),
                    'status_code': event.get('statusCode'),
                    'event_scope_code': event.get('eventScopeCode')
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
            ce_client = boto3.client('ce')  # Cost Explorer for marketplace costs
            
            marketplace_data = []
            start_date_aware, end_date_aware = self._get_timezone_aware_dates()
            
            try:
                # Get marketplace costs from Cost Explorer
                cost_response = AWSResponse(ce_client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date_aware.strftime('%Y-%m-%d'),
                        'End': end_date_aware.strftime('%Y-%m-%d')
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
                            total_cost += cost_amount
                    
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
                            'product_code': entitlement.get('ProductCode'),
                            'dimension': entitlement.get('Dimension'),
                            'customer_identifier': entitlement.get('CustomerIdentifier'),
                            'value': entitlement.get('Value'),
                            'expiration_date': entitlement.get('ExpirationDate'),
                            'cost_consumed': total_cost,
                            'currency': 'USD',
                            'period_start': start_date_aware.strftime('%Y-%m-%d'),
                            'period_end': end_date_aware.strftime('%Y-%m-%d'),
                            'daily_costs': daily_costs,
                            'status': 'ACTIVE'
                        })
                
                except Exception:
                    # If no entitlements but there are costs, create a generic entry
                    if total_cost > 0:
                        marketplace_data.append({
                            'product_code': 'MARKETPLACE_USAGE',
                            'product_name': 'AWS Marketplace Products',
                            'dimension': 'Usage',
                            'customer_identifier': None,
                            'value': None,
                            'expiration_date': None,
                            'cost_consumed': total_cost,
                            'currency': 'USD',
                            'period_start': start_date_aware.strftime('%Y-%m-%d'),
                            'period_end': end_date_aware.strftime('%Y-%m-%d'),
                            'daily_costs': daily_costs,
                            'status': 'CONSUMED'
                        })
            
            except Exception as e:
                print(f"Error getting marketplace costs: {str(e)}")
            
            self.data.set_data(attr=AWSResourceType.MARKETPLACE, data=marketplace_data)
            self.set_log(def_type=AWSResourceType.MARKETPLACE, status="Pass")
            return marketplace_data
        except Exception as e:
            self.set_log(def_type=AWSResourceType.MARKETPLACE, status="Fail", value={'marketplace': str(e)})
            return []

def get_data(interval="DAILY", start_date=None, end_date=None):
    import time
    start_time = time.time()
    process_times = {}
    
    sts_client      = boto3.client('sts')
    
    identity        = AWSResponse(sts_client.get_caller_identity())
    account         = identity.data['Account']
    
    end_date        = end_date
    start_date      = None
    
    interval        = interval
    aws             = AWSResourceManager(account_id=account, interval=interval, start_date=start_date, end_date=end_date)

    
    #1. Fetch Account Data
    step_start = time.time()
    aws.get_account_details()
    process_times['account_details'] = round(time.time() - step_start, 2)
    
    #2. Fetch Services Data  
    step_start = time.time()
    aws.get_services()
    process_times['services'] = round(time.time() - step_start, 2)
    
    #3. Fetch Config Data  
    step_start = time.time()
    aws.get_config()
    process_times['config'] = round(time.time() - step_start, 2)
    
    #4. Fetch Cost Data
    step_start = time.time()
    aws.get_cost()
    process_times['cost'] = round(time.time() - step_start, 2)
    
    #5. Fetch Inventory Data
    step_start = time.time()
    aws.get_inventory()
    process_times['inventory'] = round(time.time() - step_start, 2)
    
    #6. Fetch Security Data
    step_start = time.time()
    aws.get_security()
    process_times['security'] = round(time.time() - step_start, 2)
    
    #7. Fetch Trusted Advisor Data
    step_start = time.time()
    aws.get_trusted_advisor()
    process_times['trusted_advisor'] = round(time.time() - step_start, 2)
    
    #8. Fetch Application Signals Data
    step_start = time.time()
    aws.get_application_signals()
    process_times['application_signals'] = round(time.time() - step_start, 2)
    
    #9. Fetch Resilience Hub Application Data
    step_start = time.time()
    aws.get_resilience_hub_apps()
    process_times['resilience_hub'] = round(time.time() - step_start, 2)
    
    #10. Fetch Health Data
    step_start = time.time()
    aws.get_health()
    process_times['health'] = round(time.time() - step_start, 2)
    
    #11. Fetch Marketplace Data
    step_start = time.time()
    aws.get_marketplace()
    process_times['marketplace'] = round(time.time() - step_start, 2)

    #All. Get All Data
    step_start = time.time()
    data = aws.data.get_all_data()
    process_times['get_all_data'] = round(time.time() - step_start, 2)
    
    # Ensure data is not None before uploading
    if data is None:
        print("Warning: No data collected, creating empty data structure")
        data = {
            "account": {"account_id": account},
            "error": "No data collected",
            "timestamp": datetime.now().isoformat()
        }
    
    step_start = time.time()
    result = upload_to_s3(data=data, account=account, end_date=end_date, interval=interval)
    process_times['upload_to_s3'] = round(time.time() - step_start, 2)
    
    # Calculate total processing time
    total_time = round(time.time() - start_time, 2)
    process_times['total_time'] = total_time
    
    # Add processing times to result
    if isinstance(result, dict):
        result['processing_times'] = process_times
    
    return result

def load_current_data(interval="DAILY", end_date=None):
    import time
    start_time = time.time()
    
    data = get_data(interval=interval, end_date=end_date)
    
    processing_time = round(time.time() - start_time, 2)
    print(f"{TIMING} Current data load ({interval}) completed in {processing_time}s")
    
    # Add timing info to result if it's a dict
    if isinstance(data, dict) and 'processing_times' not in data:
        data['processing_times'] = {'total_time': processing_time}
    
    return data

def load_historical_data():
    import time
    overall_start_time = time.time()
    
    till_date   = datetime.now()
    start_date  = datetime(till_date.year, 1, 1)  # January 1st of current year
    interval    = "DAILY"
    
    print(f"{CALENDAR}  Will process daily data from {start_date.strftime('%d-%m-%Y')} to {till_date.strftime('%d-%m-%Y')}")

    current                 = start_date
    count                   = 0
    total_processing_time   = 0
    processing_times        = []
    
    while current <= till_date:
        formatted_date = current.strftime('%d-%m-%Y')
        day_start_time = time.time()
        
        try:
            last_day_of_month   = monthrange(current.year, current.month)[1]
            is_last_day         = current.day == last_day_of_month
            #interval            = "MONTHLY" if(is_last_day) else "DAILY"

            #if(is_last_day):
            #    daily_start = time.time()
            #    data = get_data(interval="DAILY", end_date=current)
            #    daily_time = round(time.time() - daily_start, 2)
            #    print(f"{SUCCESS} DAILY : {formatted_date} Loaded (took {daily_time}s)")

            interval_start = time.time()
            data = get_data(interval=interval, end_date=current)
            interval_time = round(time.time() - interval_start, 2)
            
            day_total_time = round(time.time() - day_start_time, 2)
            total_processing_time += day_total_time
            
            # Ensure data is a dict before accessing get method
            if isinstance(data, dict):
                processing_times.append({
                    'date': formatted_date,
                    'interval': interval,
                    'processing_time': day_total_time,
                    'details': data.get('processing_times', {})
                })
            else:
                processing_times.append({
                    'date': formatted_date,
                    'interval': interval,
                    'processing_time': day_total_time,
                    'details': {'error': 'No data returned'}
                })
            
            print(f"{SUCCESS} {interval} : {formatted_date} Loaded (took {interval_time}s)")
        except Exception as e:
            print(f"{ERROR} {interval} : {formatted_date} Not Loaded - {str(e)}")
            continue
        
        finally:
            # Move to next day
            current += timedelta(days=1)
            count += 1

    overall_time = round(time.time() - overall_start_time, 2)
    avg_time = round(total_processing_time / count if count > 0 else 0, 2)
    
    print(f"Historical data processing complete:")
    print(f"{TIMING} Total time: {overall_time}s")
    print(f"{TIMING} Average time per day: {avg_time}s")
    print(f"{CALENDAR} Days processed: {count}")
    
    return {
        "from": start_date.strftime('%d-%m-%Y'), 
        "to": till_date.strftime('%d-%m-%Y'), 
        "loaded": count,
        "total_time": overall_time,
        "avg_time": avg_time,
        "processing_times": processing_times
    }

def process_data_status(has_daily, has_monthly, has_history, daily_data, monthly_data, history_data, load_time=None):
    daily_status    = f"{ERROR} No Daily Data"
    monthly_status  = f"{ERROR} No Monthly Data"
    history_status  = f"{ERROR} No Historical Data"
    
    if(has_daily and daily_data is not None):
        daily_status    = f"{SUCCESS} Daily Data - {daily_data.get('path', 'Unknown')} Time-Taken: {load_time['daily_load_time']}"

    if(has_monthly and monthly_data is not None):
        monthly_status    = f"{SUCCESS} Monthly Data - {monthly_data.get('path', 'Unknown')} Time-Taken: {load_time['daily_load_time']}"

    if(has_history and history_data is not None):
        history_status  = f"{SUCCESS} {history_data.get('loaded', 0)} Historical Data Loaded between {history_data.get('from', '')} - {history_data.get('to', '')} Time-Taken: {load_time['historical_load_time']}"
    
    return [daily_status, monthly_status, history_status]

def lambda_handler(event=None, context=None):
    import time
    start_time = time.time()
    
    #1. AWS Boto3 Permission Test
    aws_permission = AWSBoto3Permissions()
    
    has_daily     = False
    has_monthly   = False
    has_history   = False
    daily_data    = None
    monthly_data  = None
    history_data  = None
    status        = []
    timing_info   = {}

    if aws_permission.test():
        print("*"*15,"Connected","*"*15)
        if (event is not None and isinstance(event, dict) and "history" in event and (event['history'] == True or event['history'] == "True")):
            print("Loading Historical Data")
            history_start = time.time()
            history_data = load_historical_data()
            history_time = round(time.time() - history_start, 2)
            has_history = True
            timing_info['historical_load_time'] = history_time
            
            print(f"{SUCCESS if(has_history) else ERROR} History Data (took {history_time}s)")
        else:
            print(f"{INFO} Loading Daily & Monthly Data")
            daily_start = time.time()
            daily_data = load_current_data(interval="DAILY")
            daily_time = round(time.time() - daily_start, 2)
            timing_info['daily_load_time'] = daily_time
            
            if(daily_data and daily_data is not None and 'path' in daily_data):
                has_daily = True
                ## Uncomment if you want to load monthly data
                # monthly_start = time.time()
                # monthly_data = load_current_data(interval="MONTHLY")
                # monthly_time = round(time.time() - monthly_start, 2)
                # timing_info['monthly_load_time'] = monthly_time
                # 
                # if(monthly_data and monthly_data is not None and 'path' in monthly_data):
                #     has_monthly = True
          
            status = process_data_status(has_daily, has_monthly, has_history, daily_data, monthly_data, history_data, load_time=timing_info)
            print(status[0])
            print(status[1])
            print(status[2])

        total_time = round(time.time() - start_time, 2)
        timing_info['total_execution_time'] = total_time
        print(f"{TIMING} Total execution time: {total_time}s")
        print("*"*14,"Disconnected","*"*13)
        
        # Add timing info to status response
        if isinstance(status, list):
            status.append(f"Execution time: {total_time}s")
        
        # If returning a dict instead of status list
        result = {
            'status': status,
            'timing': timing_info
        }
        
        return result

if __name__ == "__main__":
    
    temp = lambda_handler({"history":False})
    #print(temp)
