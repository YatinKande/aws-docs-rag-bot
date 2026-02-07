import boto3
from typing import Dict, Any
from backend.services.cloud_providers.base import CloudProviderBase

class AWSClient(CloudProviderBase):
    def __init__(self, access_key: str, secret_key: str, region: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def validate_credentials(self) -> Dict[str, Any]:
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            return {
                "valid": True,
                "account_id": identity['Account'],
                "arn": identity['Arn']
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def query(self, service: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic entry point for cloud queries."""
        # For now, we only have specific handlers like CostExplorer
        # This acts as a fallback or general router
        return {"status": "success", "message": f"AWS query for {service} received.", "params": query_params}
