"use client";

import React, { useState, useEffect } from "react";
import { Brain, Compass, RefreshCw, BarChart2, Zap, ShieldAlert, Award } from "lucide-react";
import { fixtureSelfState } from "@/lib/fixtures";
import type { SelfState } from "@/lib/types";
import ThreeVectorSpace from "@/components/ThreeVectorSpace";
import { cn } from "@/lib/utils";

// Same thresholds the backend fires on (feed.py saturation gate, events.py
// DRIFT_DETECTED) — a tile only breaks from quiet-neutral when it's about to
// (or has) triggered a real agent action, never as decoration.
const SATURATION_ALERT = 0.85;
const DRIFT_ALERT = 0.35;

export default function SelfTwinPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [selfState, setSelfState] = useState<SelfState | null>(null);
  const [useMock, setUseMock] = useState(false);
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
      <div className="flex-1 bg-background flex flex-col items-center justify-center text-muted-foreground gap-3">
        <RefreshCw className="h-5 w-5 animate-spin text-agent" />
        <span className="label-caps">Fetching Self Twin…</span>
      </div>
    );
  }

  // §10: Alignment/Momentum/Saturation/Drift come straight off risk_like_state —
  // each tile's value AND its driver text, not a locally re-derived approximation.
  const { alignment, momentum, saturation, drift } = selfState.risk_like_state;
  const saturationHot = saturation.value >= SATURATION_ALERT;
  const driftHot = drift.value >= DRIFT_ALERT;

  return (
    <div className="flex-1 bg-background px-6 py-10 md:px-10 text-foreground flex flex-col">
      <div className="mx-auto w-full max-w-3xl space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div>
            <h2 className="label-caps text-foreground">Identity matrix</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              The rolling state of who you are trying to become.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[0.65rem] font-mono text-muted-foreground">
              {useMock ? "Offline mock" : "Live backend"}
            </span>
            <button
              onClick={() => setUseMock(!useMock)}
              className="text-[0.65rem] font-mono border border-border hover:border-muted-foreground/40 px-2 py-0.5 rounded text-muted-foreground hover:text-foreground transition-colors"
            >
              Toggle mode
            </button>
          </div>
        </div>

        {/* 3D Identity Space Visualizer */}
        <div className="panel p-5 relative overflow-hidden">
          <div className="flex items-center gap-2 text-muted-foreground mb-2 border-b border-border pb-2.5">
            <Brain className="h-3.5 w-3.5" />
            <span className="label-caps">3D identity trajectory (dual-vector)</span>
          </div>
          <div className="h-[320px] w-full flex items-center justify-center">
            <ThreeVectorSpace themes={selfState.themes} driftScore={selfState.risk_like_state.drift.value} />
          </div>
          <p className="text-xs font-mono text-muted-foreground/70 mt-2 text-center">
            Visualising the gap vector (target minus current). Theme orbits spin relative to momentum.
          </p>
        </div>

        {/* 1. Stated Aspirations Section */}
        <div className="panel p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-3">
            <Award className="h-3.5 w-3.5" />
            <span className="label-caps">Active goals & aspirations</span>
          </div>
          <div className="space-y-2.5">
            {selfState.aspirations.map((asp) => (
              <div key={asp.id} className="flex items-center justify-between border-b border-border/60 pb-2.5 last:border-0 last:pb-0">
                <p className="text-foreground text-sm font-medium">"{asp.text}"</p>
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-[0.65rem] font-mono border capitalize",
                    asp.status === "active"
                      ? "border-agent/40 bg-agent/10 text-agent"
                      : "border-border text-muted-foreground"
                  )}
                >
                  {asp.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 2. Core Metrics 4-Tile Grid — quiet by default, a tile only lights
            up when its value has crossed the threshold that fires a real
            backend event; color here is information, not decoration. */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">

          <MetricTile
            icon={<Compass className="h-3.5 w-3.5" />}
            label="Alignment"
            value={`${Math.round(alignment.value * 100)}%`}
            driver={alignment.driver}
          />

          <MetricTile
            icon={<Zap className="h-3.5 w-3.5" />}
            label="Momentum"
            value={momentum.value.toFixed(2)}
            driver={momentum.driver}
          />

          <MetricTile
            icon={<ShieldAlert className="h-3.5 w-3.5" />}
            label="Saturation"
            value={saturation.value.toFixed(2)}
            driver={saturation.driver}
            hot={saturationHot}
            hotTone="destructive"
          />

          <MetricTile
            icon={<Brain className="h-3.5 w-3.5" />}
            label="Drift"
            value={drift.value.toFixed(2)}
            driver={drift.driver}
            hot={driftHot}
            hotTone="agent"
          />

        </div>

        {/* 3. Theme Depth Grid (Beta-Bernoulli Knowledge Tracing Arithmetic) */}
        <div className="panel p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <div className="flex items-center gap-2 text-muted-foreground">
              <BarChart2 className="h-3.5 w-3.5" />
              <span className="label-caps">Beta-Bernoulli knowledge depth</span>
            </div>
            <span className="text-xs font-mono text-muted-foreground">Prior: B(1.0, 1.0)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {selfState.themes.map((theme) => {
              // Posterior mean: alpha / (alpha + beta)
              const depthPct = Math.round(theme.depth * 100);

              return (
                <div key={theme.id} className="border border-border bg-secondary/30 rounded-xl p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-base font-semibold text-foreground">{theme.name}</h4>
                      <span className="text-xs font-mono text-muted-foreground block mt-0.5">{theme.slug}</span>
                    </div>
                    <span className="score-mono text-sm font-bold text-emerald-400">{depthPct}% depth</span>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="space-y-1.5">
                    <div className="h-2.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                        style={{ width: `${depthPct}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[0.7rem] font-mono text-muted-foreground">
                      <span>Beginner</span>
                      <span>Intermediate</span>
                      <span>Mastery</span>
                    </div>
                  </div>

                  {/* Behind-the-scenes math data */}
                  <div className="grid grid-cols-3 gap-2 border-t border-border pt-4">
                    <div className="bg-background/40 p-2.5 rounded-lg border border-border/30">
                      <span className="block text-[0.7rem] text-zinc-400 font-semibold uppercase">Alpha</span>
                      <span className="score-mono text-sm font-bold text-foreground">α = {theme.alpha.toFixed(2)}</span>
                    </div>
                    <div className="bg-background/40 p-2.5 rounded-lg border border-border/30">
                      <span className="block text-[0.7rem] text-zinc-400 font-semibold uppercase">Beta</span>
                      <span className="score-mono text-sm font-bold text-foreground">β = {theme.beta.toFixed(2)}</span>
                    </div>
                    <div className="bg-background/40 p-2.5 rounded-lg border border-border/30">
                      <span className="block text-[0.7rem] text-zinc-400 font-semibold uppercase">Formula</span>
                      <span className="score-mono text-xs font-semibold text-muted-foreground">α/(α+β)</span>
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

function MetricTile({
  icon,
  label,
  value,
  driver,
  hot = false,
  hotTone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  driver: string;
  hot?: boolean;
  hotTone?: "destructive" | "agent";
}) {
  const toneText = hot && hotTone === "destructive" ? "text-destructive" : hot && hotTone === "agent" ? "text-agent" : "text-foreground";
  const toneBorder = hot && hotTone === "destructive" ? "border-destructive/30" : hot && hotTone === "agent" ? "border-agent/30" : "border-border";

  return (
    <div className={cn("panel p-5 flex flex-col justify-between min-h-36 border shadow-lg", toneBorder)}>
      <div className="flex items-center justify-between border-b border-border pb-2.5 mb-3 text-muted-foreground">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">{label}</span>
        {icon}
      </div>
      <div>
        <span className={cn("score-mono text-3xl font-extrabold", toneText)}>{value}</span>
        <p className="text-xs md:text-sm font-medium text-zinc-300 mt-2 leading-relaxed">{driver}</p>
      </div>
    </div>
  );
}
