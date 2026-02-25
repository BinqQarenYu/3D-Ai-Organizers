import React, { useEffect, useState } from 'react';
import { AssetDetail } from '../api/types';
import { api } from '../api/client';
import { statusBus } from './StatusBar';
import { X, ExternalLink, Search, Copy } from 'lucide-react';

interface AssetDetailPanelProps {
    assetId: string | null;
    onClose: () => void;
    onFindSimilar: (assetId: string) => void;
}

const AssetDetailPanel: React.FC<AssetDetailPanelProps> = ({ assetId, onClose, onFindSimilar }) => {
    const [asset, setAsset] = useState<AssetDetail | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!assetId) {
            setAsset(null);
            return;
        }

        const fetchDetails = async () => {
            setLoading(true);
            try {
                const data = await api.getAssetDetails(assetId);
                setAsset(data);
            } catch (err) {
                console.error('Failed to get asset details', err);
                statusBus.emit('Error fetching asset details');
                // fallback in UI
            } finally {
                setLoading(false);
            }
        };

        fetchDetails();
    }, [assetId]);

    // Handle ESC mapping
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && assetId) {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [assetId, onClose]);

    const handleOpen = async () => {
        if (!asset) return;
        try {
            await api.openOriginal(asset.asset_id);
            statusBus.emit(`Opening ${asset.original_ext} in native app`);
        } catch (err) {
            statusBus.emit('Failed to open original file');
        }
    };

    const handleCopy = () => {
        if (asset) {
            navigator.clipboard.writeText(JSON.stringify(asset, null, 2));
            statusBus.emit('Metadata copied to clipboard');
        }
    };

    if (!assetId) return null;

    return (
        <>
            {/* Backdrop overlay */}
            <div
                className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Slide-in Panel */}
            <div className={`fixed inset-y-0 right-0 z-50 w-full md:w-96 bg-white dark:bg-slate-900 shadow-2xl border-l border-gray-200 dark:border-slate-800 transition-transform duration-300 ease-out flex flex-col`}>
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-800" style={{ WebkitAppRegion: 'no-drag' } as any}>
                    <h2 className="text-lg font-semibold truncate pr-4 text-slate-800 dark:text-gray-100">
                        {asset?.display_name || 'Loading...'}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors shrink-0"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6" style={{ WebkitAppRegion: 'no-drag' } as any}>
                    {loading ? (
                        <div className="w-full aspect-square bg-slate-100 dark:bg-slate-800 animate-pulse rounded-xl" />
                    ) : asset ? (
                        <>
                            {/* Preview Image */}
                            <div className="w-full aspect-square bg-slate-100 dark:bg-slate-800 rounded-xl overflow-hidden flex items-center justify-center p-4">
                                <img
                                    src={api.getPreviewUrl(asset.asset_id)}
                                    alt={asset.display_name}
                                    className="max-w-full max-h-full object-contain drop-shadow-md"
                                />
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={handleOpen}
                                    className="flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors shadow-sm"
                                >
                                    <ExternalLink className="w-4 h-4" />
                                    Open Original
                                </button>
                                <button
                                    onClick={() => { onClose(); onFindSimilar(asset.asset_id); }}
                                    className="flex items-center justify-center gap-2 py-2.5 px-4 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 hover:border-indigo-500 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition-colors shadow-sm"
                                >
                                    <Search className="w-4 h-4" />
                                    Find Similar
                                </button>
                            </div>

                            {/* Metadata Details */}
                            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4 border border-gray-100 dark:border-slate-800">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Metadata</h3>
                                    <button onClick={handleCopy} className="text-slate-400 hover:text-indigo-500" title="Copy Metadata">
                                        <Copy className="w-4 h-4" />
                                    </button>
                                </div>

                                <div className="space-y-3 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">ID</span>
                                        <span className="font-mono text-slate-700 dark:text-slate-300 truncate ml-4" title={asset.asset_id}>{asset.asset_id}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Extension</span>
                                        <span className="text-slate-700 dark:text-slate-300 uppercase font-medium">{asset.original_ext?.replace('.', '') || 'UNKNOWN'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Status</span>
                                        <span className="text-slate-700 dark:text-slate-300 capitalize">{asset.status.replace('_', ' ')}</span>
                                    </div>
                                    {asset.category && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-500">Category</span>
                                            <span className="text-slate-700 dark:text-slate-300">{asset.category}</span>
                                        </div>
                                    )}
                                    {asset.tags && asset.tags.length > 0 && (
                                        <div className="flex flex-col gap-1 mt-2">
                                            <span className="text-slate-500 text-xs">Tags</span>
                                            <div className="flex flex-wrap gap-1.5">
                                                {asset.tags.map(tag => (
                                                    <span key={tag} className="px-2 py-1 bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded text-xs text-slate-600 dark:text-slate-300">
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="text-center text-slate-500 mt-10">Asset not found.</div>
                    )}
                </div>
            </div>
        </>
    );
};

export default AssetDetailPanel;
