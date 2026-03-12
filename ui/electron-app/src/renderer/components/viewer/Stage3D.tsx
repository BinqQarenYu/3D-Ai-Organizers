import React, { Suspense, useMemo } from 'react';
import { Box } from 'lucide-react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls, Environment, Center, Html, useGLTF } from '@react-three/drei';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { Group, Mesh, MeshStandardMaterial } from 'three';

interface Stage3DProps {
    sourceUrl: string;
    extension: string;
}

const ModelLoader: React.FC<{ url: string, ext: string }> = ({ url, ext }) => {
    const extension = ext.toLowerCase();

    // For GLTF/GLB
    if (extension === '.glb' || extension === '.gltf') {
        const { scene } = useGLTF(url);
        return <primitive object={scene} />;
    }

    // For OBJ
    if (extension === '.obj') {
        const obj = useLoader(OBJLoader, url) as Group;
        return <primitive object={obj} />;
    }

    // For FBX
    if (extension === '.fbx') {
        const fbx = useLoader(FBXLoader, url) as Group;
        return <primitive object={fbx} />;
    }

    // For STL
    if (extension === '.stl') {
        const geometry = useLoader(STLLoader, url);
        const material = useMemo(() => new MeshStandardMaterial({ color: 0x888888, metalness: 0.1, roughness: 0.5 }), []);
        return <mesh geometry={geometry} material={material} />;
    }

    // Fallback message for proprietary formats
    return (
        <Html center>
            <div className="flex flex-col items-center justify-center p-6 bg-slate-900/90 backdrop-blur-lg rounded-2xl text-white shadow-2xl border border-white/10 max-w-[280px] text-center">
                <div className="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center mb-4">
                    <Box size={24} className="text-indigo-400" />
                </div>
                <h3 className="text-sm font-bold mb-1 italic">Proprietary Format</h3>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                    Format {extension.toUpperCase()} is indexed but cannot be viewed directly in-browser. <br/>
                    <span className="text-indigo-400 font-semibold mt-2 block">Use "Open File" to view in native app.</span>
                </p>
            </div>
        </Html>
    );
};

const LoadingOverlay: React.FC = () => {
    return (
        <Html center>
            <div className="flex flex-col items-center justify-center p-3 bg-slate-900/80 backdrop-blur-md rounded-xl text-white shadow-xl">
                <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2"></div>
                <span className="text-xs font-semibold tracking-wide whitespace-nowrap text-slate-200">Loading Model...</span>
            </div>
        </Html>
    );
};

const Stage3D: React.FC<Stage3DProps> = ({ sourceUrl, extension }) => {
    return (
        <Canvas camera={{ position: [0, 0, 5], fov: 50 }} className="w-full h-full bg-slate-100 dark:bg-slate-900" style={{ pointerEvents: 'auto' }}>
            <Suspense fallback={<LoadingOverlay />}>
                <Environment preset="city" />
                <Center>
                    <ModelLoader url={sourceUrl} ext={extension} />
                </Center>
            </Suspense>
            <OrbitControls makeDefault autoRotate autoRotateSpeed={2} enableDamping dampingFactor={0.05} />
        </Canvas>
    );
};

export default Stage3D;
