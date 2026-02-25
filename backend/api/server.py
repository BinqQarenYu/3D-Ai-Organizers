import os
import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from backend.config.settings import settings
from backend.config.logging import logger
from backend.storage.local_disk import LocalDiskProvider
from backend.vision.vector_store import EmbeddingStore
from backend.vision.embedder import StubEmbedder
from backend.vision.similarity_service import SimilarityService
from backend.api import schemas

app = FastAPI(title="AI Asset Memory Backend", version="0.1.0")

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

@app.on_event("startup")
async def startup_event():
    global storage_provider, embedding_store, similarity_service
    
    logger.info("Initializing Backend Services...")
    storage_provider = LocalDiskProvider(settings.assets_root)
    
    # Store sqlite DB in the standard index directory under storage root
    index_dir = Path(settings.assets_root) / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    
    embedding_store = EmbeddingStore(str(index_dir / "embeddings.sqlite"))
    embedder = StubEmbedder()
    similarity_service = SimilarityService(embedding_store, embedder)
    
    logger.info("Backend Services Initialized.")

@app.get("/api/v1/health", response_model=schemas.HealthResponse)
async def get_health():
    features = schemas.HealthFeatures(
        watcher=False,
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
    asset_id: Optional[str] = Form(None),
    top_k: int = Form(24),
    threshold: float = Form(0.70),
    file: Optional[UploadFile] = File(None)
):
    if mode not in ("by_asset", "by_image"):
        raise HTTPException(status_code=400, detail="Invalid mode, must be by_asset or by_image")

    results = []
    query_info = schemas.SimilarQueryInfo()

    if mode == "by_asset":
        if not asset_id:
            raise HTTPException(status_code=400, detail="asset_id is required for by_asset mode")
        query_info.asset_id = asset_id
        
        sims = similarity_service.similar_by_asset(asset_id, top_k, threshold)
        for s in sims:
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
            sims = similarity_service.similar_by_image_path(temp_path, top_k, threshold)
            for s in sims:
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

# --- Stubs for Frontend Integration Testing ---

@app.post("/api/v1/search", response_model=schemas.SearchResponse)
async def search_assets(req: schemas.SearchRequest):
    # Stub response matching exactly the parameters from UI limits
    items = []
    # Just returning some fake elements so the frontend paginates correctly
    for i in range(req.limit):
        id_str = f"stub_{req.offset + i}"
        items.append(schemas.AssetListItem(
            asset_id=id_str,
            display_name=f"Search Result {req.query} #{req.offset + i}",
            name_source="stub",
            status="indexed",
            original_ext=".fbx"
        ))
    
    data = schemas.AssetListData(
        total=5000,
        offset=req.offset,
        limit=req.limit,
        items=items
    )
    return schemas.SearchResponse(data=data)

@app.get("/api/v1/assets", response_model=schemas.AssetListResponse)
async def list_recent_assets():
    # Stub response for recent assets home page
    items = [
        schemas.AssetListItem(
            asset_id=f"recent_{i}",
            display_name=f"Recent Asset {i}",
            name_source="stub",
            status="indexed",
            original_ext=".rvt"
        ) for i in range(6)
    ]
    data = schemas.AssetListData(total=6, offset=0, limit=12, items=items)
    return schemas.AssetListResponse(data=data)

@app.get("/api/v1/assets/{asset_id}", response_model=schemas.AssetDetailsResponse)
async def get_asset_details(asset_id: str):
    # Stub response
    storage = schemas.StorageInfo(provider="local_disk", root=settings.assets_root)
    paths = schemas.PathsInfo(original_ref=schemas.StorageRefSchema(provider="local",root_id="1",key="fake"))
    ident = schemas.IdentityInfo(display_name=f"Detail View {asset_id}", name_source="stub", confidence=1.0)
    classif = schemas.ClassificationInfo(category="Furniture", tags=["Wood", "Interior"], confidence=0.8)
    vis = schemas.VisionInfo(embedding_dim=768, engine="stub", embedding_created="now")
    stat = schemas.StatusInfo(state="indexed", needs_review=False)
    times = schemas.AssetTimestamps()

    data = schemas.AssetDetailsData(
        asset_id=asset_id, storage=storage, paths=paths,
        identity=ident, classification=classif, vision=vis, status=stat, timestamps=times
    )
    return schemas.AssetDetailsResponse(data=data)

@app.post("/api/v1/files/open-original")
async def open_original(req: schemas.OpenOriginalRequest):
    # Stub returning success
    return schemas.OpenOriginalResponse(data=schemas.OpenOriginalData(opened=True))

@app.get("/api/v1/files/preview/{asset_id}")
async def get_preview_image(asset_id: str):
    # Instead of sending a real file, just 404 or send transparent 1x1 for now so frontend handles onError
    raise HTTPException(status_code=404, detail="Preview not generated yet")
