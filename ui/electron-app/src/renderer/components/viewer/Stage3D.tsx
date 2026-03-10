import React, { Suspense, useMemo } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls, Environment, Center, Html, useGLTF } from '@react-three/drei';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { Group } from 'three';

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

    // Fallback or unsupported
    return null;
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
