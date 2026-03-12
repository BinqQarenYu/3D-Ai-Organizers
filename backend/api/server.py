# pyre-ignore-all-errors
# pyright: reportMissingImports=false
# Backend server for 3D AI Organizers
import os
import shutil
import tempfile
from pathlib import Path
import itertools
from typing import Optional, List, Dict, Any, cast # type: ignore
from fastapi import FastAPI, HTTPException, UploadFile, Form, File, Depends, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.staticfiles import StaticFiles # type: ignore
from fastapi.responses import FileResponse # type: ignore
from bson import ObjectId # type: ignore
import uuid # type: ignore

from backend.config.settings import settings # type: ignore
from backend.config.logging import logger # type: ignore
from backend.storage.local_disk import LocalDiskProvider # type: ignore
from backend.vision.vector_store import EmbeddingStore # type: ignore
from backend.vision.embedder import StubEmbedder # type: ignore
from backend.vision.similarity_service import SimilarityService # type: ignore
from backend.watcher.watch_service import WatchService # type: ignore
from backend.indexer.asset_record import load_asset_metadata, create_initial_record, save_asset_metadata # type: ignore
from backend.api import schemas # type: ignore
from backend.api.auth import get_current_user # type: ignore
from backend.api.database import init_db, get_db # type: ignore
from backend.api.routes import auth, projects # type: ignore
from backend.api.extract_3d import extract_3d_metadata # type: ignore
from backend.api.proxy import router as proxy_router # type: ignore

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
storage_provider: LocalDiskProvider = None # type: ignore
embedding_store: EmbeddingStore = None # type: ignore
similarity_service: SimilarityService = None # type: ignore
watch_service: WatchService = None # type: ignore


@app.on_event("startup")
async def startup_event():
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
        provider=cast(LocalDiskProvider, storage_provider).provider_name(),
        root=cast(LocalDiskProvider, storage_provider).to_local_path(cast(LocalDiskProvider, storage_provider).ref("")) or settings.assets_root
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
        
        # Use cast for global service call and pass project_id directly
        results = await cast(SimilarityService, similarity_service).similar_by_asset(
            asset_id=asset_id,
            project_id=project_id,
            top_k=top_k,
            threshold=threshold
        )
        
        # Deriving preview URLs for results
        items: List[schemas.SimilarResultItem] = []
        for r in results:
            aid = r.get("asset_id")
            items.append(schemas.SimilarResultItem(
                asset_id=aid,
                similarity=r.get("score", 0),
                preview_url=f"/api/v1/files/preview/{aid}",
                display_name=r.get("display_name")
            ))

    elif mode == "by_image":
        if not file:
            raise HTTPException(status_code=400, detail="file is required for by_image mode")
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        try:
            results = await cast(SimilarityService, similarity_service).similar_by_image_path(tmp_path, project_id, top_k, threshold)
            
            items: List[schemas.SimilarResultItem] = []
            for r in results:
                aid = r.get("asset_id")
                items.append(schemas.SimilarResultItem(
                    asset_id=aid,
                    similarity=r.get("score", 0),
                    preview_url=f"/api/v1/files/preview/{aid}",
                    display_name=r.get("display_name")
                ))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    data = schemas.SimilarData(query=query_info, results=items)
    return schemas.SimilarResponse(data=data)

# --- API Implementations ---


from bson.errors import InvalidId # type: ignore

async def check_project_access(project_id: Optional[str], current_user: dict):
    if not project_id:
        return
    if current_user.get("role") == "admin":
        return True # Admins can access all projects

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

def _load_all_records(project_id: Optional[str] = None) -> List[dict]:
    records = []
    if not storage_provider:
        logger.warning("Storage provider not initialized, cannot load records.")
        return []

    assets_ref = cast(LocalDiskProvider, storage_provider).ref("assets")
    if cast(LocalDiskProvider, storage_provider).exists(assets_ref):
        for item in cast(LocalDiskProvider, storage_provider).listdir(assets_ref):
            if item.name.endswith(".json"):
                asset_id = item.name[:-5]
                data = load_asset_metadata(cast(LocalDiskProvider, storage_provider), asset_id)
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

    save_asset_metadata(cast(LocalDiskProvider, storage_provider), asset_id, record)

    return schemas.AssetCreateResponse(data=schemas.AssetCreateData(asset_id=asset_id))

@app.post("/api/v1/search", response_model=schemas.SearchResponse)
async def search_assets(req: schemas.SearchRequest, project_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    await check_project_access(req.filters.category if req.filters else None, current_user)
    all_records = _load_all_records(project_id=None) # We don't have project_id in search yet safely
    
    items: List[schemas.AssetListItem] = []
    
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
    # Ensure indices are integers for slicing
    start = int(req.offset) if req.offset is not None else 0
    end = (int(req.offset) + int(req.limit)) if (req.offset is not None and req.limit is not None) else len(items)
    # Use islice to work around slicing type errors
    paged = list(itertools.islice(items, start, end))
    
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
    
    items: List[schemas.AssetListItem] = []
    # Derive items as list to avoid slice indexing troubles
    records_list = list(all_records)
    for r in list(itertools.islice(records_list, 12)):
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
    record = load_asset_metadata(cast(LocalDiskProvider, storage_provider), asset_id)
    if record and record.get("project_id"):
        await check_project_access(record.get("project_id"), current_user)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    storage = schemas.StorageInfo(provider="local_disk", root=settings.assets_root)
    
    original_file = record.get("files", {}).get("original_filename", "")
    orig_ref_data = record.get("files", {}).get("original_ref")
    
    if orig_ref_data:
        original_ref = schemas.StorageRefSchema(
            provider=orig_ref_data.get("provider", "local"),
            root_id=str(cast(LocalDiskProvider, storage_provider).root_id),
            key=orig_ref_data.get("key", "")
        )
    else:
        original_ref = schemas.StorageRefSchema(
            provider="local",
            root_id=str(cast(LocalDiskProvider, storage_provider).root_id),
            key=original_file
        )
        
    paths = schemas.PathsInfo(original_ref=original_ref)
    
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
    record = load_asset_metadata(cast(LocalDiskProvider, storage_provider), req.asset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    orig_rel_path = record.get("files", {}).get("original_filename")
    if not orig_rel_path:
        raise HTTPException(status_code=404, detail="No original file path in metadata")
        
    full_path = cast(LocalDiskProvider, storage_provider).to_local_path(cast(LocalDiskProvider, storage_provider).ref(orig_rel_path))
    
    if os.path.exists(full_path):
        import subprocess
        try:
              # On Windows, os.startfile is best.
              if os.name == 'nt' and hasattr(os, 'startfile'):
                  getattr(os, 'startfile')(full_path)
              else:
                  # Fallback for other systems
                  import platform
                  opener = "open" if platform.system() == "Darwin" else "xdg-open"
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
        full_path = cast(LocalDiskProvider, storage_provider).to_local_path(cast(LocalDiskProvider, storage_provider).ref(orig_rel_path))
        if os.path.exists(full_path):
            return FileResponse(full_path)
            
    # Instead of sending a real file, just 404 or send transparent 1x1 for now so frontend handles onError
    raise HTTPException(status_code=404, detail="Preview not generated yet")


# --- File Upload ---

ALLOWED_UPLOAD_EXTENSIONS = {
    ".obj", ".glb", ".gltf", ".fbx", ".blend", 
    ".skp", ".max", ".rvt", ".rft", ".stl", ".ply", 
    ".dae", ".3mf", ".3dm", ".ifc",
    ".png", ".jpg", ".jpeg"
}

@app.post("/api/v1/files/upload", response_model=schemas.AssetCreateResponse)
async def upload_file(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    await check_project_access(project_id, current_user)

    original_filename = file.filename or "unknown"
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")

    # Create unique asset ID + storage key
    asset_id = str(uuid.uuid4()).replace("-", "")
    storage_key = f"originals/{asset_id}{ext}"
    dest_ref = cast(LocalDiskProvider, storage_provider).ref(storage_key)

    # Save uploaded bytes to originals/
    orig_dir = Path(settings.assets_root) / "originals"
    orig_dir.mkdir(parents=True, exist_ok=True)
    dest_path = Path(settings.assets_root) / storage_key

    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    logger.info(f"Uploaded file saved to: {dest_path}")

    # Create and save asset record
    record = create_initial_record(
        asset_id=asset_id,
        original_filename=storage_key,
        project_id=project_id,
        owner_id=current_user.get("id")
    )
    record["identity"]["display_name"] = os.path.splitext(original_filename)[0]

    # Extract 3D metadata synchronously
    try:
        meta3d, metabim = extract_3d_metadata(str(dest_path))
        if meta3d or metabim:
            if "vision" not in record:
                record["vision"] = {}
            if meta3d:
                record["vision"]["metadata_3d"] = meta3d
            if metabim:
                record["vision"]["metadata_bim"] = metabim
    except Exception as e:
        logger.warning(f"3D metadata extraction failed for {original_filename}: {e}")

    record["status"]["state"] = "indexed"
    save_asset_metadata(storage_provider, asset_id, record)

    return schemas.AssetCreateResponse(data=schemas.AssetCreateData(asset_id=asset_id))


@app.post("/api/v1/files/import-local", response_model=schemas.AssetCreateResponse)
async def import_local_file(
    project_id: str = Form(...),
    file_path: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    await check_project_access(project_id, current_user)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Local file not found.")

    original_filename = os.path.basename(file_path)
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    asset_id = str(uuid.uuid4()).replace("-", "")
    storage_key = f"originals/{asset_id}{ext}"
    dest_path = Path(settings.assets_root) / storage_key

    orig_dir = Path(settings.assets_root) / "originals"
    orig_dir.mkdir(parents=True, exist_ok=True)

    # Copy file from local disk to assets_root
    shutil.copy(file_path, dest_path)
    logger.info(f"Imported local file {file_path} to: {dest_path}")

    # Create and save asset record
    record = create_initial_record(
        asset_id=asset_id,
        original_filename=storage_key,
        project_id=project_id,
        owner_id=current_user.get("id")
    )
    record["identity"]["display_name"] = os.path.splitext(original_filename)[0]

    # Extract 3D metadata synchronously
    try:
        meta3d, metabim = extract_3d_metadata(str(dest_path))
        if meta3d or metabim:
            if "vision" not in record:
                record["vision"] = {}
            if meta3d:
                record["vision"]["metadata_3d"] = meta3d
            if metabim:
                record["vision"]["metadata_bim"] = metabim
    except Exception as e:
        logger.warning(f"3D metadata extraction failed for {original_filename}: {e}")

    record["status"]["state"] = "indexed"
    save_asset_metadata(storage_provider, asset_id, record)

    return schemas.AssetCreateResponse(data=schemas.AssetCreateData(asset_id=asset_id))
