"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ElicitationOption {
  label: string;
  value: string;
}

export interface ElicitationCardProps {
  /** small caption above the prompt, e.g. "Step 2 of 4" or "Drift proposal" */
  meta?: string;
  prompt: string;
  /** null => single free-text field (only the onboarding aspiration step uses this) */
  options: ElicitationOption[] | null;
  onSelect?: (value: string) => void;
}

/**
 * The ONE elicitation surface (CLAUDE.md §5a/§10): onboarding interview steps,
 * the post-item check-in, and every `Intervention` all render through this —
 * same shape, same one-tap interaction, never a free-text chat box.
 */
export function ElicitationCard({ meta, prompt, options, onSelect }: ElicitationCardProps) {
  const [resolved, setResolved] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  function resolve(value: string) {
    if (!value.trim()) return;
    setResolved(value);
    onSelect?.(value);
  }

  return (
    <motion.div layout className="panel p-4" data-slot="elicitation-card">
      {meta && <div className="label-caps mb-1.5">{meta}</div>}
      <p className="text-sm leading-relaxed text-foreground">{prompt}</p>

      {resolved ? (
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-agent/40 bg-agent/10 px-3 py-1 text-sm text-agent">
          <Check className="size-3.5" />
          {options?.find((o) => o.value === resolved)?.label ?? resolved}
        </div>
      ) : options ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => resolve(opt.value)}
              className={cn(
                "rounded-full border border-border bg-secondary px-3 py-1.5 text-sm text-foreground",
                "transition-colors hover:border-agent/50 hover:bg-agent/10 hover:text-agent"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      ) : (
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            resolve(draft);
          }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type your answer…"
            className="h-9 flex-1 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          />
          <button
            type="submit"
            className="rounded-md bg-agent px-3 text-sm font-medium text-agent-foreground"
          >
            Next
          </button>
        </form>
      )}
    </motion.div>
  );
}
