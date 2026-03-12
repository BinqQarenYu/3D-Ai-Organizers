import React, { useEffect, useState, Suspense } from 'react';
import { AssetDetail } from '../api/types';
import { api } from '../api/client';
import { statusBus } from './StatusBar';
import { X, ExternalLink, Search, Copy, Box, Image } from 'lucide-react';
import Stage3D from './viewer/Stage3D';

const API_BASE = 'http://127.0.0.1:17831';
const VIEWABLE_3D_EXTS = new Set([
    '.obj', '.glb', '.gltf', '.fbx', '.stl', 
    '.ply', '.dae', '.3mf', '.3dm', 
    '.skp', '.rvt', '.rft', '.max', '.ifc', '.blend'
]);

interface AssetDetailPanelProps {
    assetId: string | null;
    onClose: () => void;
    onFindSimilar: (assetId: string) => void;
}

const AssetDetailPanel: React.FC<AssetDetailPanelProps> = ({ assetId, onClose, onFindSimilar }) => {
    const [asset, setAsset] = useState<AssetDetail | null>(null);
    const [loading, setLoading] = useState(false);
    const [previewMode, setPreviewMode] = useState<'3d' | 'image'>('3d');

    useEffect(() => {
        if (!assetId) {
            setAsset(null);
            return;
        }

        const fetchDetails = async () => {
            setLoading(true);
            setPreviewMode('3d');
            try {
                const data = await api.getAssetDetails(assetId);
                setAsset(data);
            } catch (err) {
                console.error('Failed to get asset details', err);
                statusBus.emit('Error fetching asset details');
            } finally {
                setLoading(false);
            }
        };

        fetchDetails();
    }, [assetId]);

    // ESC to close
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && assetId) onClose();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [assetId, onClose]);

    const handleOpen = async () => {
        if (!asset) return;
        try {
            await api.openOriginal(asset.asset_id);
            statusBus.emit(`Opening ${asset.original_ext} in native app`);
        } catch {
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

    // Build the URL to serve the 3D file from the backend's /uploads/ static mount
    // The stored key is like "originals/<asset_id>.obj" — strip "originals/" prefix
    const ext = asset?.original_ext?.toLowerCase() || '';
    const is3D = VIEWABLE_3D_EXTS.has(ext);

    // The backend mounts /uploads -> assets_root/originals/
    // stored key = "originals/<assetId><ext>", so the filename = <assetId><ext>
    const uploadFilename = asset ? `${asset.asset_id}${ext}` : '';
    const sourceUrl = `${API_BASE}/uploads/${uploadFilename}`;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 z-40 bg-slate-900/30 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Slide-in Panel */}
            <div className="fixed inset-y-0 right-0 z-50 w-full md:w-[420px] bg-white dark:bg-slate-900 shadow-2xl border-l border-gray-200 dark:border-slate-800 flex flex-col transition-transform duration-300 ease-out">

                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-slate-800 shrink-0" style={{ WebkitAppRegion: 'no-drag' } as any}>
                    <div className="flex items-center gap-2 min-w-0">
                        <Box size={16} className="text-indigo-500 shrink-0" />
                        <h2 className="text-base font-semibold truncate text-slate-800 dark:text-gray-100">
                            {asset?.display_name || 'Loading...'}
                        </h2>
                        {ext && (
                            <span className="shrink-0 text-xs font-mono uppercase px-1.5 py-0.5 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-300 rounded">
                                {ext.replace('.', '')}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="ml-2 p-1.5 rounded-md text-gray-400 hover:text-gray-700 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors shrink-0"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto flex flex-col gap-5 p-5" style={{ WebkitAppRegion: 'no-drag' } as any}>
                    {loading ? (
                        <div className="w-full aspect-square bg-slate-100 dark:bg-slate-800 animate-pulse rounded-xl" />
                    ) : asset ? (
                        <>
                            {/* Preview area: 3D viewer or fallback image */}
                            <div className="w-full aspect-square bg-slate-100 dark:bg-slate-800 rounded-xl overflow-hidden relative">
                                {is3D && previewMode === '3d' ? (
                                    <Suspense fallback={
                                        <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm gap-2">
                                            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                                            <span>Loading 3D model...</span>
                                        </div>
                                    }>
                                        <Stage3D sourceUrl={sourceUrl} extension={ext} />
                                    </Suspense>
                                ) : (
                                    <img
                                        src={api.getPreviewUrl(asset.asset_id)}
                                        alt={asset.display_name}
                                        className="w-full h-full object-contain p-4 drop-shadow-md"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).style.display = 'none';
                                        }}
                                    />
                                )}

                                {/* Toggle 3D / Image button */}
                                {is3D && (
                                    <button
                                        onClick={() => setPreviewMode(m => m === '3d' ? 'image' : '3d')}
                                        title={previewMode === '3d' ? 'Switch to image preview' : 'Switch to 3D viewer'}
                                        className="absolute top-2 right-2 p-1.5 rounded-lg bg-slate-900/60 hover:bg-slate-900/80 text-white backdrop-blur-sm transition-colors"
                                    >
                                        {previewMode === '3d' ? <Image size={14} /> : <Box size={14} />}
                                    </button>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={handleOpen}
                                    className="flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors shadow-sm"
                                >
                                    <ExternalLink className="w-4 h-4" />
                                    Open File
                                </button>
                                <button
                                    onClick={() => { onClose(); onFindSimilar(asset.asset_id); }}
                                    className="flex items-center justify-center gap-2 py-2.5 px-4 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 hover:border-indigo-500 text-slate-700 dark:text-slate-200 rounded-lg font-medium transition-colors shadow-sm"
                                >
                                    <Search className="w-4 h-4" />
                                    Find Similar
                                </button>
                            </div>

                            {/* Metadata */}
                            <div className="bg-gray-50 dark:bg-slate-800/50 rounded-lg p-4 border border-gray-100 dark:border-slate-800">
                                <div className="flex justify-between items-center mb-3">
                                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Metadata</h3>
                                    <button onClick={handleCopy} className="text-slate-400 hover:text-indigo-500" title="Copy Metadata">
                                        <Copy className="w-4 h-4" />
                                    </button>
                                </div>

                                <div className="space-y-2.5 text-sm">
                                    <Row label="ID" value={<span className="font-mono text-xs truncate ml-4" title={asset.asset_id}>{asset.asset_id.slice(0, 12)}…</span>} />
                                    <Row label="Format" value={<span className="uppercase font-medium">{ext?.replace('.', '') || 'Unknown'}</span>} />
                                    <Row label="Status" value={<span className="capitalize">{asset.status?.replace('_', ' ')}</span>} />
                                    {asset.category && <Row label="Category" value={asset.category} />}
                                    {asset.vertex_count && <Row label="Vertices" value={asset.vertex_count.toLocaleString()} />}
                                    {asset.material_count && <Row label="Materials" value={asset.material_count.toLocaleString()} />}
                                    {asset.created_at && <Row label="Imported" value={new Date(asset.created_at).toLocaleDateString()} />}
                                </div>

                                {asset.tags && asset.tags.length > 0 && (
                                    <div className="mt-3 flex flex-wrap gap-1.5">
                                        {asset.tags.map(tag => (
                                            <span key={tag} className="px-2 py-1 bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded text-xs text-slate-600 dark:text-slate-300">
                                                {tag}
                                            </span>
                                        ))}
                                    </div>
                                )}
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

const Row: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
    <div className="flex justify-between items-center">
        <span className="text-slate-500 shrink-0">{label}</span>
        <span className="text-slate-700 dark:text-slate-300 text-right">{value}</span>
    </div>
);

export default AssetDetailPanel;
