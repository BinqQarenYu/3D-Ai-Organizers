import os
import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional

from backend.config.settings import settings
from backend.config.logging import logger
from backend.storage.local_disk import LocalDiskProvider
from backend.vision.vector_store import EmbeddingStore
from backend.vision.embedder import StubEmbedder
from backend.vision.similarity_service import SimilarityService
from backend.watcher.watch_service import WatchService
import uuid
from backend.indexer.asset_record import load_asset_metadata, create_initial_record, save_asset_metadata
from backend.api import schemas
from backend.api.auth import get_current_user
from fastapi import Depends
from backend.api.database import get_db
from bson import ObjectId



from .database import init_db
from .routes import auth, projects
from fastapi import Request

from backend.api.extract_3d import extract_3d_metadata
from backend.api.proxy import router as proxy_router

app = FastAPI(title="AI Asset Memory Backend", version="0.1.0")

# Include Proxy router
app.include_router(proxy_router)

# Include Auth & Project routers
app.include_router(auth.router)
app.include_router(projects.router)


# Allow all CORS for desktop Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services references
storage_provider: LocalDiskProvider
embedding_store: EmbeddingStore
similarity_service: SimilarityService
watch_service: WatchService


@app.on_event("startup")
async def startup_event():
    from .database import init_db
    try:
        await init_db()
        logger.info("MongoDB connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")

    global storage_provider, embedding_store, similarity_service
    
    logger.info("Initializing Backend Services...")
    storage_provider = LocalDiskProvider(settings.assets_root)
    
    # Store sqlite DB in the standard index directory under storage root
    index_dir = Path(settings.assets_root) / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    
    embedding_store = EmbeddingStore(str(index_dir / "embeddings.sqlite"))
    embedder = StubEmbedder()
    similarity_service = SimilarityService(embedding_store, embedder)
    
    # Mount the /uploads route for static file serving
    uploads_dir = Path(settings.assets_root) / "originals"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    # Start the background background watcher
    watch_service = WatchService(storage_provider)
    watch_service.start(interval_seconds=15)
    
    logger.info("Backend Services Initialized.")

@app.get("/api/v1/health", response_model=schemas.HealthResponse)
async def get_health():
    features = schemas.HealthFeatures(
        watcher=True,
        preview_generation=False,
        vision_embeddings=True,
        similarity_search=True,
        ai_optional=False,
        cloud_providers=False
    )
    
    storage = schemas.StorageInfo(
        provider=storage_provider.provider_name(),
        root=storage_provider.to_local_path(storage_provider.ref("")) or settings.assets_root
    )
    
    data = schemas.HealthData(
        service="AI Asset Memory Backend",
        version="0.1.0",
        storage=storage,
        features=features
    )
    
    return schemas.HealthResponse(data=data)

@app.get("/api/v1/settings", response_model=schemas.SettingsResponse)
async def get_settings():
    data = schemas.SettingsData(
        assets_root=settings.assets_root,
        thresholds=schemas.ThresholdSettings(
            duplicate=settings.duplicate_threshold,
            similar=settings.similar_threshold
        ),
        paging=schemas.PagingSettings()
    )
    return schemas.SettingsResponse(data=data)


@app.post("/api/v1/vision/similar", response_model=schemas.SimilarResponse)
async def find_similar(
    mode: str = Form(...),
    project_id: str = Form(...),
    asset_id: Optional[str] = Form(None),
    top_k: int = Form(24),
    threshold: float = Form(0.70),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    await check_project_access(project_id, current_user)

    if mode not in ("by_asset", "by_image"):
        raise HTTPException(status_code=400, detail="Invalid mode, must be by_asset or by_image")

    results = []
    query_info = schemas.SimilarQueryInfo()

    if mode == "by_asset":
        if not asset_id:
            raise HTTPException(status_code=400, detail="asset_id is required for by_asset mode")
        query_info.asset_id = asset_id
        
        sims = similarity_service.similar_by_asset(asset_id, top_k * 5, threshold) # fetch more to filter
        for s in sims:
            record = load_asset_metadata(storage_provider, s.asset_id)
            if not record or record.get("project_id") != project_id:
                continue
            if len(results) >= top_k:
                break
            results.append(schemas.SimilarResultItem(
                asset_id=s.asset_id,
                similarity=s.similarity,
                preview_url=f"/api/v1/files/preview/{s.asset_id}", # Placeholder
                display_name=f"Asset {s.asset_id}" # Placeholder
            ))

    elif mode == "by_image":
        if not file:
            raise HTTPException(status_code=400, detail="file is required for by_image mode")
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tf:
            shutil.copyfileobj(file.file, tf)
            temp_path = tf.name
            
        try:
            sims = similarity_service.similar_by_image_path(temp_path, top_k * 5, threshold)
            for s in sims:
                record = load_asset_metadata(storage_provider, s.asset_id)
                if not record or record.get("project_id") != project_id:
                    continue
                if len(results) >= top_k:
                    break
                results.append(schemas.SimilarResultItem(
                    asset_id=s.asset_id,
                    similarity=s.similarity,
                    preview_url=f"/api/v1/files/preview/{s.asset_id}", # Placeholder
                    display_name=f"Asset {s.asset_id}" # Placeholder
                ))
        finally:
             if os.path.exists(temp_path):
                 os.remove(temp_path)

    data = schemas.SimilarData(query=query_info, results=results)
    return schemas.SimilarResponse(data=data)

# --- API Implementations ---


from bson.errors import InvalidId

async def check_project_access(project_id: str, current_user: dict):
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    db = get_db()
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid project_id format")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user["id"] != project["owner_id"] and current_user["id"] not in project.get("members", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return True

def _load_all_records(project_id: str = None):
    assets_ref = storage_provider.ref("assets")
    records = []
    if storage_provider.exists(assets_ref):
        for item in storage_provider.listdir(assets_ref):
            if item.name.endswith(".json"):
                asset_id = item.name[:-5]
                data = load_asset_metadata(storage_provider, asset_id)
                if data:
                    # Filter by project_id
                    if project_id and data.get("project_id") != project_id:
                        continue
                    records.append(data)
    # Sort descending by creation date (newest first)
    records.sort(key=lambda x: x.get("timestamps", {}).get("created_at", ""), reverse=True)
    return records

@app.post("/api/v1/assets", response_model=schemas.AssetCreateResponse)
async def create_asset(req: schemas.AssetCreateRequest, project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    await check_project_access(project_id, current_user)
    asset_id = str(uuid.uuid4()).replace("-", "")

    # Generate a sensible name if none provided
    name = req.name
    if not name:
        name = req.reference_url.split("/")[-1]

    record = create_initial_record(asset_id, name, project_id=project_id, owner_id=current_user.get('id'))

    # Store reference url instead of local original file
    record["files"]["original_filename"] = req.reference_url

    # Extract 3D Metadata if it's referenced
    meta3d, metabim = extract_3d_metadata(req.reference_url)
    if meta3d or metabim:
        if "vision" not in record:
            record["vision"] = {}
        if meta3d:
            record["vision"]["metadata_3d"] = meta3d
        if metabim:
            record["vision"]["metadata_bim"] = metabim

    save_asset_metadata(storage_provider, asset_id, record)

    return schemas.AssetCreateResponse(data=schemas.AssetCreateData(asset_id=asset_id))

@app.post("/api/v1/search", response_model=schemas.SearchResponse)
async def search_assets(req: schemas.SearchRequest, project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    await check_project_access(project_id, current_user)
    all_records = _load_all_records(project_id=project_id)
    items = []
    
    query = (req.query or "").lower().strip()
    
    for r in all_records:
        ident = r.get("identity", {})
        display_name = ident.get("display_name", "")
        # Basic filter
        if query and query not in display_name.lower():
             continue
             
        items.append(schemas.AssetListItem(
            asset_id=r.get("asset_id", ""),
            display_name=display_name,
            name_source=ident.get("name_source", "unknown"),
            status=r.get("status", {}).get("state", "indexed"),
            original_ext=os.path.splitext(r.get("files", {}).get("original_filename", ""))[1]
        ))
    
    total = len(items)
    paged = items[req.offset: req.offset + req.limit]
    
    data = schemas.AssetListData(
        total=total,
        offset=req.offset,
        limit=req.limit,
        items=paged
    )
    return schemas.SearchResponse(data=data)

@app.get("/api/v1/assets", response_model=schemas.AssetListResponse)
async def list_recent_assets(project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    await check_project_access(project_id, current_user)
    all_records = _load_all_records(project_id=project_id)
    
    items = []
    # Take top 12
    for r in all_records[:12]:
        items.append(schemas.AssetListItem(
            asset_id=r.get("asset_id", ""),
            display_name=r.get("identity", {}).get("display_name", ""),
            name_source=r.get("identity", {}).get("name_source", "unknown"),
            status=r.get("status", {}).get("state", "indexed"),
            original_ext=os.path.splitext(r.get("files", {}).get("original_filename", ""))[1]
        ))
        
    data = schemas.AssetListData(total=len(all_records), offset=0, limit=12, items=items)
    return schemas.AssetListResponse(data=data)

@app.get("/api/v1/assets/{asset_id}", response_model=schemas.AssetDetailsResponse)
async def get_asset_details(asset_id: str, current_user: dict = Depends(get_current_user)):
    record = load_asset_metadata(storage_provider, asset_id)
    if record and record.get("project_id"):
        await check_project_access(record.get("project_id"), current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    storage = schemas.StorageInfo(provider="local_disk", root=settings.assets_root)
    
    original_file = record.get("files", {}).get("original_filename", "")
    paths = schemas.PathsInfo(
        original_ref=schemas.StorageRefSchema(
            provider="local",
            root_id=storage_provider.root_id(),
            key=original_file
        )
    )
    
    ident_data = record.get("identity", {})
    ident = schemas.IdentityInfo(
        display_name=ident_data.get("display_name", ""),
        name_source=ident_data.get("name_source", ""),
        confidence=ident_data.get("confidence", 1.0)
    )
    classif = schemas.ClassificationInfo(category="Uncategorized", tags=[], confidence=0.0)
    vis_data = record.get("vision", {})
    vis = schemas.VisionInfo(
        embedding_dim=vis_data.get("embedding_dim", 0),
        engine=vis_data.get("engine", "none"),
        embedding_created=vis_data.get("embedding_created", ""),
        metadata_3d=vis_data.get("metadata_3d"),
        metadata_bim=vis_data.get("metadata_bim")
    )
    
    stat_data = record.get("status", {})
    stat = schemas.StatusInfo(state=stat_data.get("state", "indexed"), needs_review=stat_data.get("needs_review", False))
    
    ts_data = record.get("timestamps", {})
    times = schemas.AssetTimestamps(created_at=ts_data.get("created_at"), last_updated=ts_data.get("last_updated"))

    data = schemas.AssetDetailsData(
        asset_id=asset_id, storage=storage, paths=paths,
        identity=ident, classification=classif, vision=vis, status=stat, timestamps=times
    )
    return schemas.AssetDetailsResponse(data=data)

@app.post("/api/v1/files/open-original")
async def open_original(req: schemas.OpenOriginalRequest):
    record = load_asset_metadata(storage_provider, req.asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    orig_rel_path = record.get("files", {}).get("original_filename")
    if not orig_rel_path:
        raise HTTPException(status_code=404, detail="No original file path in metadata")
        
    full_path = storage_provider.to_local_path(storage_provider.ref(orig_rel_path))
    
    if os.path.exists(full_path):
        import subprocess
        try:
             # On Windows, os.startfile is best. Using subprocess for general safety.
             if os.name == 'nt':
                 os.startfile(full_path)
             else:
                 # Fallback for other systems (though user is on Windows)
                 opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
                 subprocess.call([opener, full_path])
             return schemas.OpenOriginalResponse(data=schemas.OpenOriginalData(opened=True))
        except Exception as e:
             logger.error(f"Failed to open file: {e}")
             raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail=f"File not found on disk: {full_path}")

@app.get("/api/v1/files/preview/{asset_id}")
async def get_preview_image(asset_id: str):
    record = load_asset_metadata(storage_provider, asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    orig_rel_path = record.get("files", {}).get("original_filename")
    if orig_rel_path:
        full_path = storage_provider.to_local_path(storage_provider.ref(orig_rel_path))
        if os.path.exists(full_path):
            from fastapi.responses import FileResponse
            return FileResponse(full_path)
            
    # Instead of sending a real file, just 404 or send transparent 1x1 for now so frontend handles onError
    raise HTTPException(status_code=404, detail="Preview not generated yet")
