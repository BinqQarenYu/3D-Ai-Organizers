import json
from typing import Dict, Any, Optional
from ..storage.base import StorageProvider, StorageRef

def load_asset_metadata(provider: StorageProvider, asset_id: str) -> Optional[Dict[str, Any]]:
    """Loads a JSON metadata file from the assets/ folder."""
    key = provider.join("assets", f"{asset_id}.json")
    ref = provider.ref(key)
    
    if not provider.exists(ref):
        return None
        
    try:
        raw_bytes = provider.get_bytes(ref)
        return json.loads(raw_bytes.decode('utf-8'))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load asset metadata {asset_id}: {e}")
        return None

def save_asset_metadata(provider: StorageProvider, asset_id: str, data: Dict[str, Any]) -> None:
    """Saves a JSON metadata dict to the assets/ folder."""
    key = provider.join("assets", f"{asset_id}.json")
    ref = provider.ref(key)
    
    raw_bytes = json.dumps(data, indent=2).encode('utf-8')
    provider.put_bytes(ref, raw_bytes, overwrite=True)

def create_initial_record(asset_id: str, original_filename: str) -> Dict[str, Any]:
    """Scaffolds a new empty record."""
    from datetime import datetime
    now = datetime.utcnow().isoformat()
    return {
        "asset_id": asset_id,
        "identity": {
            "display_name": original_filename.split('.')[0],
            "name_source": "filename",
            "confidence": 1.0
        },
        "files": {
            "original_filename": original_filename,
            "preview_exists": False
        },
        "status": {
            "state": "raw",
            "needs_review": False,
            "issues": []
        },
        "timestamps": {
            "created_at": now,
            "last_updated": now
        }
    }
