from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Generic Base
class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class MetaInfo(BaseModel):
    execution_ms: Optional[int] = None
    note: Optional[str] = None

class ApiResponse(BaseModel):
    ok: bool = True
    error: Optional[ErrorInfo] = None
    meta: Optional[MetaInfo] = None

# Health & Settings
class HealthFeatures(BaseModel):
    watcher: bool
    preview_generation: bool
    vision_embeddings: bool
    similarity_search: bool
    ai_optional: bool
    cloud_providers: bool

class StorageInfo(BaseModel):
    provider: str
    root: str

class HealthData(BaseModel):
    service: str
    version: str
    storage: StorageInfo
    features: HealthFeatures

class HealthResponse(ApiResponse):
    data: Optional[HealthData] = None

class ThresholdSettings(BaseModel):
    duplicate: float
    similar: float

class PagingSettings(BaseModel):
    default_limit: int = 50
    max_limit: int = 200

class SettingsData(BaseModel):
    assets_root: str
    thresholds: ThresholdSettings
    paging: PagingSettings

class SettingsResponse(ApiResponse):
    data: Optional[SettingsData] = None

# Storage
class StorageRefSchema(BaseModel):
    provider: str
    root_id: str
    key: str

# Asset Listing
class AssetListItem(BaseModel):
    asset_id: str
    display_name: str
    name_source: str
    preview_url: Optional[str] = None
    original_ext: Optional[str] = None
    status: str
    needs_review: bool = False
    updated_at: Optional[str] = None

class AssetListData(BaseModel):
    total: int
    offset: int
    limit: int
    items: List[AssetListItem]

class AssetListResponse(ApiResponse):
    data: Optional[AssetListData] = None

# Asset Details
class IdentityInfo(BaseModel):
    display_name: str
    name_source: str
    confidence: float

class ClassificationInfo(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    confidence: float

class Meta3D(BaseModel):
    bounding_box: Optional[List[float]] = None
    vertex_count: Optional[int] = None
    material_count: Optional[int] = None

class BimMetadata(BaseModel):
    element_counts: Optional[Dict[str, int]] = None
    parameters: Optional[Dict[str, Any]] = None
    format_specific_data: Optional[Dict[str, Any]] = None

class VisionInfo(BaseModel):
    embedding_dim: Optional[int] = None
    engine: Optional[str] = None
    embedding_created: Optional[str] = None
    metadata_3d: Optional[Meta3D] = None
    metadata_bim: Optional[BimMetadata] = None

class StatusInfo(BaseModel):
    state: str
    needs_review: bool
    issues: List[str] = Field(default_factory=list)

class AssetTimestamps(BaseModel):
    created_at: Optional[str] = None
    indexed_at: Optional[str] = None
    last_updated: Optional[str] = None

class PathsInfo(BaseModel):
    original_ref: StorageRefSchema
    preview_ref: Optional[StorageRefSchema] = None

class AssetDetailsData(BaseModel):
    asset_id: str
    storage: StorageInfo
    paths: PathsInfo
    identity: IdentityInfo
    classification: ClassificationInfo
    vision: VisionInfo
    status: StatusInfo
    timestamps: AssetTimestamps

class AssetDetailsResponse(ApiResponse):
    data: Optional[AssetDetailsData] = None

# Search
class SearchFilters(BaseModel):
    category: Optional[str] = None
    ext: Optional[List[str]] = None
    state: Optional[List[str]] = None

class SearchRequest(BaseModel):
    query: str
    offset: int = 0
    limit: int = 50
    filters: Optional[SearchFilters] = None

class SearchResponse(ApiResponse):
    data: Optional[AssetListData] = None

# Vision Similarity
class SimilarResultItem(BaseModel):
    asset_id: str
    similarity: float
    preview_url: Optional[str] = None
    display_name: Optional[str] = None

class SimilarQueryInfo(BaseModel):
    asset_id: Optional[str] = None

class SimilarData(BaseModel):
    query: SimilarQueryInfo
    results: List[SimilarResultItem]

class SimilarResponse(ApiResponse):
    data: Optional[SimilarData] = None

# Asset Creation
class AssetCreateRequest(BaseModel):
    reference_url: str
    name: Optional[str] = None

class AssetCreateData(BaseModel):
    asset_id: str

class AssetCreateResponse(ApiResponse):
    data: Optional[AssetCreateData] = None

# File Operations
class OpenOriginalRequest(BaseModel):
    asset_id: str

class OpenOriginalData(BaseModel):
    opened: bool

class OpenOriginalResponse(ApiResponse):
    data: Optional[OpenOriginalData] = None
