from typing import List, Optional
from dataclasses import dataclass
from .vector_store import EmbeddingStore
from .embedder import ImageEmbedder
from .similarity import top_k_similar
import logging

logger = logging.getLogger(__name__)

@dataclass
class SimilarResult:
    asset_id: str
    similarity: float

class SimilarityService:
    def __init__(self, store: EmbeddingStore, embedder: ImageEmbedder):
        self.store = store
        self.embedder = embedder
        self.engine_name = embedder.engine_name

    def similar_by_asset(self, asset_id: str, top_k: int, threshold: float) -> List[SimilarResult]:
        """Find assets similar to an existing asset."""
        query_vec = self.store.get_embedding(asset_id)
        if query_vec is None:
            logger.warning(f"No embedding found for asset_id={asset_id}")
            return []

        all_candidates = self.store.all_embeddings(engine=self.engine_name)
        
        # Remove self from candidates
        candidates = [c for c in all_candidates if c[0] != asset_id]
        if not candidates:
            return []

        raw_results = top_k_similar(query_vec, candidates, top_k=top_k, min_threshold=threshold)
        
        return [SimilarResult(asset_id=r[0], similarity=r[1]) for r in raw_results]

    def similar_by_image_path(self, image_path: str, top_k: int, threshold: float) -> List[SimilarResult]:
        """Find assets similar to a newly uploaded image path."""
        try:
            query_vec = self.embedder.embed_image_path(image_path)
        except Exception as e:
            logger.error(f"Failed to embed image {image_path}: {e}")
            return []

        candidates = self.store.all_embeddings(engine=self.engine_name)
        if not candidates:
            return []

        raw_results = top_k_similar(query_vec, candidates, top_k=top_k, min_threshold=threshold)
        
        return [SimilarResult(asset_id=r[0], similarity=r[1]) for r in raw_results]
