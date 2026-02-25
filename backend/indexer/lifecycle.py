from datetime import datetime
import logging
from .asset_record import load_asset_metadata, save_asset_metadata
from ..storage.base import StorageProvider

logger = logging.getLogger(__name__)

def update_status(provider: StorageProvider, asset_id: str, new_state: str, issue: str = None) -> bool:
    """Helper to cleanly transition asset states."""
    data = load_asset_metadata(provider, asset_id)
    if not data:
        logger.error(f"Cannot update status for unknown asset {asset_id}")
        return False
        
    if "status" not in data:
        data["status"] = {}
        
    data["status"]["state"] = new_state
    
    if issue:
        if "issues" not in data["status"]:
            data["status"]["issues"] = []
        data["status"]["issues"].append(issue)
        
    data.setdefault("timestamps", {})["last_updated"] = datetime.utcnow().isoformat()
    if new_state == "indexed":
         data["timestamps"]["indexed_at"] = data["timestamps"]["last_updated"]
         
    save_asset_metadata(provider, asset_id, data)
    return True

def mark_preview_missing(provider: StorageProvider, asset_id: str) -> bool:
    return update_status(provider, asset_id, "preview_missing")

def mark_preview_ready(provider: StorageProvider, asset_id: str) -> bool:
    return update_status(provider, asset_id, "preview_ready")

def mark_indexed(provider: StorageProvider, asset_id: str) -> bool:
    return update_status(provider, asset_id, "indexed")

def mark_error(provider: StorageProvider, asset_id: str, issue: str) -> bool:
    return update_status(provider, asset_id, "error", issue)
