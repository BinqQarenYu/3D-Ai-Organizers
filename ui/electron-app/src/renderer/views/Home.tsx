import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { AssetListItem } from '../api/types';
import { api } from '../api/client';
import AssetCard from '../components/AssetCard';
import AssetDetailPanel from '../components/AssetDetailPanel';
import { statusBus } from '../components/StatusBar';
import { useProject } from '../contexts/ProjectContext';
import ImportButton from '../components/ImportButton';


const Home: React.FC = () => {
    const navigate = useNavigate();
    const [recentAssets, setRecentAssets] = useState<AssetListItem[]>([]);
    const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
    const { selectedProject } = useProject();


    const loadRecent = useCallback(async () => {
        if (!selectedProject?.id) {
            setRecentAssets([]);
            return;
        }
        try {
            const assets = await api.getRecentAssets(selectedProject?.id);
            setRecentAssets(assets);
        } catch (e) {
            console.error(e);
            statusBus.emit('Failed to connect to backend for recent assets.');
        }
    }, [selectedProject]);

    useEffect(() => {
        loadRecent();
    }, [loadRecent]);

    const handleImported = (_assetId: string) => {
        // Refresh asset list when a new file is imported
        loadRecent();
        statusBus.emit('Asset imported successfully!');
    };

    const handleSearch = (query: string) => {
        navigate(`/search?q=${encodeURIComponent(query)}`);
    };

    const handleFindSimilar = (assetId: string) => {
        navigate(`/similar/${assetId}?projectId=${selectedProject?.id || ''}`);
    };

    return (
        <div className="h-full overflow-y-auto flex flex-col p-8 transition-colors duration-200" style={{ WebkitAppRegion: 'no-drag' } as any}>

            {/* Search Header */}
            <div className="mt-8 mb-16 max-w-4xl mx-auto w-full text-center">
                <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600 mb-6 drop-shadow-sm tracking-tight">
                    What are you looking for?
                </h1>
                <SearchBar onSearch={handleSearch} autoFocus />
                {/* Import Button */}
                <div className="mt-4 flex justify-center">
                    <ImportButton
                        projectId={selectedProject?.id || ''}
                        onImported={handleImported}
                    />
                </div>
            </div>

            {/* Recommended/Recent Area */}
            {recentAssets.length > 0 && (
                <div className="max-w-7xl mx-auto w-full">
                    <h2 className="text-lg font-medium text-slate-600 dark:text-slate-400 mb-4 px-2 tracking-wide">
                        Recently Added
                    </h2>
                    <div className="flex gap-4 overflow-x-auto pb-6 px-2 snap-x hide-scrollbars">
                        {recentAssets.map(asset => (
                            <div key={asset.asset_id} className="w-64 shrink-0 snap-start">
                                <AssetCard
                                    asset={asset}
                                    onFindSimilar={handleFindSimilar}
                                    onClick={() => setSelectedAsset(asset.asset_id)}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Global Slide-in Panel */}
            <AssetDetailPanel
                assetId={selectedAsset}
                onClose={() => setSelectedAsset(null)}
                onFindSimilar={(id) => { setSelectedAsset(null); handleFindSimilar(id); }}
            />
        </div>
    );
};

export default Home;
