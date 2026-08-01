# PRAXIS — build order

Read `CLAUDE.md` first. Each phase has paste-ready Claude Code prompts and a hard acceptance test. **Do not start a phase until the previous phase's acceptance test passes.**

Lanes: **A** = agents (`api/agents/`) · **B** = backend (`api/engine/`, `api/routes/`, `api/models.py`) · **W** = web (`web/`) · **L** = lead (demo, pitch, scope)

---

## PHASE −1 — TONIGHT, before you sleep (~90 min)

This is the highest-leverage 90 minutes of the whole hackathon. Do not skip it to "save energy." Every item here is something that fails badly over venue wifi at 11am.

- [ ] **3 × Gemini API keys** (three team Google accounts). Test one real call with `gemini-3.6-flash` and structured output. Confirm the model ID resolves on your key.
- [ ] **3 × YouTube Data API v3 keys.** Enable the API in each GCP project. Test one `search.list`.
- [ ] **Supabase project** created, Postgres connection string in hand, `?sslmode=require` tested from a laptop.
- [ ] **Resend account**, API key, send one test email to a team phone. Use `onboarding@resend.dev` as sender — do not burn time on domain verification.
- [ ] **Scaffold and push the repo now**: `create-next-app` (TS, Tailwind, App Router) + `shadcn init` + FastAPI skeleton + `uv sync` / `npm install` committed. Push `CLAUDE.md` and this file to the repo root. **Never run a cold `npm install` on venue wifi.**
- [ ] `ollama pull llama3.1:8b` on one laptop.
- [ ] Everyone clones and runs the scaffold successfully **before leaving home**.
- [ ] Write `.env.example` with every key name. Share real values in a private channel.

---

## PHASE 0 — H0→H1 · Contract lock (all four, same table, laptops half-shut)

Nobody writes feature code this hour. This hour is why you won't be in integration hell at hour 18.

**Together, out loud, agree and write down:**
1. The exact `GoalState` shape.
2. The nine event types.
3. The `PlanDiff` shape.
4. Who owns which directory for the next 24 hours.

> **Claude Code prompt (run once, lead's machine):**
> "Read CLAUDE.md. Create `api/schemas.py` with Pydantic v2 models for GoalSpec, Skill, SkillEdge, Milestone, Task, Resource, QuizItem, QuizResult, Event, PlanDiff, RiskState, TraceFrame, and GoalState. Then create `web/lib/types.ts` with TypeScript interfaces that mirror them exactly, field for field. Then create `web/lib/fixtures.ts` exporting a realistic complete GoalState for an 'AWS Solutions Architect in 10 weeks' learner with 6 skills, 3 milestones, 14 tasks, 4 plan diffs, and mid-range mastery values. Do not write any other code."

**Acceptance:** `web/lib/fixtures.ts` imports cleanly and the frontend lane can start immediately.

---

## PHASE 1 — H1→H4 · Three lanes in parallel, all on mocks

### Lane B — data layer
> "Read CLAUDE.md §2 and §7. Create `api/clock.py` exposing `now()` (real UTC + offset read from the clock table, cached 5s), `advance(days)`, and `reset()`. Then `api/models.py` with SQLAlchemy 2 async models for the full §7 schema, and `api/db.py` with session management. Write an Alembic migration. **Critical: no model may use `server_default=func.now()`; all timestamps are set by application code via `clock.now()`.** Add a unit test proving `advance(4)` moves `now()` forward exactly four days."

Then routes returning fixture data so the frontend can point at a real server by H2.

### Lane W — the whole UI against fixtures
> "Read CLAUDE.md §10. Build the `/g/[goalId]` dashboard using only `web/lib/fixtures.ts` — no network calls. Components: PlanBoard (milestones with nested task cards showing kind icon, est_minutes, status, and a difficulty dial rendering p_success 0–1), MasteryHeatmap (skill grid, colour = mastery, opacity = confidence), RiskGauge (score + top 2 drivers as text), DiffTimeline (reverse-chron, each entry showing trigger, reasoning, and added/removed/moved counts), AgentTrace (collapsible bottom drawer). Dark instrument-panel aesthetic, one accent colour. Use Framer Motion `layout` on task cards so future insertions animate. Do not build a settings page, a nav bar, or a landing page."

### Lane A — first three agents, CLI only
> "Read CLAUDE.md §3 and §4. Create `api/agents/llm.py`: a thin Gemini client using `gemini-3.6-flash` and `gemini-3.5-flash-lite`, with native structured output against Pydantic schemas, one retry on validation failure, and an Ollama `llama3.1:8b` fallback behind the same interface. **Do not pass temperature, top_p, or top_k — they are deprecated on Gemini 3.x.** Then `intake.py` (messy text → GoalSpec), `architect.py` (GoalSpec → skills + prerequisite edges + criticality, must produce a valid DAG — reject and retry if cyclic), and `planner.py` (skills + hours_per_week + deadline → milestones + dated tasks, respecting prerequisite order and never exceeding hours_per_week in any week). Add a `python -m api.agents.cli 'some goal'` entrypoint that prints the result as JSON. No FastAPI, no database."

**H4 acceptance:** Lane A prints a valid plan for a goal nobody hardcoded. Lane W renders a full dashboard from fixtures. Lane B serves fixture-shaped JSON over HTTP.

---

## PHASE 2 — H4→H8 · First real end-to-end

> **Lane A+B together:** "Wire `api/agents/graph.py` as a LangGraph with the three entry points in CLAUDE.md §4. Implement `POST /api/goals` running intake → architect → planner, persisting to Postgres. Implement `GET /api/goals/{id}` returning the full GoalState in one query batch. Implement `GET /api/goals/{id}/stream` as SSE emitting a TraceFrame per node with node name, status, elapsed ms, and a one-line summary."

> **Lane W:** "Replace fixtures with real fetches. Build `/` — a single large textarea, three example-goal chips, and a submit that opens the SSE stream and renders trace frames live while the plan generates."

**H8 acceptance — the milestone that matters:** someone who has not seen the code types a goal into a browser and gets a real skill graph and plan on screen in under 30 seconds. **If this is not true at H8, cut scope immediately, do not push on.**

---

## PHASE 3 — H8→H12 · Resources, quizzes, mastery

> **Lane A:** "Read CLAUDE.md §6. Implement `integrations/youtube.py` (search.list + videos.list, key rotation across 3 keys on 403, best-fit by duration vs task.est_minutes), `integrations/grounding.py` (Gemini with google_search tool, extracting real URLs from groundingMetadata — never from model memory), and `integrations/verify.py` (async HEAD, 5s timeout, follow redirects). Then `agents/curator.py` running all tasks concurrently via `asyncio.gather` with a semaphore of 8. Cache every result in the resources table keyed by normalized query. On quota exhaustion across all keys, degrade to grounding-only and log the path used."

> **Lane A:** "Implement `agents/assessor.py`: given a skill, generate 5 MCQ items tagged with that skill_id and difficulty 1–3 using flash-lite; and a grade function returning per-item correctness."

> **Lane B:** "Read CLAUDE.md §5. Implement `engine/mastery.py` and `engine/zpd.py` exactly as specified, as pure functions with no I/O. Write unit tests: mastery rises with correct answers, confidence rises with n, decay pulls toward the prior after 21 days, and next_task picks the task closest to 0.78 predicted success. Then wire `POST /api/tasks/{id}/quiz` to grade, update alpha/beta, and return mastery_delta per skill."

**H12 acceptance:** open goal → real verified YouTube links on task cards → take a quiz → mastery heatmap visibly changes.

---

## PHASE 4 — H12→H16 · The closed loop (this is the whole project)

> **Lane B:** "Read CLAUDE.md §5. Implement `engine/events.py` with the five trigger rules and `engine/risk.py` with the weighted score returning top 2 drivers. Every trigger evaluation writes an events row."

> **Lane A:** "Implement `agents/replanner.py`. Input: a triggering event plus current GoalState. Output: a validated PlanDiff — added tasks, removed tasks, moved dates, plus a one-paragraph `reasoning` written for the learner, not the developer. **Python must validate before persisting**: no task before its prerequisites, no week over hours_per_week, no removal of a task other tasks depend on. Invalid proposals retry once then fall back to the deterministic rule 'insert one remedial task, push milestone by 2 days'. Every accepted diff writes a plan_diffs row."

> **Lane B:** "Implement `engine/scheduler.py`: APScheduler every 60s real-time, using `clock.now()`. Each tick applies mastery decay, recomputes risk, evaluates triggers, and fires nudges. Implement `agents/coach.py` producing tier, channel and copy per the escalation ladder, and `integrations/email.py` sending via Resend. Tier 4 (risk > 0.85) must not send a nudge — it creates a pending scope-renegotiation proposal that `POST /api/goals/{id}/renegotiate` accepts or rejects."

> **Lane W:** "Wire DiffTimeline to `/diffs` and make new entries animate in. Wire RiskGauge to `/risk`. Add the scope-renegotiation approval card."

**H16 acceptance — the demo's spine:** fail a quiz in the browser → remedial tasks animate into the plan → milestone shifts → a new diff entry appears with human-readable reasoning. This works or you have no project.

---

## 🔒 H16 — FEATURE FREEZE

Lead calls it. Anything not working now gets **cut, not fixed**. Apply the cut-line in CLAUDE.md §14.

---

## PHASE 5 — H16→H19 · Demo infrastructure

> **Lane B:** "Implement `POST /api/demo/advance` (shifts the clock, runs a scheduler tick synchronously, returns every event, nudge and diff produced), `POST /api/demo/reset`, and `POST /api/demo/seed` for named scenarios."

> **Lane W:** "Build `/demo`: advance clock by 1/3/7 days, reset, seed scenario, force a specific event. Keyboard shortcuts so the presenter never hunts for a button on stage."

> **Lane L:** "Write `seed/demo_learner.py` creating a learner three weeks into an AWS SAA goal with realistic history — 60% completion, a 5-day streak, one previously failed quiz, two existing plan diffs, mid-range mastery with two weak skills. The dashboard must never be demoed empty."

Also this phase: loading states, empty states, error toasts. **Pre-warm the YouTube cache** for 4–5 goals a judge might plausibly type.

---

## PHASE 6 — H19→H21 · Deploy and triage

Deploy web to Vercel, api to Railway. Verify SSE survives the proxy — **if it doesn't, demo from localhost and stop fighting it.** Fix only bugs on the §11 demo path. Every other bug is now a known limitation you mention proudly in the roadmap slide.

---

## PHASE 7 — H21→H23 · Rehearse

- Run the full 7-minute script **five times**, timed. Rotate who presents until two people can do it.
- **Record a complete successful run as video.** Non-negotiable. This is your insurance against the venue's wifi.
- Screenshot every key state as slide backup.
- Run the AIA-PAL 8-criterion evaluation (CLAUDE.md §12) against your own system and put the numbers on a slide — especially your response times against their 90–148s. Almost no hackathon team shows an evaluation table. This one slide separates you from the field.
- **Validate the mastery estimator on synthetic learners (~30 lines, 20 minutes — do this before building the eval slide).** Simulate 200 learners with known true per-skill mastery, generate response sequences from it, run them through `engine/mastery.py`, and plot estimated vs. true mastery as n grows. This is the same sanity check the pyBKT paper runs. It turns "we built a Bayesian mastery model" into "here is proof it converges," and it costs almost nothing. The convergence plot goes on the eval slide.
- **Do NOT attempt a real benchmark run** (ASSIST09 / ASSIST17 / EdNet) during the hackathon. Those datasets assume a fixed, expert-authored concept taxonomy; your skills are LLM-generated per goal, so there is no mapping — and a rushed comparison you lose to published BKT numbers is worse than no comparison at all. Put it on the roadmap slide instead: *"next step is validation against the standard knowledge-tracing benchmarks."* That reads as rigour, not as a gap.
- Drill Q&A: *how is this different from ChatGPT plus a to-do list · how do you know mastery is real · what stops the LLM hallucinating a bad plan · cost at scale · who pays.*

---

## H23→H24 — Slides, final commit, sleep in shifts

---

## Three ways this dies, and the guard for each

| Failure | Guard |
|---|---|
| YouTube quota gone by hour 20 | 3 rotating keys, aggressive cache, grounding-only fallback, pre-warmed demo goals |
| H8 end-to-end slips | Hard stop and cut scope. Do not "push through" — that is how teams arrive at hour 22 with nothing demoable |
| Everyone builds, nobody rehearses | Lead owns the clock and is not on a build lane after H16 |
