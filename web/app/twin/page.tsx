"use client";

import React, { useState, useEffect } from "react";
import { Brain, Compass, Sparkles, AlertCircle, RefreshCw, BarChart2, Zap, ShieldAlert, Award } from "lucide-react";
import { fixtureSelfState } from "@/lib/fixtures";
import type { SelfState } from "@/lib/types";
import ThreeVectorSpace from "@/components/ThreeVectorSpace";

export default function SelfTwinPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [selfState, setSelfState] = useState<SelfState | null>(null);
  const [useMock, setUseMock] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUserId = localStorage.getItem("praxis_user_id");
    if (storedUserId) {
      setUserId(storedUserId);
      setUseMock(false);
    } else {
      setSelfState(fixtureSelfState);
    }
  }, []);

  useEffect(() => {
    if (useMock || !userId) {
      setSelfState(fixtureSelfState);
      return;
    }

    const fetchSelfState = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/self/${userId}`);
        if (!res.ok) throw new Error("API failed");
        const data = (await res.json()) as SelfState;
        setSelfState(data);
      } catch (err) {
        console.error("Live SelfState fetch failed, falling back to mock:", err);
        setSelfState(fixtureSelfState);
      } finally {
        setLoading(false);
      }
    };

    fetchSelfState();
  }, [userId, useMock]);

  if (loading || !selfState) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col items-center justify-center text-zinc-400 gap-3">
        <RefreshCw className="h-6 w-6 animate-spin text-indigo-400" />
        <span className="text-xs font-mono tracking-widest uppercase">Fetching Self Twin...</span>
      </div>
    );
  }

  // §10: Alignment/Momentum/Saturation/Drift come straight off risk_like_state —
  // each tile's value AND its driver text, not a locally re-derived approximation.
  const { alignment, momentum, saturation, drift } = selfState.risk_like_state;

  return (
    <div className="flex-1 bg-zinc-950 p-6 md:p-12 text-zinc-100 flex flex-col">
      <div className="mx-auto w-full max-w-4xl space-y-8">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
          <div>
            <h2 className="text-xs font-mono font-bold tracking-widest uppercase text-zinc-400">
              Identity Matrix
            </h2>
            <p className="text-[10px] text-zinc-600 font-mono mt-0.5">
              The rolling state of who you are trying to become.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono text-zinc-600">
              Mode: {useMock ? "Offline Mock" : "Live Backend"}
            </span>
            <button
              onClick={() => setUseMock(!useMock)}
              className="text-[10px] font-mono border border-zinc-800 hover:border-zinc-700 px-2 py-0.5 rounded text-zinc-400 hover:text-zinc-200"
            >
              [Toggle Mode]
            </button>
          </div>
        </div>

        {/* 3D Identity Space Visualizer */}
        <div className="bg-[#141414] border border-zinc-900 rounded-xl p-6 relative overflow-hidden">
          <div className="flex items-center gap-2 text-zinc-400 mb-2 border-b border-zinc-900/60 pb-3">
            <Brain className="h-4 w-4 text-indigo-400" />
            <span className="text-[10px] font-mono font-bold tracking-wider uppercase">3D Identity Trajectory (Dual-Vector)</span>
          </div>
          <div className="h-[320px] w-full flex items-center justify-center">
            <ThreeVectorSpace themes={selfState.themes} driftScore={selfState.risk_like_state.drift.value} />
          </div>
          <p className="text-[9px] font-mono text-zinc-500 mt-2 text-center">
            Visualising the gap vector (target minus current). Theme orbits spin relative to momentum.
          </p>
        </div>

        {/* 1. Stated Aspirations Section */}
        <div className="bg-[#141414] border border-zinc-900 rounded-xl p-6">
          <div className="flex items-center gap-2 text-zinc-400 mb-3">
            <Award className="h-4 w-4 text-indigo-400" />
            <span className="text-[10px] font-mono font-bold tracking-wider uppercase">Active Goals & Aspirations</span>
          </div>
          <div className="space-y-3">
            {selfState.aspirations.map((asp) => (
              <div key={asp.id} className="flex items-center justify-between border-b border-zinc-900/40 pb-2.5 last:border-0 last:pb-0">
                <p className="text-zinc-200 text-sm font-medium">"{asp.text}"</p>
                <span className={`px-2 py-0.5 rounded text-[9px] font-mono border capitalize ${
                  asp.status === "active" 
                    ? "border-emerald-950 bg-emerald-950/20 text-emerald-400" 
                    : "border-amber-950 bg-amber-950/20 text-amber-400"
                }`}>
                  {asp.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 2. Core Metrics 4-Tile Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Tile 1: Alignment */}
          <div className="bg-[#141414] border border-zinc-900 rounded-xl p-5 flex flex-col justify-between min-h-[8.5rem]">
            <div className="flex items-center justify-between border-b border-zinc-900/60 pb-2 mb-2">
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase">Alignment</span>
              <Compass className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <span className="text-2xl font-mono font-bold text-indigo-400">
                {Math.round(alignment.value * 100)}%
              </span>
              <p className="text-[9px] font-mono text-zinc-500 mt-1 leading-normal">
                {alignment.driver}
              </p>
            </div>
          </div>

          {/* Tile 2: Momentum */}
          <div className="bg-[#141414] border border-zinc-900 rounded-xl p-5 flex flex-col justify-between min-h-[8.5rem]">
            <div className="flex items-center justify-between border-b border-zinc-900/60 pb-2 mb-2">
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase">Momentum</span>
              <Zap className="h-4 w-4 text-emerald-400" />
            </div>
            <div>
              <span className="text-2xl font-mono font-bold text-emerald-400">
                {momentum.value.toFixed(2)}
              </span>
              <p className="text-[9px] font-mono text-zinc-500 mt-1 leading-normal">
                {momentum.driver}
              </p>
            </div>
          </div>

          {/* Tile 3: Saturation */}
          <div className="bg-[#141414] border border-zinc-900 rounded-xl p-5 flex flex-col justify-between min-h-[8.5rem]">
            <div className="flex items-center justify-between border-b border-zinc-900/60 pb-2 mb-2">
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase">Saturation</span>
              <ShieldAlert className="h-4 w-4 text-rose-400" />
            </div>
            <div>
              <span className="text-2xl font-mono font-bold text-rose-400">
                {saturation.value.toFixed(2)}
              </span>
              <p className="text-[9px] font-mono text-zinc-500 mt-1 leading-normal">
                {saturation.driver}
              </p>
            </div>
          </div>

          {/* Tile 4: Drift */}
          <div className="bg-[#141414] border border-zinc-900 rounded-xl p-5 flex flex-col justify-between min-h-[8.5rem]">
            <div className="flex items-center justify-between border-b border-zinc-900/60 pb-2 mb-2">
              <span className="text-[10px] font-mono font-bold text-zinc-500 uppercase">Drift</span>
              <Brain className="h-4 w-4 text-amber-400" />
            </div>
            <div>
              <span className="text-2xl font-mono font-bold text-amber-400">
                {drift.value.toFixed(2)}
              </span>
              <p className="text-[9px] font-mono text-zinc-500 mt-1 leading-normal">
                {drift.driver}
              </p>
            </div>
          </div>

        </div>

        {/* 3. Theme Depth Grid (Beta-Bernoulli Knowledge Tracing Arithmetic) */}
        <div className="bg-[#141414] border border-zinc-900 rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900/60 pb-3">
            <div className="flex items-center gap-2 text-zinc-400">
              <BarChart2 className="h-4 w-4 text-indigo-400" />
              <span className="text-[10px] font-mono font-bold tracking-wider uppercase">Beta-Bernoulli Knowledge Depth</span>
            </div>
            <span className="text-[9px] font-mono text-zinc-600 uppercase">Prior Probability: B(1.0, 1.0)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {selfState.themes.map((theme) => {
              // Posterior mean: alpha / (alpha + beta)
              const depthPct = Math.round(theme.depth * 100);
              
              return (
                <div key={theme.id} className="border border-zinc-900/80 bg-zinc-950/40 rounded-xl p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-zinc-200">{theme.name}</h4>
                      <span className="text-[9px] font-mono text-zinc-600 block mt-0.5">Slug: {theme.slug}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-indigo-400">{depthPct}% Depth</span>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="space-y-1">
                    <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-indigo-500/80 rounded-full transition-all duration-500"
                        style={{ width: `${depthPct}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-[9px] font-mono text-zinc-600">
                      <span>Beginner</span>
                      <span>Intermediate</span>
                      <span>Mastery</span>
                    </div>
                  </div>

                  {/* Behind-the-scenes math data */}
                  <div className="grid grid-cols-3 gap-2 border-t border-zinc-900/50 pt-3 text-[10px] font-mono">
                    <div className="bg-zinc-900/20 p-2 rounded">
                      <span className="block text-[8px] text-zinc-600 uppercase">Alpha (Succeeds)</span>
                      <span className="text-emerald-400">α = {theme.alpha.toFixed(2)}</span>
                    </div>
                    <div className="bg-zinc-900/20 p-2 rounded">
                      <span className="block text-[8px] text-zinc-600 uppercase">Beta (Struggles)</span>
                      <span className="text-rose-400">β = {theme.beta.toFixed(2)}</span>
                    </div>
                    <div className="bg-zinc-900/20 p-2 rounded">
                      <span className="block text-[8px] text-zinc-600 uppercase">Formula</span>
                      <span className="text-zinc-500">α / (α + β)</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
