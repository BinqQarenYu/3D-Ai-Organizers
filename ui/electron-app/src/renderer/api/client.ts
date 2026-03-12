import { AssetListItem, SearchResponse, SimilarResultItem, AssetDetail } from './types';

const API_BASE_URL = 'http://127.0.0.1:17831/api/v1';

class ApiClient {
    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...options?.headers as Record<string, string>,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    getPreviewUrl(assetId: string): string {
        return `${API_BASE_URL}/files/preview/${assetId}`;
    }

    async searchAssets(query: string, projectId?: string, offset: number = 0, limit: number = 50): Promise<SearchResponse> {
        let endpoint = '/search';
        if (projectId) endpoint += `?project_id=${projectId}`;

        return this.request<SearchResponse>(endpoint, {
            method: 'POST',
            body: JSON.stringify({ query, offset, limit })
        });
    }

    async getRecentAssets(projectId?: string): Promise<AssetListItem[]> {
        let endpoint = '/assets?sort=recent&limit=12';
        if (projectId) endpoint += `&project_id=${projectId}`;

        // Ensure proper unwrapping of data depending on backend schema
        const res = await this.request<any>(endpoint);
        return res.data?.items || [];
    }

    async getAssetDetails(assetId: string): Promise<any> {
        const res = await this.request<any>(`/assets/${assetId}`);
        const d = res.data;
        if (!d) return null;

        // Derive original_ext from the stored key (e.g. "originals/<assetId>.obj")
        const key: string = d.paths?.original_ref?.key || '';
        const originalExt = key ? '.' + key.split('.').pop() : '';

        return {
            ...d,
            asset_id: d.asset_id,
            display_name: d.identity?.display_name || '',
            status: d.status?.state || 'indexed',
            original_ext: originalExt,
            category: d.classification?.category,
            tags: d.classification?.tags || [],
            vertex_count: d.vision?.metadata_3d?.vertex_count,
            created_at: d.timestamps?.created_at,
        };
    }

    async openOriginal(assetId: string): Promise<void> {
        return this.request<void>('/files/open-original', {
            method: 'POST',
            body: JSON.stringify({ asset_id: assetId })
        });
    }

    async findSimilar(assetId: string, projectId: string, topK: number = 24, threshold: number = 0.75): Promise<SimilarResultItem[]> {
        const formData = new URLSearchParams();
        formData.append('mode', 'by_asset');
        formData.append('project_id', projectId);
        formData.append('asset_id', assetId);
        formData.append('top_k', topK.toString());
        formData.append('threshold', threshold.toString());

        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {
            'Content-Type': 'application/x-www-form-urlencoded'
        };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${API_BASE_URL}/vision/similar`, {
            method: 'POST',
            headers,
            body: formData.toString()
        });

        if (!res.ok) throw new Error('API Error');
        const data = await res.json();
        return data.data?.results || [];
    }

    async uploadFile(file: File, projectId: string): Promise<{ asset_id: string }> {
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const formData = new FormData();
        formData.append('project_id', projectId);
        formData.append('file', file);

        const res = await fetch(`${API_BASE_URL}/files/upload`, {
            method: 'POST',
            headers,
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err?.detail || `Upload failed: ${res.statusText}`);
        }
        const data = await res.json();
        return data.data;
    }

    async importLocalFile(filePath: string, projectId: string): Promise<{ asset_id: string }> {
        const token = localStorage.getItem('token');
        const headers: Record<string, string> = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const formData = new FormData();
        formData.append('project_id', projectId);
        formData.append('file_path', filePath);

        const res = await fetch(`${API_BASE_URL}/files/import-local`, {
            method: 'POST',
            headers,
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err?.detail || `Import failed: ${res.statusText}`);
        }
        const data = await res.json();
        return data.data;
    }
}

export const api = new ApiClient();
