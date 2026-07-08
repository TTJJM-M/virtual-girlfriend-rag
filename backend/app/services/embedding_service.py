from typing import List, Optional
from dashscope import TextEmbedding
from app.config import model_pool, settings
import numpy as np


class EmbeddingService:
    """DashScope embedding service with automatic model failover"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY

    def _get_embedding_with_retry(self, texts: List[str], model: str) -> Optional[List[List[float]]]:
        """Try to get embedding with specific model"""
        try:
            response = TextEmbedding.call(
                model=model,
                input=texts,
                api_key=self.api_key,
            )
            if response.status_code == 200:
                embeddings = [item["embedding"] for item in response.output["embeddings"]]
                return embeddings
            else:
                # Mark model as exhausted on error
                error_msg = str(response.message) if hasattr(response, 'message') else str(response.status_code)
                model_pool.mark_error(model, error_msg)
                return None
        except Exception as e:
            error_str = str(e)
            model_pool.mark_error(model, error_str)
            return None

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """Embed multiple documents with automatic model switching"""
        all_embeddings = []

        for doc in documents:
            embedding = self._embed_single(doc)
            if embedding:
                all_embeddings.append(embedding)

        return all_embeddings

    def embed_query(self, query: str) -> Optional[List[float]]:
        """Embed single query with automatic model switching"""
        return self._embed_single(query)

    def _embed_single(self, text: str) -> Optional[List[float]]:
        """Embed single text with failover"""
        # Try models in priority order
        for model in [mq.model for mq in model_pool.embedding_models]:
            result = self._get_embedding_with_retry([text], model)
            if result:
                if result[0]:  # valid embedding
                    return result[0]
        return None

    def get_model_status(self) -> dict:
        """Get current model pool status"""
        return model_pool.get_status()

    def reset_model(self, model: str):
        """Reset a model's exhausted status"""
        model_pool.reset_model(model)


# Singleton instance
embedding_service = EmbeddingService()
