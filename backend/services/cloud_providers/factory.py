from typing import Dict, Any
from backend.services.cloud_providers.aws.client import AWSClient
from backend.services.cloud_providers.gcp.client import GCPClient
from backend.services.cloud_providers.azure.client import AzureClient

class CloudProviderFactory:
    @staticmethod
    def get_provider(provider_type: str, credentials: Dict[str, Any]):
        if provider_type == "aws":
            return AWSClient(
                access_key=credentials.get("access_key"),
                secret_key=credentials.get("secret_key"),
                region=credentials.get("region", "us-east-1")
            )
        elif provider_type == "gcp":
            return GCPClient(service_account_info=credentials)
        elif provider_type == "azure":
            return AzureClient(credentials=credentials)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider_type}")
