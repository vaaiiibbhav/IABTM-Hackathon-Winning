"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { fixtureFeed } from "@/lib/fixtures";
import type { FeedItem } from "@/lib/types";
import { ScoreBreakdownGrid } from "@/components/breakdown";
import { pct } from "@/lib/format";

export default function WhyPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [items, setItems] = useState<FeedItem[] | null>(null);
  const [useMock, setUseMock] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const storedUserId = localStorage.getItem("praxis_user_id");
    if (storedUserId) {
      setUserId(storedUserId);
      setUseMock(false);
    } else {
      setItems(fixtureFeed);
    }
  }, []);

  useEffect(() => {
    if (useMock || !userId) {
      setItems(fixtureFeed);
      return;
    }

    const fetchDecisions = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/decisions/${userId}`);
        if (!res.ok) throw new Error("API failed");
        const data = (await res.json()) as FeedItem[];
        setItems(data);
      } catch (err) {
        console.error("Live decision log fetch failed, falling back to mock:", err);
        setItems(fixtureFeed);
      } finally {
        setLoading(false);
      }
    };

    fetchDecisions();
  }, [userId, useMock]);

  if (loading || !items) {
    return (
      <div className="flex-1 bg-background flex flex-col items-center justify-center text-muted-foreground gap-3">
        <RefreshCw className="h-5 w-5 animate-spin text-agent" />
        <span className="label-caps">Fetching decision log…</span>
      </div>
    );
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-10">
      <header className="mb-6 flex items-start justify-between border-b border-border pb-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Why</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            The decision log. Every item traces to arithmetic — nothing here is vibes.
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
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
      </header>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No decisions logged yet.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((item, index) => (
            <div key={`${item.candidate.id}-${index}`} className="panel p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="label-caps">
                    {item.candidate.kind} · {item.candidate.provider}
                  </span>
                  <h3 className="mt-0.5 text-base font-semibold text-foreground">
                    {item.candidate.title}
                  </h3>
                  <a
                    href={item.candidate.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1.5 inline-flex items-center gap-1 text-xs font-mono text-agent hover:underline"
                  >
                    Open Link ↗
                  </a>
                </div>
                <div className="shrink-0 text-right">
                  <div className="label-caps">growth score</div>
                  <div className="score-mono text-lg font-semibold text-agent">
                    {item.breakdown.score.toFixed(2)}
                  </div>
                </div>
              </div>

              <ScoreBreakdownGrid breakdown={item.breakdown} className="mt-4" />

              <div className="mt-4 rounded-lg border border-border bg-secondary/40 p-3">
                <div className="label-caps">what it beat</div>
                {item.counterfactual_candidate ? (
                  <p className="mt-1 text-sm text-foreground">
                    {item.counterfactual_candidate.title}{" "}
                    <span className="score-mono text-muted-foreground">
                      (engagement score{" "}
                      {item.counterfactual_engagement_score !== null
                        ? pct(item.counterfactual_engagement_score)
                        : "—"}
                      )
                    </span>
                  </p>
                ) : (
                  <p className="mt-1 text-sm text-muted-foreground">
                    No meaningful counterfactual — nothing in the pool scored meaningfully
                    differently under the engagement objective.
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
