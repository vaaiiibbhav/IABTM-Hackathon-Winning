import { fixtureCandidates, fixtureDecisions } from "@/lib/fixtures";
import { ScoreBreakdownGrid } from "@/components/breakdown";
import { pct } from "@/lib/format";

const candidatesById = Object.fromEntries(
  Object.values(fixtureCandidates).map((c) => [c.id, c])
);

export default function WhyPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-foreground">Why</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The decision log. Every item traces to arithmetic — nothing here is vibes.
        </p>
      </header>

      <div className="flex flex-col gap-4">
        {fixtureDecisions.map((decision) => {
          const candidate = candidatesById[decision.candidate_id];
          const counterfactual =
            decision.counterfactual_id !== null
              ? candidatesById[decision.counterfactual_id]
              : null;

          return (
            <div key={decision.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                    {candidate?.kind} · {candidate?.provider}
                  </span>
                  <h3 className="mt-0.5 text-base font-semibold text-foreground">
                    {candidate?.title ?? decision.candidate_id}
                  </h3>
                </div>
                <div className="shrink-0 text-right">
                  <div className="text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                    growth score
                  </div>
                  <div className="font-mono text-lg font-semibold text-agent">
                    {decision.growth_score.toFixed(2)}
                  </div>
                </div>
              </div>

              <ScoreBreakdownGrid breakdown={decision.breakdown} className="mt-4" />

              <div className="mt-4 rounded-lg border border-border bg-secondary/40 p-3">
                <div className="text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                  what it beat
                </div>
                {counterfactual ? (
                  <p className="mt-1 text-sm text-foreground">
                    {counterfactual.title}{" "}
                    <span className="font-mono text-muted-foreground">
                      (engagement score{" "}
                      {decision.counterfactual_score !== null
                        ? pct(decision.counterfactual_score)
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
          );
        })}
      </div>
    </main>
  );
}
