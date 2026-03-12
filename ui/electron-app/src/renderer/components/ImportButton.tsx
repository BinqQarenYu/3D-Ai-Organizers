import React, { useState, useRef } from 'react';
import { Upload, FolderOpen, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../api/client';

interface ImportButtonProps {
    projectId: string;
    onImported?: (assetId: string) => void;
}

type Status = 'idle' | 'picking' | 'uploading' | 'success' | 'error';

const ImportButton: React.FC<ImportButtonProps> = ({ projectId, onImported }) => {
    const [status, setStatus] = useState<Status>('idle');
    const [errorMsg, setErrorMsg] = useState('');
    const [newAssetId, setNewAssetId] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const ACCEPTED = '.obj,.glb,.gltf,.fbx,.blend';

    // Try Electron native dialog first, fallback to browser file input
    const handleImport = async () => {
        if (!projectId) {
            setErrorMsg('Please select a project first.');
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
            return;
        }

        const electronAPI = (window as any).electronAPI;
        if (electronAPI?.selectFile) {
            // Electron: open native OS file picker
            setStatus('picking');
            try {
                const filePath: string | null = await electronAPI.selectFile({
                    title: 'Import 3D Asset',
                    filters: [
                        { name: '3D Assets', extensions: ['obj', 'glb', 'gltf', 'fbx', 'blend'] },
                        { name: 'OBJ Files', extensions: ['obj'] },
                        { name: 'GLTF / GLB', extensions: ['gltf', 'glb'] },
                    ],
                    properties: ['openFile'],
                });

                if (!filePath) {
                    setStatus('idle');
                    return;
                }

                setStatus('uploading');
                // Use the local file import route on the backend instead of passing huge files over IPC
                const result = await api.importLocalFile(filePath, projectId);

                setNewAssetId(result.asset_id);
                setStatus('success');
                onImported?.(result.asset_id);
                setTimeout(() => setStatus('idle'), 3000);
            } catch (e: any) {
                setErrorMsg(e?.message || 'Import failed.');
                setStatus('error');
                setTimeout(() => setStatus('idle'), 4000);
            }
        } else {
            // Browser fallback: use hidden <input type="file">
            fileInputRef.current?.click();
        }
    };

    const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        e.target.value = '';

        if (!projectId) {
            setErrorMsg('Please select a project first.');
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
            return;
        }

        setStatus('uploading');
        try {
            const result = await api.uploadFile(file, projectId);
            setNewAssetId(result.asset_id);
            setStatus('success');
            onImported?.(result.asset_id);
            setTimeout(() => setStatus('idle'), 3000);
        } catch (e: any) {
            setErrorMsg(e?.message || 'Upload failed.');
            setStatus('error');
            setTimeout(() => setStatus('idle'), 4000);
        }
    };

    const getButtonContent = () => {
        switch (status) {
            case 'picking':
                return (
                    <>
                        <FolderOpen size={15} className="flex-shrink-0" />
                        <span>Selecting...</span>
                    </>
                );
            case 'uploading':
                return (
                    <>
                        <Loader2 size={15} className="flex-shrink-0 animate-spin" />
                        <span>Importing...</span>
                    </>
                );
            case 'success':
                return (
                    <>
                        <CheckCircle size={15} className="flex-shrink-0 text-green-400" />
                        <span className="text-green-400">Imported!</span>
                    </>
                );
            case 'error':
                return (
                    <>
                        <XCircle size={15} className="flex-shrink-0 text-red-400" />
                        <span className="text-red-400 truncate max-w-[160px]" title={errorMsg}>{errorMsg}</span>
                    </>
                );
            default:
                return (
                    <>
                        <Upload size={15} className="flex-shrink-0" />
                        <span>Import 3D File</span>
                    </>
                );
        }
    };

    const isDisabled = status === 'uploading' || status === 'picking';

    return (
        <>
            <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED}
                className="hidden"
                onChange={handleFileInputChange}
            />
            <button
                id="import-3d-button"
                onClick={handleImport}
                disabled={isDisabled}
                className={`
                    inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
                    transition-all duration-200 select-none
                    ${isDisabled
                        ? 'opacity-60 cursor-not-allowed bg-indigo-700 text-white'
                        : 'bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white shadow-md hover:shadow-indigo-500/30'
                    }
                    ${status === 'success' ? 'bg-green-700 hover:bg-green-700' : ''}
                    ${status === 'error' ? 'bg-red-900/50 hover:bg-red-900/50' : ''}
                `}
                title={status === 'error' ? errorMsg : 'Import an OBJ, GLB, GLTF or FBX file from your computer'}
            >
                {getButtonContent()}
            </button>
        </>
    );
};

export default ImportButton;
