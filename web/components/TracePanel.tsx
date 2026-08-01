"use client";

import React, { useEffect, useState, useRef } from "react";
import { Terminal, Cpu, CheckCircle2, AlertCircle, Play, ChevronRight, ChevronDown } from "lucide-react";
import type { TraceFrame } from "../lib/types";

interface TracePanelProps {
  userId: string;
  isEnabled: boolean;
}

export default function TracePanel({ userId, isEnabled }: TracePanelProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [frames, setFrames] = useState<TraceFrame[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isEnabled || !userId) return;

    setFrames([]);
    setIsConnected(true);

    // Create EventSource listener
    const eventSource = new EventSource(`/api/self/${userId}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const frame = JSON.parse(event.data) as TraceFrame;
        setFrames((prev) => [...prev, frame]);
      } catch (err) {
        console.error("Error parsing trace frame:", err);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [userId, isEnabled]);

  // Autoscroll trace panel on new frame
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [frames]);

  if (!isEnabled) return null;

  return (
    <div
      className={`fixed bottom-4 right-4 z-40 flex flex-col rounded-xl border border-zinc-800 bg-zinc-950/95 shadow-2xl backdrop-blur transition-all duration-300 ${
        isOpen ? "h-80 w-96" : "h-12 w-64"
      }`}
    >
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-4 py-3 text-left hover:bg-zinc-900/50 rounded-t-xl select-none"
      >
        <div className="flex items-center gap-2 text-zinc-200">
          <Terminal className="h-4 w-4 text-emerald-500" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider">Agent Telemetry</span>
          {isConnected && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-zinc-500">
            {frames.length} frame{frames.length !== 1 ? "s" : ""}
          </span>
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-zinc-500" />
          )}
        </div>
      </button>

      {/* Frame logs */}
      {isOpen && (
        <div className="flex-1 flex flex-col p-3 overflow-hidden">
          <div
            ref={scrollRef}
            className="flex-1 bg-black/50 rounded-lg p-2 font-mono text-[11px] text-zinc-400 overflow-y-auto space-y-2 border border-zinc-900/60"
          >
            {frames.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-zinc-600 gap-1 select-none">
                <Cpu className="h-6 w-6 animate-pulse" />
                <span>Listening for agent triggers...</span>
              </div>
            ) : (
              frames.map((frame, index) => (
                <div key={index} className="border-b border-zinc-900/50 pb-1.5 last:border-b-0 last:pb-0">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <div className="flex items-center gap-1.5">
                      {frame.status === "started" && (
                        <Play className="h-3 w-3 text-amber-500 animate-pulse fill-amber-500" />
                      )}
                      {frame.status === "ok" && (
                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                      )}
                      {frame.status === "error" && (
                        <AlertCircle className="h-3 w-3 text-rose-500" />
                      )}
                      <span
                        className={`${
                          frame.status === "error"
                            ? "text-rose-400"
                            : frame.status === "started"
                            ? "text-amber-400"
                            : "text-zinc-200"
                        }`}
                      >
                        {frame.node}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500">{frame.ms}ms</span>
                  </div>
                  <p className="text-[10px] text-zinc-500 pl-4.5 mt-0.5 leading-relaxed">
                    {frame.summary}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
