from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStoreBase(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add list of documents (content + metadata) to the store."""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the store for relevant documents."""
        pass
