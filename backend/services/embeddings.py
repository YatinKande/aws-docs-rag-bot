from FlagEmbedding import BGEM3FlagModel
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self._model = BGEM3FlagModel(
            settings.EMBEDDING_MODEL,
            use_fp16=True  # Faster on Mac
        )
        logger.info(
            "BGE-M3 embedding model loaded"
        )
    
    def embed_documents(self, texts: list) -> list:
        output = self._model.encode(
            texts,
            batch_size=12,
            max_length=8192,
            return_dense=True
        )
        return output["dense_vecs"].tolist()
    
    def embed_query(self, text: str) -> list:
        output = self._model.encode(
            [text],
            batch_size=1,
            max_length=8192,
            return_dense=True
        )
        return output["dense_vecs"][0].tolist()

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
            self._embeddings = EmbeddingService()
            print(f"DEBUG: Shared Embedding Model LOADED in {time.time() - start:.2f}s")
        return self._embeddings

# Global access point
def get_shared_embeddings():
    return EmbeddingProvider.get_instance().get_embeddings()
