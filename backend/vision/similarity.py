import numpy as np
from typing import List, Tuple

def _normalize(v: np.ndarray, axis: int = -1, eps: float = 1e-8) -> np.ndarray:
    """Safely normalizes numeric vectors avoiding division by zero."""
    norm = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / (norm + eps)

def cosine_similarity_matrix(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Computes cosine similarity between a single query and a matrix of candidates.
    query: (dim,)
    matrix: (N, dim)
    Returns: (N,) similarity values in [-1, 1]
    """
    if matrix.shape[0] == 0:
        return np.array([], dtype=np.float32)
        
    q_norm = _normalize(query)
    m_norm = _normalize(matrix, axis=1)
    
    # Dot product of normalized vectors
    return np.dot(m_norm, q_norm)

def top_k_similar(query_vec: np.ndarray, candidates: List[Tuple[str, np.ndarray]], top_k: int = 10, min_threshold: float = -1.0) -> List[Tuple[str, float]]:
    """
    Finds top k similar items.
    candidates: List of (asset_id, embedding)
    Returns sorted list of (asset_id, similarity)
    """
    if not candidates:
        return []
        
    asset_ids = [c[0] for c in candidates]
    matrix = np.vstack([c[1] for c in candidates])
    
    sims = cosine_similarity_matrix(query_vec, matrix)
    
    # Create tuples to sort
    results = []
    for i, sim in enumerate(sims):
        sim_val = float(sim)
        if sim_val >= min_threshold:
            results.append((asset_ids[i], sim_val))
            
    # Sort descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
