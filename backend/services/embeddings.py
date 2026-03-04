from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingProvider:
    _instance = None
    _embeddings = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EmbeddingProvider()
        return cls._instance

    def get_embeddings(self):
        if self._embeddings is None:
            print(f"DEBUG: Loading Shared Embedding Model: {settings.EMBEDDING_MODEL}...")
            import time
            start = time.time()
            self._embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
            print(f"DEBUG: Shared Embedding Model LOADED in {time.time() - start:.2f}s")
        return self._embeddings

# Global access point
def get_shared_embeddings():
    return EmbeddingProvider.get_instance().get_embeddings()
