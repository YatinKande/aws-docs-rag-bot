from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStoreBase(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add list of documents (content + metadata) to the store."""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search the store for relevant documents."""
        pass

    @abstractmethod
    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from the store matching the filter."""
        pass
