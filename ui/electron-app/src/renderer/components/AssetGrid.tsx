import React from 'react';
import { AssetListItem } from '../api/types';
import AssetCard from './AssetCard';

interface AssetGridProps {
    assets: AssetListItem[];
    onFindSimilar: (assetId: string) => void;
    onSelect: (assetId: string) => void;
    isLoading?: boolean;
}

const AssetGrid: React.FC<AssetGridProps> = ({ assets, onFindSimilar, onSelect, isLoading }) => {
    if (isLoading && assets.length === 0) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 p-6">
                {[...Array(10)].map((_, i) => (
                    <div key={i} className="h-64 rounded-xl bg-gray-200 dark:bg-slate-800 animate-pulse"></div>
                ))}
            </div>
        );
    }

    if (!isLoading && assets.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
                <p>No assets found.</p>
            </div>
        );
    }

    // Simplified grid. For 100K items, this would use react-window / FixedSizeGrid
    // However, since we page 50-100 at a time, a standard DOM grid is usually fine.
    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6 p-6 overflow-y-auto w-full">
            {assets.map((asset) => (
                <AssetCard
                    key={asset.asset_id}
                    asset={asset}
                    onFindSimilar={onFindSimilar}
                    onClick={onSelect}
                />
            ))}
        </div>
    );
};

export default AssetGrid;
