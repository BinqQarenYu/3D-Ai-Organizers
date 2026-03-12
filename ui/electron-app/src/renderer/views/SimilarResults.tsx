import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useProject } from '../contexts/ProjectContext';
import { ArrowLeft } from 'lucide-react';
import AssetGrid from '../components/AssetGrid';
import AssetDetailPanel from '../components/AssetDetailPanel';
import { api } from '../api/client';
import { SimilarResultItem, AssetDetail } from '../api/types';
import { statusBus } from '../components/StatusBar';

const SimilarResults: React.FC = () => {
    const { assetId } = useParams<{ assetId: string }>();
    const [searchParams] = useSearchParams();
    const projectId = searchParams.get('projectId');
    const { selectedProject } = useProject();
    const navigate = useNavigate();

    const [sourceAsset, setSourceAsset] = useState<AssetDetail | null>(null);
    const [similarAssets, setSimilarAssets] = useState<SimilarResultItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedAsset, setSelectedAsset] = useState<string | null>(null);

    useEffect(() => {
        const fetchSimilar = async () => {
            if (!assetId) return;

            setLoading(true);
            setSourceAsset(null);
            setSimilarAssets([]);
            statusBus.emit('Finding visually similar assets...');

            try {
                // Fetch source asset details
                const source = await api.getAssetDetails(assetId);
                setSourceAsset(source);

                // Fetch similar items
                const results = await api.findSimilar(assetId, 30, 0.7);
                setSimilarAssets(results);
                statusBus.emit(`Found ${results.length} visually similar assets`);
            } catch (err) {
                console.error(err);
                statusBus.emit('Failed to find similar assets.');
            } finally {
                setLoading(false);
            }
        };

        fetchSimilar();
    }, [assetId]);

    return (
        <div className="flex flex-col h-full overflow-hidden bg-gray-50 dark:bg-slate-900" style={{ WebkitAppRegion: 'no-drag' } as any}>
            {/* Top Header */}
            <div className="flex flex-col md:flex-row gap-6 p-6 border-b border-gray-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md shrink-0">
                <button
                    onClick={() => navigate(-1)}
                    className="self-start p-2 rounded-full hover:bg-gray-200 dark:hover:bg-slate-800 transition-colors text-slate-500"
                    title="Go Back"
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>

                <div className="flex items-center gap-6">
                    <div className="w-24 h-24 bg-white dark:bg-slate-800 rounded-lg overflow-hidden border border-gray-200 dark:border-slate-700 shrink-0 shadow-sm flex items-center justify-center p-2">
                        {sourceAsset ? (
                            <img
                                src={api.getPreviewUrl(sourceAsset.asset_id)}
                                alt={sourceAsset.display_name}
                                className="max-w-full max-h-full object-contain"
                            />
                        ) : (
                            <div className="w-full h-full bg-slate-100 dark:bg-slate-800 animate-pulse" />
                        )}
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600 mb-1">
                            Visually Similar
                        </h1>
                        <p className="text-slate-600 dark:text-slate-400 font-medium">
                            Showing assets similar to <span className="text-slate-900 dark:text-white font-semibold">"{sourceAsset?.display_name || 'Loading...'}"</span>
                        </p>
                    </div>
                </div>
            </div>

            {/* Grid Container */}
            <div className="flex-1 overflow-x-hidden overflow-y-auto relative">
                <AssetGrid
                    assets={similarAssets}
                    isLoading={loading}
                    onFindSimilar={(id) => navigate(`/similar/${id}`)}
                    onSelect={setSelectedAsset}
                />
            </div>

            <AssetDetailPanel
                assetId={selectedAsset}
                onClose={() => setSelectedAsset(null)}
                onFindSimilar={(id) => { setSelectedAsset(null); navigate(`/similar/${id}`); }}
            />
        </div>
    );
};

export default SimilarResults;
