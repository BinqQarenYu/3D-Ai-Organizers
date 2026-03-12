export interface AssetListItem {
    asset_id: string;
    display_name: string;
    preview_url?: string;
    original_ext?: string;
    status: string;
    needs_review?: boolean;
}

export interface SearchResponse {
    items: AssetListItem[];
    total: number;
    offset: number;
    limit: number;
}

export interface SimilarResultItem extends AssetListItem {
    similarity_score?: number;
}

export interface AssetDetail extends AssetListItem {
    category?: string;
    tags?: string[];
    file_size?: number;
    created_at?: string;
    updated_at?: string;
    vertex_count?: number;
    material_count?: number;
    // Other fields as defined by the backend...
}
