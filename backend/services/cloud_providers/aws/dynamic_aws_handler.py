from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicAWSHandler:
    """
    Dynamic AWS query handler that executes boto3 API calls based on parsed queries.
    Supports multiple AWS services: S3, EC2, Lambda, RDS, IAM, Cost Explorer.
    """
    
    def __init__(self, client):
        """
        Initialize dynamic AWS handler with AWS client.
        
        Args:
            client: AWSClient instance with boto3 session
        """
        self.aws_client = client
        self.session = client.session
        
    async def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AWS query based on parsed query information.
        
        Args:
            parsed_query: Dict from LLM interpretation containing:
                - service: AWS service name
                - operation: API operation
                - resources: Resource identifiers
                - filters: Filtering criteria
                - intent: High-level intent
                
        Returns:
            Dict containing:
                - status: "success" or "error"
                - service: AWS service name
                - operation: Operation performed
                - data: Query results
                - metadata: Timestamp, region, etc.
                - message: Error message if status is "error"
        """
        service = parsed_query.get('service', '').lower()
        
        logger.info(f"Executing AWS query: service={service}, operation={parsed_query.get('operation')}, "
                   f"resources={parsed_query.get('resources')}, filters={parsed_query.get('filters')}")
        
        try:
            # Route to service-specific executor
            if service == 's3':
                return await self._execute_s3_query(parsed_query)
            elif service == 'ec2':
                return await self._execute_ec2_query(parsed_query)
            elif service == 'lambda':
                return await self._execute_lambda_query(parsed_query)
            elif service == 'rds':
                return await self._execute_rds_query(parsed_query)
            elif service == 'iam':
                return await self._execute_iam_query(parsed_query)
            elif service == 'ce':
                return await self._execute_cost_explorer_query(parsed_query)
            else:
                return {
                    "status": "error",
                    "service": service,
                    "message": f"Service '{service}' is not yet implemented. Currently supported: S3, EC2, Lambda, RDS, IAM, Cost Explorer"
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing AWS query: {error_msg}", exc_info=True)
            
            # Provide helpful error messages
            if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                return {
                    "status": "error",
                    "service": service,
                    "message": f"Access denied for {service}. Please verify your IAM permissions include read access to {service.upper()}."
                }
            elif "InvalidAccessKeyId" in error_msg:
                return {
                    "status": "error",
                    "service": service,
                    "message": "Invalid AWS access key. Please check your credentials."
                }
            else:
                return {
                    "status": "error",
                    "service": service,
                    "message": f"AWS API error: {error_msg}"
                }
    
    async def _execute_s3_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute S3-related queries."""
        operation = parsed_query.get('operation', 'list')
        resources = parsed_query.get('resources', {})
        intent = parsed_query.get('intent', 'list')
        
        s3_client = self.session.client('s3')
        
        # List all buckets
        if operation == 'list_buckets' or (operation == 'list' and not resources.get('bucket_name')):
            logger.info("Calling AWS s3.list_buckets")
            response = await asyncio.to_thread(s3_client.list_buckets)
            
            buckets = []
            for bucket in response.get('Buckets', []):
                buckets.append({
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat()
                })
            
            return {
                "status": "success",
                "service": "s3",
                "operation": "list_buckets",
                "data": {
                    "buckets": buckets,
                    "count": len(buckets)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "api_call": "s3.list_buckets"
                }
            }
        
        # List objects in a bucket
        elif operation == 'list_objects' or resources.get('bucket_name'):
            bucket_name = resources.get('bucket_name')
            if not bucket_name:
                return {
                    "status": "error",
                    "service": "s3",
                    "message": "Bucket name is required for listing objects"
                }
            
            logger.info(f"Calling AWS s3.list_objects_v2 with Bucket={bucket_name}")
            
            # Use pagination for large buckets
            objects = []
            total_size = 0
            continuation_token = None
            max_keys = 1000  # Limit to first 1000 objects
            
            try:
                while len(objects) < max_keys:
                    params = {'Bucket': bucket_name, 'MaxKeys': min(1000, max_keys - len(objects))}
                    if continuation_token:
                        params['ContinuationToken'] = continuation_token
                    
                    response = await asyncio.to_thread(s3_client.list_objects_v2, **params)
                    
                    for obj in response.get('Contents', []):
                        objects.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })
                        total_size += obj['Size']
                    
                    if not response.get('IsTruncated'):
                        break
                    continuation_token = response.get('NextContinuationToken')
                
                # Format size in MB
                total_size_mb = total_size / (1024 * 1024)
                
                return {
                    "status": "success",
                    "service": "s3",
                    "operation": "list_objects_v2",
                    "data": {
                        "bucket": bucket_name,
                        "objects": objects[:10] if intent == 'count' else objects,  # Show sample if counting
                        "object_count": len(objects),
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size_mb, 2),
                        "truncated": len(objects) >= max_keys
                    },
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "api_call": f"s3.list_objects_v2(Bucket={bucket_name})"
                    }
                }
                
            except Exception as e:
                if "NoSuchBucket" in str(e):
                    return {
                        "status": "error",
                        "service": "s3",
                        "message": f"Bucket '{bucket_name}' does not exist or you don't have access to it."
                    }
                raise
        
        return {
            "status": "error",
            "service": "s3",
            "message": f"S3 operation '{operation}' is not yet implemented"
        }
    
    async def _execute_ec2_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute EC2-related queries."""
        operation = parsed_query.get('operation', 'describe_instances')
        filters = parsed_query.get('filters', {})
        
        region = filters.get('region', self.aws_client.region)
        ec2_client = self.session.client('ec2', region_name=region)
        
        if operation == 'describe_instances':
            # Build filters
            boto_filters = []
            if filters.get('state'):
                boto_filters.append({'Name': 'instance-state-name', 'Values': [filters['state']]})
            
            logger.info(f"Calling AWS ec2.describe_instances with Filters={boto_filters}")
            response = await asyncio.to_thread(
                ec2_client.describe_instances,
                Filters=boto_filters if boto_filters else []
            )
            
            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'availability_zone': instance['Placement']['AvailabilityZone']
                    })
            
            return {
                "status": "success",
                "service": "ec2",
                "operation": "describe_instances",
                "data": {
                    "instances": instances,
                    "count": len(instances),
                    "filters_applied": filters
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "region": region,
                    "api_call": "ec2.describe_instances"
                }
            }
        
        elif operation == 'describe_regions':
            logger.info("Calling AWS ec2.describe_regions")
            response = await asyncio.to_thread(ec2_client.describe_regions)
            
            regions = [r['RegionName'] for r in response.get('Regions', [])]
            
            return {
                "status": "success",
                "service": "ec2",
                "operation": "describe_regions",
                "data": {
                    "regions": regions,
                    "count": len(regions)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "api_call": "ec2.describe_regions"
                }
            }
        
        return {
            "status": "error",
            "service": "ec2",
            "message": f"EC2 operation '{operation}' is not yet implemented. Supported: describe_instances, describe_regions"
        }
    
    async def _execute_lambda_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Lambda-related queries."""
        operation = parsed_query.get('operation', 'list_functions')
        filters = parsed_query.get('filters', {})
        
        region = filters.get('region', self.aws_client.region)
        lambda_client = self.session.client('lambda', region_name=region)
        
        if operation == 'list_functions' or operation == 'list':
            logger.info(f"Calling AWS lambda.list_functions in region {region}")
            response = await asyncio.to_thread(lambda_client.list_functions)
            
            functions = []
            for func in response.get('Functions', []):
                functions.append({
                    'function_name': func['FunctionName'],
                    'runtime': func.get('Runtime', 'N/A'),
                    'handler': func.get('Handler', 'N/A'),
                    'memory_size': func.get('MemorySize', 0),
                    'last_modified': func.get('LastModified', 'N/A')
                })
            
            return {
                "status": "success",
                "service": "lambda",
                "operation": "list_functions",
                "data": {
                    "functions": functions,
                    "count": len(functions)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "region": region,
                    "api_call": "lambda.list_functions"
                }
            }
        
        return {
            "status": "error",
            "service": "lambda",
            "message": f"Lambda operation '{operation}' is not yet implemented. Supported: list_functions"
        }
    
    async def _execute_rds_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RDS-related queries."""
        operation = parsed_query.get('operation', 'describe_db_instances')
        filters = parsed_query.get('filters', {})
        
        region = filters.get('region', self.aws_client.region)
        rds_client = self.session.client('rds', region_name=region)
        
        if operation == 'describe_db_instances' or operation == 'list':
            logger.info(f"Calling AWS rds.describe_db_instances in region {region}")
            response = await asyncio.to_thread(rds_client.describe_db_instances)
            
            instances = []
            for db in response.get('DBInstances', []):
                instances.append({
                    'db_instance_identifier': db['DBInstanceIdentifier'],
                    'engine': db['Engine'],
                    'engine_version': db.get('EngineVersion', 'N/A'),
                    'instance_class': db['DBInstanceClass'],
                    'status': db['DBInstanceStatus'],
                    'availability_zone': db.get('AvailabilityZone', 'N/A')
                })
            
            return {
                "status": "success",
                "service": "rds",
                "operation": "describe_db_instances",
                "data": {
                    "instances": instances,
                    "count": len(instances)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "region": region,
                    "api_call": "rds.describe_db_instances"
                }
            }
        
        return {
            "status": "error",
            "service": "rds",
            "message": f"RDS operation '{operation}' is not yet implemented. Supported: describe_db_instances"
        }
    
    async def _execute_iam_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute IAM-related queries (read-only)."""
        operation = parsed_query.get('operation', 'list_users')
        
        iam_client = self.session.client('iam')
        
        if operation == 'list_users' or operation == 'list':
            logger.info("Calling AWS iam.list_users")
            response = await asyncio.to_thread(iam_client.list_users)
            
            users = []
            for user in response.get('Users', []):
                users.append({
                    'user_name': user['UserName'],
                    'user_id': user['UserId'],
                    'arn': user['Arn'],
                    'create_date': user['CreateDate'].isoformat()
                })
            
            return {
                "status": "success",
                "service": "iam",
                "operation": "list_users",
                "data": {
                    "users": users,
                    "count": len(users)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "api_call": "iam.list_users"
                }
            }
        
        elif operation == 'list_roles':
            logger.info("Calling AWS iam.list_roles")
            response = await asyncio.to_thread(iam_client.list_roles)
            
            roles = []
            for role in response.get('Roles', []):
                roles.append({
                    'role_name': role['RoleName'],
                    'role_id': role['RoleId'],
                    'arn': role['Arn'],
                    'create_date': role['CreateDate'].isoformat()
                })
            
            return {
                "status": "success",
                "service": "iam",
                "operation": "list_roles",
                "data": {
                    "roles": roles,
                    "count": len(roles)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "api_call": "iam.list_roles"
                }
            }
        
        return {
            "status": "error",
            "service": "iam",
            "message": f"IAM operation '{operation}' is not yet implemented. Supported: list_users, list_roles"
        }
    
    async def _execute_cost_explorer_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Cost Explorer queries (use existing implementation)."""
        from backend.services.cloud_providers.aws.cost_explorer import AWSCostExplorer
        
        ce = AWSCostExplorer(self.aws_client)
        data = await ce.get_cost_summary()
        
        return {
            "status": data.get('status', 'success'),
            "service": "ce",
            "operation": "get_cost_and_usage",
            "data": data,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "api_call": "ce.get_cost_and_usage"
            }
        }
