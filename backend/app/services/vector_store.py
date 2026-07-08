import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.config import settings, model_pool
from app.services.embedding_service import embedding_service
import faiss


@dataclass
class SearchResult:
    text: str
    score: float
    chunk_index: int
    document_id: int
    document_name: str


class FAISSVectorStore:
    """Per-user FAISS vector store with automatic model failover"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.base_path = os.path.join(settings.VECTOR_STORE_DIR, str(user_id))
        self.index_path = os.path.join(self.base_path, "index.faiss")
        self.metadata_path = os.path.join(self.base_path, "metadata.json")
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict[str, Any]] = []  # [{text, doc_id, doc_name, chunk_idx}]
        self.embedding_dim = 1024  # text-embedding-v3 dimension
        self._ensure_dir()
        self._load_or_create_index()

    def _ensure_dir(self):
        """Ensure directory exists"""
        os.makedirs(self.base_path, exist_ok=True)

    def _load_or_create_index(self):
        """Load existing index or create new one"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                print(f"Loaded vector store for user {self.user_id}: {len(self.metadata)} chunks")
            except Exception as e:
                print(f"Error loading index, creating new: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create new FAISS index"""
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        self.metadata = []
        print(f"Created new vector store for user {self.user_id}")

    def _save_index(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)

    def add_chunks(self, chunks: List[Tuple[str, int, int, str]]):
        """
        Add document chunks to index.
        chunks: [(text, chunk_idx, doc_id, doc_name), ...]
        """
        if not chunks:
            return

        # Get embeddings with automatic model failover
        texts = [c[0] for c in chunks]
        embeddings = embedding_service.embed_documents(texts)

        if not embeddings:
            raise RuntimeError("Failed to get embeddings - all embedding models exhausted")

        # Normalize embeddings for cosine similarity
        embeddings_np = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_np)

        # Add to index
        self.index.add(embeddings_np)

        # Add metadata
        for i, (text, chunk_idx, doc_id, doc_name) in enumerate(chunks):
            self.metadata.append({
                "text": text,
                "chunk_index": chunk_idx,
                "document_id": doc_id,
                "document_name": doc_name,
            })

        self._save_index()
        print(f"Added {len(chunks)} chunks to user {self.user_id}'s vector store")

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Search for similar chunks.
        Returns list of SearchResult sorted by relevance.
        """
        if self.index.ntotal == 0:
            return []

        # Get query embedding with automatic model failover
        query_embedding = embedding_service.embed_query(query)
        if not query_embedding:
            raise RuntimeError("Failed to get query embedding - all models exhausted")

        query_np = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_np)

        # Search
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_np, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append(SearchResult(
                text=meta["text"],
                score=float(scores[0][i]),
                chunk_index=meta["chunk_index"],
                document_id=meta["document_id"],
                document_name=meta["document_name"],
            ))

        return results

    def remove_document(self, document_id: int):
        """Remove all chunks belonging to a document"""
        # Filter out chunks for this document
        new_metadata = []
        indices_to_keep = []

        for i, meta in enumerate(self.metadata):
            if meta["document_id"] != document_id:
                new_metadata.append(meta)
                indices_to_keep.append(i)

        if len(indices_to_keep) == len(self.metadata):
            return  # Nothing to remove

        # Rebuild index (FAISS doesn't support efficient deletion)
        if indices_to_keep:
            vectors = self.index.reconstruct_n(0, self.index.ntotal)
            kept_vectors = vectors[indices_to_keep]

            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.index.add(kept_vectors)
            self.metadata = new_metadata
        else:
            self._create_new_index()

        self._save_index()
        print(f"Removed document {document_id} from user {self.user_id}'s vector store")

    def clear(self):
        """Clear all vectors for this user"""
        self._create_new_index()
        self._save_index()

    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "user_id": self.user_id,
            "total_chunks": len(self.metadata),
            "total_vectors": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "model_status": model_pool.get_status(),
        }


def get_vector_store(user_id: int) -> FAISSVectorStore:
    """Get or create vector store for user"""
    return FAISSVectorStore(user_id)
