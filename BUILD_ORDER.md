# PRAXIS — build order (v2, re-spec'd for the curator problem statement)

> Read CLAUDE.md fully first — this file assumes it. Paste-ready Claude
> Code prompts, hard acceptance tests. Don't start a phase until the
> previous one's acceptance test passes.

Lanes: **A** = agents (`api/agents/`) · **B** = backend (`api/engine/`, `api/routes/`, `api/models.py`) · **W** = web (`web/`) · **L** = lead (demo, pitch, scope, seeding)

---

## PHASE −1 — before you build (do this once, not mid-build)

- [ ] **3 × Gemini API keys**, one real structured-output call tested against `gemini-3.6-flash`. Confirm the model ID resolves. `temperature`/`top_p`/`top_k` are deprecated on 3.x — don't pass them.
- [ ] **3 × YouTube Data API v3 keys.** Test one `search.list`.
- [ ] Check whether `iambetterthanme.com/blogs` or their podcast expose an RSS feed. If yes, note the URL — it's a zero-quota source.
- [ ] **Supabase project**, connection string, `?sslmode=require` tested.
- [ ] **Resend account**, test email sent to a phone.
- [ ] `ollama pull llama3.1:8b` on one laptop — wifi insurance.
- [ ] **MCPs**: `chrome-devtools`, `shadcn`, `context7` connected in the main build session (`claude mcp list` to confirm). Higgsfield MCP (`https://mcp.higgsfield.ai/mcp`) goes in a **separate, short-lived session only**, never the main one — 30+ tool schemas is too much context to carry through the whole build.
- [ ] Repo root has `CLAUDE.md`, `BUILD_ORDER.md`, `web/`, `api/` — confirmed clean, no nested reference clones committed.
- [ ] `.env.example` with every key name; real values shared privately.

---

## PHASE 0 — H0→H1 · Contract lock

Nobody writes feature code this hour.

> **Claude Code prompt:** "Read CLAUDE.md fully. Create `api/schemas.py` with Pydantic v2 models: SelfSpec, Aspiration, Theme, Candidate, Decision, Signal, Intervention, Event, TraceFrame, RiskLikeState (Alignment/Momentum/Saturation/Drift), SelfState. Then `web/lib/types.ts` mirroring them field for field. Then `web/lib/fixtures.ts` exporting a realistic complete SelfState for a 'become a confident public speaker' user — 4 aspirations, 5 themes with varied depth/momentum/saturation, 8 candidates with score breakdowns, 3 decisions each showing a counterfactual, 2 interventions (one drift_proposal, one calibration). Do not write any other code."

**Acceptance:** `fixtures.ts` imports cleanly. Frontend lane starts immediately.

---

## PHASE 1 — H1→H4 · Three lanes in parallel, all on mocks

### Lane B — data layer
> "Read CLAUDE.md §3 (I1) and §8. Create `api/clock.py` (`now()`, `advance(days)`, `reset()` — real UTC + stored offset, never `datetime.now()` anywhere else). Create `api/models.py` with the full §8 schema as SQLAlchemy 2 async models — timestamps set by application code via `clock.now()`, never `server_default=func.now()`. Alembic migration. Unit test proving `advance(4)` moves `now()` forward exactly four days."

Then routes returning fixture-shaped JSON so the frontend can point at a real server.

### Lane W — the whole UI against fixtures
> "Read CLAUDE.md §10. Build three screens against `web/lib/fixtures.ts` only, no network calls: `/today` (bounded feed, each card flips to show its counterfactual side-by-side per §2 Moat 1, feed visibly ends — no infinite scroll), `/twin` (theme depth grid + Alignment/Momentum/Saturation/Drift tiles with driver text), `/why` (decision log, every score breakdown). Build ONE shared card component per §5a that renders interview steps, one-tap check-ins, and every intervention type (nudge/do_block/drift_proposal/calibration) — same shape everywhere. Warm dark, editorial aesthetic per IABTM's brand (`#2E2E2E` base), not generic dashboard chrome. Framer Motion `layout` on cards. No chat tab, no analytics tab."

### Lane A — first agents, CLI only
> "Read CLAUDE.md §3, §4, §5, §5a. Create `api/agents/llm.py`: Gemini client, `gemini-3.6-flash`/`gemini-3.5-flash-lite`, native structured output, one retry on validation failure, Ollama fallback behind the same interface. No temperature/top_p/top_k. Then `interviewer.py` (drives the 3-5 step structured onboarding interview, one question at a time) and `intake.py` (interview answers → SelfSpec). Add `python -m api.agents.cli` testable via a scripted set of answers, prints SelfSpec as JSON. No FastAPI, no database yet."

**H4 acceptance:** Lane A prints a valid SelfSpec from scripted interview answers. Lane W renders all three screens from fixtures, including the counterfactual flip. Lane B serves fixture-shaped JSON over HTTP.

---

## PHASE 2 — H4→H8 · First real end-to-end

> **Lane A+B together:** "Wire `api/agents/graph.py` as a LangGraph with entry points `create_self`, `curate_today`, `log_signal`, `answer_check_in`, `tick` (CLAUDE.md §5). Implement `POST /api/self/interview/start` and `/answer` running `interviewer` → `intake`, persisting to Postgres on the final step. Implement `GET /api/self/{id}` returning full SelfState in one query batch. Implement `GET /api/self/{id}/stream` as SSE emitting a TraceFrame per node."

> **Lane W:** "Replace fixtures with real fetches. Wire the interview card to `/api/self/interview/*` — real multi-step round trips, not a big paste. On the last step, redirect to `/today` and open the SSE stream."

**H8 acceptance — the milestone that matters:** someone who hasn't seen the code answers the interview in a browser and lands on a real self-model in under 30 seconds. **If this isn't true at H8, cut scope, don't push on.**

---

## PHASE 3 — H8→H12 · Candidates, scoring, the counterfactual

> **Lane A:** "Read CLAUDE.md §6a (source), §4 (trust_weight), §7. Implement `integrations/youtube.py` (search+videos, key rotation on 403), `integrations/rss.py` (feedparser, including IABTM's own feed if one exists), `integrations/grounding.py` (Gemini + google_search tool, real URLs from groundingMetadata only), `integrations/verify.py` (async HEAD, 5s timeout). Create `config/sources.json` — the trust-tier registry, credibility weights per source. Then `agents/scout.py` (theme → candidate pool from all three sources, concurrent via `asyncio.gather`, semaphore 8) and `agents/appraiser.py` (candidate → structured metadata + embedding via Gemini's embedding endpoint, batched, flash-lite). Cache everything keyed by normalized query."

> **Lane B:** "Read CLAUDE.md §4. Implement `engine/score.py` exactly as spec'd — `growth_score` with `trust_weight`, and `engagement_score` as the adversary. Pure Python, zero LLM, zero I/O beyond reading `config/sources.json`. Unit tests: growth_score penalizes what engagement_score rewards; it can go negative; trust_weight scales correctly. Then `agents/curator.py` (pure Python): assemble the bounded daily set, and for each item compute what the top engagement-scored candidate would have been — that's the counterfactual pair."

**H12 acceptance:** open `/today` → real verified candidates with real score breakdowns → every card flips to a real counterfactual, not a mock.

---

## PHASE 4 — H12→H16 · The closed loop (this is the whole project)

> **Lane B:** "Read CLAUDE.md §4, §5. Implement `engine/self_model.py` (per-theme depth, momentum, saturation — Beta-Bernoulli, 21-day decay), `engine/drift.py`, `engine/events.py` (SATURATED/DRIFT_DETECTED/STALLED/BREAKTHROUGH/BUDGET_EXCEEDED). Every trigger evaluation writes an `events` row."

> **Lane A:** "Implement `agents/reflector.py` (one-tap check-in → signal → self_model update) and `agents/coach.py` (state → nudge/do_block/drift_proposal/calibration, human-written copy, per the escalation ladder). Wire `POST /api/signal` and `POST /api/interventions/{id}/resolve`."

> **Lane B:** "Implement `engine/scheduler.py`: APScheduler every 60s real-time on `clock.now()` — decay, recompute risk-like state, evaluate triggers, fire interventions. `integrations/email.py` via Resend for nudge-tier only."

> **Lane W:** "Wire the shared card component to real check-ins and interventions. A `SATURATED` event must visibly stop the feed and show the Do Block (§2 Moat 2) — no new candidates until acted on. A `drift_proposal` must be a real approve/reject card that re-curates the feed on accept."

**H16 acceptance — the demo's spine:** consume several items on one theme with no action → feed stops, Do Block appears, unprompted. That single moment, working live, is the project.

---

## 🔒 H16 — FEATURE FREEZE

Lead calls it. Anything not working now gets **cut, not fixed** — see cut-line below.

---

## PHASE 5 — H16→H19 · Demo infrastructure + asset batch

> **Lane B:** "Implement `POST /api/demo/advance` (shifts clock, runs a scheduler tick synchronously, returns every event/intervention produced), `POST /api/demo/reset`, `POST /api/demo/seed {scenario}`."

> **Lane L:** "Write `seed/demo_user.py` — a user three weeks into a real aspiration with realistic history: several decisions with counterfactuals, one saturated theme close to triggering a Do Block, one drift signal building. Never demo empty."

> **Separate Claude Code session, Higgsfield MCP connected (not the main session):** run the asset-generation prompt from CLAUDE.md §6 — hero video, brand marks, per-theme cover art, and the "Becoming" reveal for the 4-5 seed scenarios you're already pre-warming YouTube for. Save to `web/public/assets/`. Disconnect the MCP from that session afterward; don't reconnect it in the main build session.

Also this phase: loading/empty/error states. Pre-warm YouTube+RSS cache for the same 4-5 demo goals the Higgsfield batch covers — one list, not two.

---

## PHASE 6 — H19→H21 · Deploy and triage

Deploy web to Vercel, api to Railway. Verify SSE survives the proxy — if not, demo from localhost. Fix only bugs on the demo path (§11 of CLAUDE.md). Everything else is a roadmap slide, not a bug.

---

## PHASE 7 — H21→H23 · Rehearse

- Run the full demo script (CLAUDE.md §11) five times, timed.
- **Record a complete successful run as backup video.**
- **Validate the depth/mastery estimator on synthetic users (~30 lines, 20 min).** Simulate 200 users with known true per-theme depth, generate signal sequences, run through `engine/self_model.py`, plot estimated vs. true depth as n grows. Same sanity check pyBKT runs on itself. Convergence plot goes on the eval slide.
- **Do NOT attempt a real knowledge-tracing benchmark** (ASSIST09/17, EdNet) — no taxonomy mapping exists for LLM-generated themes. Roadmap slide line instead: "next step is validation against standard benchmarks." Reads as rigour, not a gap.
- Run the AIA-PAL 8-criterion evaluation against your own system (CLAUDE.md §12) — especially your response time vs. their reported 90–148s. Put it on a slide.
- Drill Q&A from CLAUDE.md §12.

---

## H23→H24 — Slides, final commit, sleep in shifts

---

## Cut-line (exact order, apply at H16 if behind)

1. Higgsfield asset batch → fall back to static placeholder images, keep the Becoming card structure
2. Landing-page GSAP pass (Lenis + ScrollTrigger) → skip, ship the plain landing page
3. Growth Hive (§2.4) → skip entirely, use the Q&A fallback line
4. Calibration asks (§5a #3) → keep only the onboarding interview + one-tap check-ins
5. RSS source → YouTube + grounding only
6. Email delivery → in-app intervention only

**Never cut: the counterfactual flip, the refusal (Do Block), or the demo console.** Those three are the project.

## Three ways this dies, and the guard for each

| Risk | Guard |
|---|---|
| YouTube quota exhausted mid-demo | 3 rotating keys, aggressive caching, grounding-only fallback, pre-warmed demo goals |
| H8 slips | Hard stop, cut scope immediately — don't push through |
| Two Claude Code sessions collide in one directory | One session per lane (§13 of CLAUDE.md), never two in `api/agents/` or `api/engine/` at once |
