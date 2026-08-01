"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import type { Theme } from "../lib/types";

interface ThreeVectorSpaceProps {
  themes: Theme[];
  driftScore: number;
}

export default function ThreeVectorSpace({ themes, driftScore }: ThreeVectorSpaceProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 300;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 2, 8); // Straight focus on the human figures

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x6366f1, 2.5, 30);
    pointLight1.position.set(5, 5, 5);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xf59e0b, 2.5, 30);
    pointLight2.position.set(-5, 5, -5);
    scene.add(pointLight2);

    // 3. Grid Floor
    const gridHelper = new THREE.GridHelper(10, 10, 0x3f3f46, 0x18181b);
    gridHelper.position.y = -1.2;
    scene.add(gridHelper);

    const vectorGroup = new THREE.Group();
    scene.add(vectorGroup);

    // ---- Helper to create a stylized procedural 3D mannequin human figure ----
    const createProceduralHuman = (color: number, emissiveColor: number) => {
      const humanGroup = new THREE.Group();

      // Semi-transparent wireframe material for futuristic overlay blending
      const material = new THREE.MeshPhongMaterial({
        color: color,
        emissive: emissiveColor,
        emissiveIntensity: 0.5,
        wireframe: true,
        transparent: true,
        opacity: 0.7,
        shininess: 30,
      });

      // 1. Head
      const headGeo = new THREE.SphereGeometry(0.18, 16, 16);
      const head = new THREE.Mesh(headGeo, material);
      head.position.y = 0.9;
      humanGroup.add(head);

      // 2. Torso (low-poly chest and hips)
      const torsoGeo = new THREE.CylinderGeometry(0.16, 0.1, 0.6, 6);
      const torso = new THREE.Mesh(torsoGeo, material);
      torso.position.y = 0.45;
      humanGroup.add(torso);

      // 3. Shoulders / Neck Joiner
      const shoulderGeo = new THREE.BoxGeometry(0.36, 0.06, 0.1);
      const shoulder = new THREE.Mesh(shoulderGeo, material);
      shoulder.position.y = 0.7;
      humanGroup.add(shoulder);

      // 4. Arms
      const armGeo = new THREE.CylinderGeometry(0.04, 0.03, 0.45, 6);
      
      const leftArm = new THREE.Mesh(armGeo, material);
      leftArm.position.set(-0.24, 0.45, 0);
      leftArm.rotation.z = Math.PI / 12;
      humanGroup.add(leftArm);

      const rightArm = new THREE.Mesh(armGeo, material);
      rightArm.position.set(0.24, 0.45, 0);
      rightArm.rotation.z = -Math.PI / 12;
      humanGroup.add(rightArm);

      // 5. Legs
      const legGeo = new THREE.CylinderGeometry(0.05, 0.04, 0.55, 6);

      const leftLeg = new THREE.Mesh(legGeo, material);
      leftLeg.position.set(-0.1, 0.05, 0);
      humanGroup.add(leftLeg);

      const rightLeg = new THREE.Mesh(legGeo, material);
      rightLeg.position.set(0.1, 0.05, 0);
      humanGroup.add(rightLeg);

      // Center pivot point
      humanGroup.position.y = -0.3;
      return humanGroup;
    };

    // 4. Instantiate CURRENT and TARGET human models
    // Current self: Cyan / Blue theme
    const currentHuman = createProceduralHuman(0x3b82f6, 0x1d4ed8);
    currentHuman.position.set(0, 0, 0);
    vectorGroup.add(currentHuman);

    // Target self (aspirations): Gold / Emerald theme
    const targetHuman = createProceduralHuman(0xf59e0b, 0xb45309);
    
    // Position target self relative to drift.
    // If driftScore is very low (aligned), targetHuman positions exactly at (0, 0, 0) overlapping currentHuman!
    // If drift is high, it moves away.
    const targetX = driftScore * 2.5; 
    const targetY = 0; // Stand on same level
    const targetZ = -driftScore * 1.5; // Offset backward slightly for 3D depth

    targetHuman.position.set(targetX, targetY, targetZ);
    vectorGroup.add(targetHuman);

    // 5. Connect them with a soft laser grid beam if they are separated
    let deltaLine: THREE.Line | null = null;
    if (driftScore > 0.05) {
      const pathPoints = [
        new THREE.Vector3(0, 0.3, 0),
        new THREE.Vector3(targetX, targetY + 0.3, targetZ),
      ];
      const pathGeo = new THREE.BufferGeometry().setFromPoints(pathPoints);
      const pathMat = new THREE.LineDashedMaterial({
        color: 0x818cf8,
        dashSize: 0.15,
        gapSize: 0.08,
      });
      deltaLine = new THREE.Line(pathGeo, pathMat);
      deltaLine.computeLineDistances();
      vectorGroup.add(deltaLine);
    }

    // 6. Satellites (Themes) Orbiting the Human Figures
    const satellites: { mesh: THREE.Mesh; angle: number; radius: number; speed: number }[] = [];

    themes.forEach((theme, index) => {
      let color = 0x10b981; // Safe: Emerald Green
      if (theme.saturation >= 0.8) {
        color = 0xef4444; // Warning: Red
      } else if (theme.saturation > 0.4) {
        color = 0xf97316; // Saturation warning: Orange
      }

      const size = 0.08 + theme.depth * 0.12;
      const satGeo = new THREE.SphereGeometry(size, 16, 16);
      const satMat = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.4,
        shininess: 20,
      });
      const satMesh = new THREE.Mesh(satGeo, satMat);

      const radius = 1.4 + index * 0.7;
      const speed = 0.008 + theme.momentum * 0.03;

      // Add thin orbital rings around the central human
      const ringGeo = new THREE.RingGeometry(radius - 0.008, radius + 0.008, 64);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x27272a, side: THREE.DoubleSide });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      vectorGroup.add(ring);

      vectorGroup.add(satMesh);
      satellites.push({
        mesh: satMesh,
        angle: Math.random() * Math.PI * 2,
        radius: radius,
        speed: speed,
      });
    });

    // 7. Text labels overlay
    const createTextSprite = (text: string, colorStr: string) => {
      const canvas = document.createElement("canvas");
      canvas.width = 128;
      canvas.height = 32;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = colorStr;
        ctx.font = "bold 14px monospace";
        ctx.textAlign = "center";
        ctx.fillText(text, 64, 20);
      }
      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({ map: texture });
      return new THREE.Sprite(material);
    };

    const currentLabel = createTextSprite("CURRENT SELF", "#3b82f6");
    currentLabel.position.set(0, 0.9, 0);
    currentLabel.scale.set(1.5, 0.4, 1);
    vectorGroup.add(currentLabel);

    const targetLabel = createTextSprite("TARGET SELF", "#f59e0b");
    targetLabel.position.set(targetX, targetY + 0.9, targetZ);
    targetLabel.scale.set(1.5, 0.4, 1);
    vectorGroup.add(targetLabel);

    // 8. Animation Loop
    let animationFrameId: number;
    let clockTime = 0;
    
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      clockTime += 0.02;

      // Slow orbital rotate
      vectorGroup.rotation.y += 0.004;

      // Stylized breathing motion (breathing scales Y scale slightly)
      const currentScaleY = 1.0 + Math.sin(clockTime * 1.5) * 0.03;
      const targetScaleY = 1.0 + Math.sin(clockTime * 1.2 + 1) * 0.03;
      
      currentHuman.scale.set(1, currentScaleY, 1);
      targetHuman.scale.set(1, targetScaleY, 1);

      // If they are close (low drift), make them glow/pulse higher representing overlap/alignment
      if (driftScore < 0.1) {
        // High alignment: increase emissive intensities to represent blend/mixing state
        (currentHuman.children[0] as THREE.Mesh).scale.setScalar(1.0 + Math.sin(clockTime * 3) * 0.04);
        (targetHuman.children[0] as THREE.Mesh).scale.setScalar(1.0 + Math.sin(clockTime * 3) * 0.04);
      }

      // Update satellites position
      satellites.forEach((sat) => {
        sat.angle += sat.speed;
        sat.mesh.position.x = Math.cos(sat.angle) * sat.radius;
        sat.mesh.position.z = Math.sin(sat.angle) * sat.radius;
        sat.mesh.position.y = Math.sin(sat.angle * 2) * 0.1;
      });

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handler
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 300;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // 10. Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      cancelAnimationFrame(animationFrameId);
      container.removeChild(renderer.domElement);
      renderer.dispose();
      
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
    };
  }, [themes, driftScore]);

  return (
    <div className="w-full h-full relative">
      <div ref={containerRef} className="w-full h-full min-h-[300px]"></div>
      
      {/* Visual Overlay Legend */}
      <div className="absolute bottom-2 left-4 flex gap-4 text-[9px] font-mono text-zinc-500 bg-zinc-950/80 p-2 rounded border border-zinc-900">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-1.5 rounded bg-blue-500 block"></span>
          <span>Current Self</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-1.5 rounded bg-amber-500 block"></span>
          <span>Target Self</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
          <span>Theme Orbits</span>
        </div>
      </div>
    </div>
  );
}
