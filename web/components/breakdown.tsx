import { Check, X } from "lucide-react";
import type { ScoreBreakdown } from "@/lib/types";
import { pct, signed } from "@/lib/format";
import { cn } from "@/lib/utils";

const FIELDS: { key: keyof Omit<ScoreBreakdown, "score">; label: string }[] = [
  { key: "alignment", label: "Alignment" },
  { key: "readiness", label: "Readiness" },
  { key: "actionability", label: "Actionability" },
  { key: "novelty", label: "Novelty" },
  { key: "effort_fit", label: "Effort fit" },
  { key: "trust_weight", label: "Trust weight" },
  { key: "saturation_penalty", label: "Saturation penalty" },
];

/** Full 7-field breakdown + final score, printable arithmetic (CLAUDE.md I3/I4). */
export function ScoreBreakdownGrid({
  breakdown,
  className,
}: {
  breakdown: ScoreBreakdown;
  className?: string;
}) {
  return (
    <div className={cn("grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-4", className)}>
      {FIELDS.map(({ key, label }) => (
        <div key={key} className="flex flex-col">
          <span className="label-caps">
            {label}
          </span>
          <span className="score-mono text-sm text-foreground">
            {key === "saturation_penalty" ? `-${pct(breakdown[key])}` : pct(breakdown[key])}
          </span>
        </div>
      ))}
      <div className="flex flex-col">
        <span className="label-caps text-agent">Score</span>
        <span className="score-mono text-sm font-semibold text-agent">
          {signed(breakdown.score)}
        </span>
      </div>
    </div>
  );
}

/** ✓/✗ pill — used for actionable / novel style boolean reads off the breakdown. */
export function BoolBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
        ok
          ? "border-agent/40 bg-agent/10 text-agent"
          : "border-border text-muted-foreground"
      )}
    >
      {ok ? <Check className="size-3" /> : <X className="size-3" />}
      {label}
    </span>
  );
}
