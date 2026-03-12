import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import AssetGrid from '../components/AssetGrid';
import AssetDetailPanel from '../components/AssetDetailPanel';
import { api } from '../api/client';
import { AssetListItem } from '../api/types';
import { statusBus } from '../components/StatusBar';
import { useProject } from '../contexts/ProjectContext';


const PAGE_SIZE = 50;

const SearchResults: React.FC = () => {
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const { selectedProject } = useProject();

    const navigate = useNavigate();

    const [assets, setAssets] = useState<AssetListItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [offset, setOffset] = useState(0);
    const [total, setTotal] = useState(0);
    const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

    const observer = useRef<IntersectionObserver | null>(null);
    const lastElementRef = useCallback((node: HTMLDivElement | null) => {
        if (loading) return;
        if (observer.current) observer.current.disconnect();

        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                setOffset(prev => prev + PAGE_SIZE);
            }
        });

        if (node) observer.current.observe(node);
    }, [loading, hasMore]);

    useEffect(() => {
        // Reset state on new query
        setAssets([]);
        setOffset(0);
        setHasMore(true);
        setTotal(0);
    }, [query, selectedProject?.id]);

    // Append new items
    useEffect(() => {
        const fetchResults = async () => {
            if (!query) return;

            setLoading(true);
            statusBus.emit(`Searching for "${query}"...`);

            try {
                const data = await api.searchAssets(query, offset, PAGE_SIZE);
                setAssets(prev => (offset === 0 ? data.items : [...prev, ...data.items]));
                setHasMore(data.items.length === PAGE_SIZE);
                setTotal(data.total);
                statusBus.emit(`Showing ${Math.min(offset + PAGE_SIZE, data.total)} of ${data.total} matches`);
            } catch (err) {
                console.error(err);
                statusBus.emit('Search failed. Backend may be offline.');
                setHasMore(false);
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
    }, [query, offset]);

    const handleSearch = (newQuery: string) => {
        if (newQuery !== query) {
            navigate(`/search?q=${encodeURIComponent(newQuery)}`);
        }
    };

    const handleFindSimilar = (assetId: string) => {
        navigate(`/similar/${assetId}?projectId=${selectedProject?.id || ''}`);
    };

    return (
        <div className="flex flex-col h-full overflow-hidden" style={{ WebkitAppRegion: 'no-drag' } as any}>
            {/* Top Header */}
            <div className="flex flex-col gap-4 p-4 border-b border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md z-10 shrink-0">
                <SearchBar initialQuery={query} onSearch={handleSearch} />
                {total > 0 && (
                    <p className="text-sm font-medium text-slate-500 text-center">
                        Search: <span className="text-slate-900 dark:text-white font-semibold">"{query}"</span> · Showing {assets.length} matches
                    </p>
                )}
            </div>

            {/* Grid Container */}
            <div className="flex-1 overflow-x-hidden overflow-y-auto relative bg-gray-50/50 dark:bg-slate-900/50">
                <AssetGrid
                    assets={assets}
                    isLoading={loading && offset === 0}
                    onFindSimilar={handleFindSimilar}
                    onSelect={setSelectedAsset}
                />

                {/* Intersection Observer Target for Infinite Scroll */}
                {hasMore && !loading && (
                    <div ref={lastElementRef} className="h-20 w-full flex items-center justify-center">
                        <div className="animate-pulse w-8 h-8 rounded-full border-t-2 border-indigo-500 animate-spin"></div>
                    </div>
                )}
            </div>

            <AssetDetailPanel
                assetId={selectedAsset}
                onClose={() => setSelectedAsset(null)}
                onFindSimilar={(id) => { setSelectedAsset(null); handleFindSimilar(id); }}
            />
        </div>
    );
};

export default SearchResults;
