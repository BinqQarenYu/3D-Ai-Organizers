import sqlite3
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmbeddingStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_embeddings (
                    asset_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    dim INTEGER NOT NULL,
                    engine TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embedding_engine 
                ON image_embeddings(engine)
            """)

    def put_embedding(self, asset_id: str, vector: np.ndarray, engine: str) -> None:
        if vector.dtype != np.float32:
            vector = vector.astype(np.float32)
        
        blob = vector.tobytes()
        dim = vector.shape[0]
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO image_embeddings (asset_id, embedding, dim, engine, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    embedding=excluded.embedding,
                    dim=excluded.dim,
                    engine=excluded.engine,
                    created_at=excluded.created_at
            """, (asset_id, blob, dim, engine, now))

    def get_embedding(self, asset_id: str) -> Optional[np.ndarray]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT embedding, dim FROM image_embeddings WHERE asset_id = ?", 
                (asset_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return np.frombuffer(row['embedding'], dtype=np.float32)

    def delete_embedding(self, asset_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM image_embeddings WHERE asset_id = ?", (asset_id,))

    def all_embeddings(self, engine: Optional[str] = None) -> List[Tuple[str, np.ndarray]]:
        query = "SELECT asset_id, embedding FROM image_embeddings"
        params = []
        if engine:
            query += " WHERE engine = ?"
            params.append(engine)
            
        results = []
        with self._get_connection() as conn:
            for row in conn.execute(query, params):
                vec = np.frombuffer(row['embedding'], dtype=np.float32)
                results.append((row['asset_id'], vec))
        return results

    def count_embeddings(self, engine: Optional[str] = None) -> int:
        query = "SELECT COUNT(*) as count FROM image_embeddings"
        params = []
        if engine:
            query += " WHERE engine = ?"
            params.append(engine)
            
        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return row['count']
