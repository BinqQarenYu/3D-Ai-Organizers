import asyncio
import logging
import uuid
import traceback
from typing import Dict, Set

from backend.storage.base import StorageProvider # type: ignore
from backend.indexer.asset_record import load_asset_metadata, save_asset_metadata, create_initial_record # type: ignore

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".fbx", ".obj", ".blend", ".gltf", ".glb", 
    ".png", ".jpg", ".jpeg", ".skp", ".max", 
    ".rvt", ".rft", ".rfa", ".dwg", ".stl", ".ply", ".dae",
    ".3mf", ".3dm", ".ifc"
}

class WatchService:
    def __init__(self, provider: StorageProvider):
        self.provider = provider
        self._is_running = False
        self._task: 'asyncio.Task | None' = None # type: ignore

    def start(self, interval_seconds: int = 15):
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._watch_loop(interval_seconds))
        logger.info(f"WatchService started, scanning every {interval_seconds} seconds.")

    def stop(self):
        self._is_running = False
        if self._task:
            self._task.cancel() # type: ignore
            logger.info("WatchService stopped.")

    async def _watch_loop(self, interval: int):
        while self._is_running:
            try:
                self.scan_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in WatchService loop: {e}\n{traceback.format_exc()}")
            
            await asyncio.sleep(interval)

    def scan_now(self):
        logger.info("Starting background scan of originals...")
        
        # Load existing indexed keys
        assets_ref = self.provider.ref("assets")
        self.provider.mkdirs(assets_ref)
        
        indexed_files = set()
        for item in self.provider.listdir(assets_ref):
            if not item.name.endswith(".json"):
                continue
            asset_id = item.name[:-5]  # strip .json
            metadata = load_asset_metadata(self.provider, asset_id)
            if metadata and "files" in metadata:
                ori_file = metadata["files"].get("original_filename")
                if ori_file:
                    indexed_files.add(ori_file)
                    
        # Scan 'originals' directory
        orig_ref = self.provider.ref("originals")
        self.provider.mkdirs(orig_ref)
        items = list(self.provider.walk(orig_ref, extensions=SUPPORTED_EXTENSIONS))
        
        new_assets_count = 0
        for item in items:
            key = item.ref.key
            if key not in indexed_files:
                asset_id = str(uuid.uuid4()).replace("-", "")
                
                logger.info(f"Found new unindexed asset: {key}")
                
                # Create initial metadata
                record = create_initial_record(asset_id, key)
                
                # Append basic metadata based on `item`
                record["files"]["size_bytes"] = item.size_bytes
                
                # Save
                save_asset_metadata(self.provider, asset_id, record)
                indexed_files.add(key)
                new_assets_count += 1
                
        if new_assets_count > 0:
            logger.info(f"Scan finished. Added {new_assets_count} new assets.")
        else:
            logger.debug("Scan finished. No new assets found.")
