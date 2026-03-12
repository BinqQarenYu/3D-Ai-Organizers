import React, { useState } from 'react';
import { AssetListItem } from '../api/types';
import { api } from '../api/client';
import { ExternalLink, Image as ImageIcon, Search } from 'lucide-react';
import Stage3D from './viewer/Stage3D';

interface AssetCardProps {
    asset: AssetListItem;
    onFindSimilar: (assetId: string) => void;
    onClick: (assetId: string) => void;
}

const is3DModel = (ext?: string) => {
    if (!ext) return false;
    const lowerExt = ext.toLowerCase();
    return lowerExt === '.glb' || lowerExt === '.gltf' || lowerExt === '.obj';
};

const API_BASE = 'http://127.0.0.1:17831';

const AssetCard: React.FC<AssetCardProps> = ({ asset, onFindSimilar, onClick }) => {
    const [imgError, setImgError] = useState(false);
    const has3D = is3DModel(asset.original_ext);
    // 3D files are served from the /uploads/ static mount (not the preview endpoint)
    const previewUrl = has3D
        ? `${API_BASE}/uploads/${asset.asset_id}${asset.original_ext}`
        : api.getPreviewUrl(asset.asset_id);

    const handleOpen = async (e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await api.openOriginal(asset.asset_id);
        } catch (err) {
            console.error('Failed to open:', err);
        }
    };

    const handleSimilar = (e: React.MouseEvent) => {
        e.stopPropagation();
        onFindSimilar(asset.asset_id);
    };

    return (
        <div
            onClick={() => onClick(asset.asset_id)}
            className="group flex flex-col pt-0 pb-3 bg-white dark:bg-slate-800 rounded-xl overflow-hidden cursor-pointer border border-gray-200 dark:border-slate-700/50 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 ease-out h-64 relative"
        >
            {/* Image/3D Area */}
            <div className="flex-1 w-full bg-slate-100 dark:bg-slate-900 overflow-hidden flex items-center justify-center relative">
                {has3D ? (
                    <Stage3D sourceUrl={previewUrl} extension={asset.original_ext!} />
                ) : !imgError ? (
                    <img
                        src={previewUrl}
                        alt={asset.display_name}
                        onError={() => setImgError(true)}
                        className="w-full h-full object-contain object-bottom pt-2 pointer-events-none"
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center text-slate-400">
                        <ImageIcon className="h-8 w-8 mb-2 opacity-50" />
                        <span className="text-xs">No preview</span>
                    </div>
                )}

                {/* Hover Actions Overlay */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-3 backdrop-blur-[2px] pointer-events-none">
                    <button
                        onClick={handleOpen}
                        className="p-2 bg-white/10 hover:bg-white text-white hover:text-slate-900 rounded-full backdrop-blur-md transition-colors pointer-events-auto"
                        title="Open Original"
                    >
                        <ExternalLink className="h-5 w-5" />
                    </button>
                    <button
                        onClick={handleSimilar}
                        className="p-2 bg-white/10 hover:bg-white text-white hover:text-slate-900 rounded-full backdrop-blur-md transition-colors pointer-events-auto"
                        title="Find Similar"
                    >
                        <Search className="h-5 w-5" />
                    </button>
                </div>
            </div>

            {/* Metadata Base */}
            <div className="px-4 mt-3 shrink-0 flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate" title={asset.display_name}>
                        {asset.display_name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                        {asset.original_ext && (
                            <span className="text-[10px] font-bold uppercase text-slate-500 bg-slate-100 dark:bg-slate-700/50 px-1.5 py-0.5 rounded">
                                {asset.original_ext.replace('.', '')}
                            </span>
                        )}
                        {asset.status !== 'indexed' && (
                            <span className="text-[10px] text-amber-600 bg-amber-50 dark:bg-amber-900/30 px-1.5 py-0.5 rounded">
                                {asset.status.replace('_', ' ')}
                            </span>
                        )}
                        {/* Find Similar Score badge (if passed for similar results) */}
                        {(asset as any).similarity_score !== undefined && (
                            <span className="text-[10px] text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 px-1.5 py-0.5 rounded">
                                Sim: {Math.round((asset as any).similarity_score * 100)}%
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AssetCard;
