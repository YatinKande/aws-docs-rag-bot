from abc import ABC, abstractmethod
from typing import Dict, Any, List

class CloudProviderBase(ABC):
    @abstractmethod
    def validate_credentials(self) -> Dict[str, Any]:
        """Validates the provided credentials."""
        pass

    @abstractmethod
    async def query(self, service: str, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generic query method for cloud services."""
        pass
