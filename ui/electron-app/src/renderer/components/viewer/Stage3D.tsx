import React, { Suspense, useMemo, useEffect } from 'react';
import { Box, AlertTriangle, Loader2 } from 'lucide-react';
import { Canvas, useLoader } from '@react-three/fiber';
import { 
    OrbitControls, 
    Environment, 
    Center, 
    Html, 
    useGLTF, 
    ContactShadows, 
    Float,
    PerspectiveCamera
} from '@react-three/drei';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js';
import { ColladaLoader } from 'three/examples/jsm/loaders/ColladaLoader.js';
import { Group, Mesh, MeshStandardMaterial, DoubleSide } from 'three';

interface Stage3DProps {
    sourceUrl: string;
    extension: string;
}

const ModelLoader: React.FC<{ url: string, ext: string }> = ({ url, ext }) => {
    const extension = ext.toLowerCase();

    try {
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
            // FBXLoader in R3F handles fflate automatically if installed
            const fbx = useLoader(FBXLoader, url) as Group;
            return <primitive object={fbx} />;
        }

        // For STL
        if (extension === '.stl') {
            const geometry = useLoader(STLLoader, url);
            const material = useMemo(() => new MeshStandardMaterial({ color: 0x999999, metalness: 0.1, roughness: 0.5 }), []);
            return <mesh geometry={geometry} material={material} />;
        }

        // For PLY
        if (extension === '.ply') {
            const geometry = useLoader(PLYLoader, url);
            const material = useMemo(() => new MeshStandardMaterial({ color: 0x999999, metalness: 0.1, roughness: 0.5 }), []);
            return <mesh geometry={geometry} material={material} />;
        }

        // For Collada (DAE)
        if (extension === '.dae') {
            const { scene } = useLoader(ColladaLoader, url);
            return <primitive object={scene} />;
        }
    } catch (err) {
        console.error(`Error loading ${extension} model:`, err);
        return (
            <Html center>
                <div className="flex flex-col items-center justify-center p-4 bg-red-900/80 backdrop-blur-md rounded-xl text-white shadow-xl border border-red-500/30 text-center min-w-[200px]">
                    <AlertTriangle size={24} className="text-red-400 mb-2" />
                    <span className="text-xs font-bold">Failed to render {extension.toUpperCase()}</span>
                    <p className="text-[10px] text-red-200 mt-1">Try opening in native app</p>
                </div>
            </Html>
        );
    }

    // Fallback message for proprietary formats (Skp, Max, Rvt)
    return (
        <Html center>
            <div className="flex flex-col items-center justify-center p-6 bg-slate-900/90 backdrop-blur-lg rounded-2xl text-white shadow-2xl border border-white/10 max-w-[280px] text-center">
                <div className="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center mb-4">
                    <Box size={24} className="text-indigo-400" />
                </div>
                <h3 className="text-sm font-bold mb-1 italic">Proprietary Format</h3>
                <p className="text-[10px] text-slate-400 leading-relaxed">
                    Format {extension.toUpperCase()} is indexed but cannot be viewed directly in-browser. <br/>
                    <span className="text-indigo-400 font-semibold mt-2 block italic">Click "Open File" for Native App</span>
                </p>
            </div>
        </Html>
    );
};

const LoadingOverlay: React.FC = () => {
    return (
        <Html center>
            <div className="flex flex-col items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md rounded-2xl text-white shadow-2xl border border-white/5">
                <Loader2 size={24} className="text-indigo-400 animate-spin mb-3" />
                <span className="text-[10px] font-bold tracking-widest uppercase opacity-80">Loading 3D Data</span>
            </div>
        </Html>
    );
};

const Stage3D: React.FC<Stage3DProps> = ({ sourceUrl, extension }) => {
    return (
        <div className="w-full h-full relative cursor-move">
            <Canvas shadows className="bg-slate-50 dark:bg-slate-950">
                <PerspectiveCamera makeDefault position={[4, 4, 4]} fov={40} />
                <Suspense fallback={<LoadingOverlay />}>
                    <Environment preset="city" />
                    <ambientLight intensity={0.7} />
                    <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
                    
                    <Center>
                        <Float speed={1.5} rotationIntensity={0.5} floatIntensity={0.5}>
                            <ModelLoader url={sourceUrl} ext={extension} />
                        </Float>
                    </Center>

                    <ContactShadows 
                        position={[0, -1.5, 0]} 
                        opacity={0.4} 
                        scale={10} 
                        blur={2.5} 
                        far={4} 
                        color="#000000" 
                    />
                </Suspense>
                <OrbitControls 
                    makeDefault 
                    enableDamping 
                    dampingFactor={0.05} 
                    minDistance={2} 
                    maxDistance={20} 
                />
            </Canvas>
        </div>
    );
};

export default Stage3D;
