import { AssetListItem, SearchResponse, SimilarResultItem, AssetDetail } from './types';

const API_BASE_URL = 'http://127.0.0.1:17831/api/v1';

class ApiClient {
    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    getPreviewUrl(assetId: string): string {
        return `${API_BASE_URL}/files/preview/${assetId}`;
    }

    async searchAssets(query: string, offset: number = 0, limit: number = 50): Promise<SearchResponse> {
        return this.request<SearchResponse>('/search', {
            method: 'POST',
            body: JSON.stringify({ query, offset, limit })
        });
    }

    async getRecentAssets(): Promise<AssetListItem[]> {
        // Assuming backend returns a list of recent assets here. We might reuse search with empty query and sort=recent
        const res = await this.request<{ items: AssetListItem[] }>('/assets?sort=recent&limit=12');
        return res.items;
    }

    async getAssetDetails(assetId: string): Promise<AssetDetail> {
        return this.request<AssetDetail>(`/assets/${assetId}`);
    }

    async openOriginal(assetId: string): Promise<void> {
        return this.request<void>('/files/open-original', {
            method: 'POST',
            body: JSON.stringify({ asset_id: assetId })
        });
    }

    async findSimilar(assetId: string, topK: number = 24, threshold: number = 0.75): Promise<SimilarResultItem[]> {
        const res = await this.request<{ items: SimilarResultItem[] }>('/vision/similar', {
            method: 'POST',
            body: JSON.stringify({ mode: 'by_asset', asset_id: assetId, top_k: topK, threshold })
        });
        return res.items;
    }
}

export const api = new ApiClient();
