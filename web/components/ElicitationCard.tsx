"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Compass, HelpCircle, ShieldAlert, Sparkles, UserCheck, ArrowRight } from "lucide-react";
import type { InterventionType } from "../lib/types";

interface ElicitationCardProps {
  type: "onboarding" | InterventionType | "check_in";
  step?: number;
  of?: number;
  title?: string;
  body: string;
  options: string[] | null;
  onResolve: (answer: string | null, accept?: boolean) => void;
}

export default function ElicitationCard({
  type,
  step,
  of,
  title,
  body,
  options,
  onResolve,
}: ElicitationCardProps) {
  const [textInput, setTextInput] = useState("");

  const getIcon = () => {
    switch (type) {
      case "onboarding":
        return <Compass className="h-5 w-5 text-indigo-400 animate-pulse" />;
      case "do_block":
        return <ShieldAlert className="h-5 w-5 text-rose-500 animate-bounce" />;
      case "drift_proposal":
        return <Brain className="h-5 w-5 text-amber-400 animate-pulse" />;
      case "nudge":
        return <Sparkles className="h-5 w-5 text-emerald-400" />;
      case "calibration":
        return <HelpCircle className="h-5 w-5 text-sky-400" />;
      case "check_in":
        return <UserCheck className="h-5 w-5 text-teal-400" />;
      default:
        return <Compass className="h-5 w-5 text-zinc-400" />;
    }
  };

  const getTypeLabel = () => {
    switch (type) {
      case "onboarding":
        return `Onboarding Interview • Step ${step} of ${of}`;
      case "do_block":
        return "System Lock: Saturation Limit Reached";
      case "drift_proposal":
        return "Identity Alignment Check";
      case "nudge":
        return "Daily Growth Nudge";
      case "calibration":
        return "Level Calibration";
      case "check_in":
        return "Reflection Check-in";
      default:
        return "Praxis Elicitation";
    }
  };

  const getBorderColor = () => {
    switch (type) {
      case "do_block":
        return "border-rose-950/70 hover:border-rose-900";
      case "drift_proposal":
        return "border-amber-950/70 hover:border-amber-900";
      case "nudge":
        return "border-emerald-950/70 hover:border-emerald-900";
      default:
        return "border-zinc-800 hover:border-zinc-700";
    }
  };

  const getHeaderBg = () => {
    switch (type) {
      case "do_block":
        return "bg-rose-950/20";
      case "drift_proposal":
        return "bg-amber-950/20";
      case "nudge":
        return "bg-emerald-950/20";
      default:
        return "bg-zinc-900/40";
    }
  };

  const handleSubmitText = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onResolve(textInput, true);
      setTextInput("");
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className={`w-full max-w-xl overflow-hidden rounded-xl border ${getBorderColor()} bg-[#1C1C1C] shadow-2xl backdrop-blur transition-colors`}
    >
      {/* Header Info */}
      <div className={`flex items-center gap-3 px-5 py-3.5 border-b border-zinc-900/60 ${getHeaderBg()}`}>
        {getIcon()}
        <span className="text-[10px] font-mono font-bold tracking-widest text-zinc-400 uppercase">
          {getTypeLabel()}
        </span>
      </div>

      {/* Main Body */}
      <div className="p-6">
        <h3 className="text-lg font-semibold text-zinc-100 mb-2 leading-snug">
          {title || "Praxis Mentor Inquiry"}
        </h3>
        <p className="text-zinc-400 text-sm leading-relaxed mb-6 font-sans">
          {body}
        </p>

        {/* Dynamic Inputs */}
        <AnimatePresence mode="wait">
          {options === null ? (
            <motion.form
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onSubmit={handleSubmitText}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                autoFocus
                placeholder="Enter your aspiration..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-700 focus:outline-none focus:ring-1 focus:ring-zinc-700 font-sans"
              />
              <button
                type="submit"
                className="flex items-center justify-center p-2.5 rounded-lg bg-zinc-100 text-zinc-950 hover:bg-zinc-200 transition-colors"
              >
                <ArrowRight className="h-5 w-5" />
              </button>
            </motion.form>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-2.5"
            >
              {options.map((opt, i) => {
                // Determine layout or style of option buttons
                const isAcceptOption = opt.toLowerCase().includes("accept") || opt.toLowerCase().includes("update") || opt.toLowerCase().includes("yes");
                const isRejectOption = opt.toLowerCase().includes("reject") || opt.toLowerCase().includes("hold") || opt.toLowerCase().includes("no");
                
                let buttonStyle = "border-zinc-800 bg-zinc-900/40 hover:bg-zinc-800/60 text-zinc-300 hover:text-zinc-100";
                if (type === "do_block") {
                  buttonStyle = "border-rose-900/30 bg-rose-950/10 hover:bg-rose-950/20 text-rose-300 hover:text-rose-100 hover:border-rose-900/60";
                } else if (type === "drift_proposal" && isAcceptOption) {
                  buttonStyle = "border-amber-900/40 bg-amber-950/10 hover:bg-amber-950/20 text-amber-300 hover:text-amber-100 hover:border-amber-900/70";
                } else if (type === "drift_proposal" && isRejectOption) {
                  buttonStyle = "border-zinc-800 bg-zinc-900/40 hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200";
                }

                return (
                  <button
                    key={i}
                    onClick={() => {
                      // Call onResolve mapping:
                      // If it's a binary choice like drift_proposal, we pass accept: true/false
                      const accept = isAcceptOption ? true : isRejectOption ? false : undefined;
                      onResolve(opt, accept);
                    }}
                    className={`w-full rounded-lg border px-4 py-3 text-left text-xs font-mono font-medium tracking-wide transition-all ${buttonStyle}`}
                  >
                    {opt}
                  </button>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
