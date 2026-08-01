"use client";

import { useRef, useState } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { motion } from "framer-motion";
import { ArrowLeftRight, Clock, ShieldCheck } from "lucide-react";
import type { FeedItem } from "@/lib/types";
import { pct, views } from "@/lib/format";
import { BoolBadge, ScoreBreakdownGrid } from "@/components/breakdown";
import { cn } from "@/lib/utils";

/** Moat 1 (CLAUDE.md §2): same candidate pool, two objectives — GSAP 3D flip to see both. */
export function FeedCard({ item }: { item: FeedItem }) {
  const [flipped, setFlipped] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const { candidate, breakdown, counterfactual_candidate, counterfactual_engagement_score } =
    item;
  const hasCounterfactual = counterfactual_candidate !== null;

  useGSAP(
    () => {
      if (!innerRef.current) return;
      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduced) {
        gsap.set(innerRef.current, { rotateY: flipped ? 180 : 0 });
        return;
      }
      gsap.to(innerRef.current, {
        rotateY: flipped ? 180 : 0,
        duration: 0.55,
        ease: "power2.inOut",
      });
    },
    { dependencies: [flipped], scope: cardRef }
  );

  return (
    <motion.div layout className="panel overflow-hidden [perspective:1200px]">
      <div ref={cardRef}>
        <div ref={innerRef} className="relative [transform-style:preserve-3d]">
          {/* front — sizes the card */}
          <div className="p-5 [backface-visibility:hidden]">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <span className="label-caps">
                  {candidate.kind} · {candidate.provider}
                </span>
                <h3 className="mt-0.5 text-base font-semibold leading-snug text-foreground">
                  {candidate.title}
                </h3>
              </div>
              <div className="shrink-0 text-right">
                <div className="label-caps">growth score</div>
                <div className="score-mono text-lg font-semibold text-agent">
                  {breakdown.score.toFixed(2)}
                </div>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3.5" /> {candidate.minutes} min
              </span>
              {candidate.verified && (
                <span className="inline-flex items-center gap-1">
                  <ShieldCheck className="size-3.5" /> verified
                </span>
              )}
              <BoolBadge ok={breakdown.actionability > 0} label="actionable" />
              <BoolBadge ok={breakdown.novelty >= 0.5} label="novel" />
            </div>

            {hasCounterfactual && (
              <button
                type="button"
                onClick={() => setFlipped(true)}
                className="mt-4 inline-flex items-center gap-1.5 rounded-md border border-agent/40 bg-agent/10 px-3 py-1.5 text-sm text-agent transition-colors hover:bg-agent/20"
              >
                <ArrowLeftRight className="size-3.5" />
                See what engagement would have picked
              </button>
            )}
          </div>

          {/* back — overlaid, pre-rotated */}
          <div className="absolute inset-0 p-5 [backface-visibility:hidden] [transform:rotateY(180deg)]">
            <button
              type="button"
              onClick={() => setFlipped(false)}
              className="mb-3 inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeftRight className="size-3.5" /> back
            </button>

            <div className={cn("grid gap-4", hasCounterfactual && "sm:grid-cols-2")}>
              <div className="rounded-lg border border-agent/30 bg-agent/[0.06] p-4">
                <div className="label-caps text-agent">What Praxis chose</div>
                <h4 className="mt-1 text-sm font-medium leading-snug text-foreground">
                  {candidate.title}
                </h4>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <BoolBadge ok={breakdown.actionability > 0} label="actionable" />
                  <BoolBadge ok={breakdown.novelty >= 0.5} label="novel" />
                </div>
                <ScoreBreakdownGrid breakdown={breakdown} className="mt-3" />
              </div>

              <div className="rounded-lg border border-border bg-secondary/40 p-4">
                <div className="label-caps">What engagement would pick</div>
                {hasCounterfactual && counterfactual_candidate ? (
                  <>
                    <h4 className="mt-1 text-sm font-medium leading-snug text-foreground">
                      {counterfactual_candidate.title}
                    </h4>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      <BoolBadge
                        ok={counterfactual_candidate.has_practice}
                        label="actionable"
                      />
                      <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                        {views(counterfactual_candidate.view_count)}
                      </span>
                      <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                        {counterfactual_candidate.minutes} min
                      </span>
                    </div>
                    <div className="mt-3 flex flex-col">
                      <span className="label-caps">predicted engagement score</span>
                      <span className="score-mono text-sm text-foreground">
                        {counterfactual_engagement_score !== null
                          ? pct(counterfactual_engagement_score)
                          : "—"}
                      </span>
                    </div>
                    <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                      Same candidate pool, the other objective. Not scored for alignment or
                      novelty — that&apos;s the point.
                    </p>
                  </>
                ) : (
                  <p className="mt-2 text-sm text-muted-foreground">
                    No meaningfully different engagement pick for this item.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
