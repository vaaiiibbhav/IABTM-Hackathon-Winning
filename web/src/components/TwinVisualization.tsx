"use client";

import React, { useRef, Suspense } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

interface TwinVisualizationProps {
  alignmentValue: number; // between 0 and 1
}

// 1. Procedural mannequin fallback component - loads instantly without Suspend
function ProceduralMannequins({ alignmentValue }: { alignmentValue: number }) {
  const distance = (1 - alignmentValue) * 3.0;
  return (
    <group>
      {/* Current Self Mannequin */}
      <group position={[-distance / 2, -0.5, 0]} scale={[0.3, 0.3, 0.3]}>
        {/* Head */}
        <mesh position={[0, 0.9, 0]}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshPhongMaterial color="#3b82f6" emissive="#1d4ed8" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
        {/* Torso */}
        <mesh position={[0, 0.45, 0]}>
          <cylinderGeometry args={[0.16, 0.1, 0.6, 6]} />
          <meshPhongMaterial color="#3b82f6" emissive="#1d4ed8" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
        {/* Shoulders */}
        <mesh position={[0, 0.7, 0]}>
          <boxGeometry args={[0.36, 0.06, 0.1]} />
          <meshPhongMaterial color="#3b82f6" emissive="#1d4ed8" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
      </group>

      {/* Target Self Mannequin */}
      <group position={[distance / 2, -0.5, 0]} scale={[0.3, 0.3, 0.3]}>
        {/* Head */}
        <mesh position={[0, 0.9, 0]}>
          <sphereGeometry args={[0.18, 16, 16]} />
          <meshPhongMaterial color="#f59e0b" emissive="#b45309" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
        {/* Torso */}
        <mesh position={[0, 0.45, 0]}>
          <cylinderGeometry args={[0.16, 0.1, 0.6, 6]} />
          <meshPhongMaterial color="#f59e0b" emissive="#b45309" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
        {/* Shoulders */}
        <mesh position={[0, 0.7, 0]}>
          <boxGeometry args={[0.36, 0.06, 0.1]} />
          <meshPhongMaterial color="#f59e0b" emissive="#b45309" emissiveIntensity={0.5} wireframe transparent opacity={0.7} />
        </mesh>
      </group>
    </group>
  );
}

// 2. GLTF model loader
function Bust({ color, emissive, ...props }: { color: string; emissive: string; [key: string]: unknown }) {
  const { scene } = useGLTF("/assets/models/bust.glb");
  const clonedScene = React.useMemo(() => scene.clone(), [scene]);

  React.useEffect(() => {
    clonedScene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.material = new THREE.MeshPhongMaterial({
          color: new THREE.Color(color),
          emissive: new THREE.Color(emissive),
          emissiveIntensity: 0.6,
          wireframe: true,
          transparent: true,
          opacity: 0.7,
        });
      }
    });
  }, [clonedScene, color, emissive]);

  return <primitive object={clonedScene} {...props} />;
}

// 3. Animation and positioning system for the busts
function AnimatedBusts({ alignmentValue }: { alignmentValue: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const currentRef = useRef<THREE.Group>(null);
  const targetRef = useRef<THREE.Group>(null);

  // Distance is driven by alignment field: higher alignment = closer together
  const distance = (1 - alignmentValue) * 3.0;

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    
    // Slow overall rotation
    if (groupRef.current) {
      groupRef.current.rotation.y = t * 0.15;
    }

    // Breathing motion: scale Y slightly
    const currentScaleY = 1.0 + Math.sin(t * 1.5) * 0.03;
    const targetScaleY = 1.0 + Math.sin(t * 1.2 + 1) * 0.03;

    if (currentRef.current) {
      currentRef.current.scale.set(0.3, 0.3 * currentScaleY, 0.3);
    }
    if (targetRef.current) {
      targetRef.current.scale.set(0.3, 0.3 * targetScaleY, 0.3);
    }
    
    // Pulse effect when overlapping/merged (alignment is high, distance is low)
    if (alignmentValue > 0.9 && currentRef.current && targetRef.current) {
      const pulse = 0.3 + Math.sin(t * 4) * 0.01;
      currentRef.current.scale.setScalar(pulse);
      targetRef.current.scale.setScalar(pulse);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Current Self Bust: Cyan/Blue */}
      <group ref={currentRef} position={[-distance / 2, -0.5, 0]}>
        <Bust color="#3b82f6" emissive="#1d4ed8" />
      </group>

      {/* Target Self Bust: Gold/Orange */}
      <group ref={targetRef} position={[distance / 2, -0.5, 0]}>
        <Bust color="#f59e0b" emissive="#b45309" />
      </group>

      {/* Connection line if not perfectly overlapping */}
      {distance > 0.1 && (
        <line>
          <bufferGeometry attach="geometry" onUpdate={(self) => {
            const points = [
              new THREE.Vector3(-distance / 2, 0, 0),
              new THREE.Vector3(distance / 2, 0, 0)
            ];
            self.setFromPoints(points);
          }} />
          <lineBasicMaterial attach="material" color="#818cf8" transparent opacity={0.4} />
        </line>
      )}
    </group>
  );
}

export default function TwinVisualization({ alignmentValue }: TwinVisualizationProps) {
  return (
    <div className="w-full h-full min-h-[300px] relative">
      <Canvas camera={{ position: [0, 0, 5], fov: 45 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[5, 5, 5]} intensity={1.5} color="#6366f1" />
        <pointLight position={[-5, 5, -5]} intensity={1.5} color="#f59e0b" />
        
        {/* Render procedural low-poly mannequins instantly, swapping to detailed GLTF busts when loaded */}
        <Suspense fallback={<ProceduralMannequins alignmentValue={alignmentValue} />}>
          <AnimatedBusts alignmentValue={alignmentValue} />
        </Suspense>
        
        <gridHelper args={[10, 10, 0x3f3f46, 0x18181b]} position={[0, -1.2, 0]} />
        <OrbitControls enableZoom={true} enablePan={false} maxPolarAngle={Math.PI / 2} />
      </Canvas>

      {/* Visual Overlay Legend */}
      <div className="absolute bottom-2 left-4 flex gap-4 text-[9px] font-mono text-zinc-500 bg-zinc-950/80 p-2 rounded border border-zinc-900 z-10">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-1.5 rounded bg-blue-500 block"></span>
          <span>Current Self</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-1.5 rounded bg-amber-500 block"></span>
          <span>Target Self (Aspirations)</span>
        </div>
        <div className="flex items-center gap-1.5 text-zinc-400">
          <span>Alignment: {Math.round(alignmentValue * 100)}%</span>
        </div>
      </div>
    </div>
  );
}

// Preload model assets
useGLTF.preload("/assets/models/bust.glb");
