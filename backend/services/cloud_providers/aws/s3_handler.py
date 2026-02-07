from typing import Dict, Any, List
import asyncio
import logging

logger = logging.getLogger(__name__)

class AWSS3Handler:
    def __init__(self, client):
        """
        Initialize S3 handler with AWS client.
        
        Args:
            client: AWSClient instance with boto3 session
        """
        self.s3 = client.session.client('s3')

    async def get_s3_buckets(self) -> Dict[str, Any]:
        """
        Retrieve list of all S3 buckets in the AWS account.
        
        Returns:
            Dict containing:
                - status: "success" or "error"
                - buckets: List of bucket info dicts (name, creation_date)
                - count: Number of buckets
                - message: Error message if status is "error"
        """
        try:
            logger.info("Fetching S3 buckets from AWS API")
            
            # Run blocking boto3 call in threadpool
            response = await asyncio.to_thread(
                self.s3.list_buckets
            )
            
            # Extract bucket information
            buckets = []
            for bucket in response.get('Buckets', []):
                buckets.append({
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat()
                })
            
            logger.info(f"Successfully retrieved {len(buckets)} S3 buckets")
            
            return {
                "status": "success",
                "buckets": buckets,
                "count": len(buckets)
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching S3 buckets: {error_msg}")
            
            # Provide user-friendly error messages
            if "AccessDenied" in error_msg:
                message = "Access denied. Please verify your AWS credentials have S3 list permissions."
            elif "InvalidAccessKeyId" in error_msg:
                message = "Invalid AWS access key. Please check your credentials."
            elif "SignatureDoesNotMatch" in error_msg:
                message = "Invalid AWS secret key. Please check your credentials."
            else:
                message = f"Failed to retrieve S3 buckets: {error_msg}"
            
            return {
                "status": "error",
                "message": message,
                "buckets": [],
                "count": 0
            }
