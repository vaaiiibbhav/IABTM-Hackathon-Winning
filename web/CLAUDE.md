@AGENTS.md
# PRAXIS — repo constitution (v2, re-spec'd for the curator problem statement)

> Read fully before writing any code. This is the contract.
> Team: Coffee to Code · HBTM Round 2, IIIT Pune · 24h build.

---

## 1. The problem, and our answer to it

> *"Today's algorithms optimize for attention. This challenge asks you to build one that optimizes for human potential."*

That sentence is the entire brief, and it is an **objective-function problem**, not a recommendation problem. A feed that optimizes `P(click)` and a feed that optimizes growth can surface the same item on the same day; what makes them different is what they maximize and what they refuse.

So we do not build a better recommender. We build a recommender **whose objective function is visible, inspectable, and explicitly not engagement** — and which is willing to serve you nothing.

**The thesis. Every design decision serves this sentence:**

> Praxis maintains a model of who you're trying to become, scores every candidate against that model instead of against your attention, and shows you the arithmetic.

**Name:** PRAXIS — the gap between knowing and doing. Even more apt here than before.

**Non-goals.** Auth. Payments. Mobile. Fine-tuning. A chat tab (see §10). Infinite scroll of any kind. If a task doesn't appear in the demo script (§11), it does not get built.

---

## 2. The moats (three core, one stretch — §2.4)

### Moat 1 — The Counterfactual Feed
Every curated item can be flipped to show what an engagement-optimized feed would have served instead, and why we didn't.

```
┌─ WHAT PRAXIS CHOSE ──────────┬─ WHAT ENGAGEMENT WOULD PICK ─┐
│ 22-min essay on deliberate   │ "10 PRODUCTIVITY HACKS 🔥"    │
│ practice                     │ 4.2M views · 8 min           │
│ alignment 0.91 · ready 0.84  │ predicted watch-time 0.94    │
│ actionable ✓ · novel ✓       │ alignment 0.21 · actionable ✗│
│                              │ you've seen 6 like it        │
└──────────────────────────────┴──────────────────────────────┘
```

This is the problem statement rendered as UI. It is unfakeable, it is instantly legible to a non-technical judge, and no other team will have it. **Build this first. It is the demo.**

Implementation is cheap: you already fetch a candidate pool. Score every candidate on *both* objectives — yours, and a crude engagement proxy (view count, recency, title-clickbait score, short duration). Show the top item under each. Same pool, two objectives, visibly different winners.

### Moat 2 — The refusal
The agent has a `SATURATED` state. When you have consumed a lot on a theme and acted on none of it, it stops serving content and issues a **Do Block** instead:

> *You've saved 7 things about writing this week and published nothing. No new links today. Open a doc, set 25 minutes, write 300 words. I'll bring you the next piece after that.*

A curator that closes itself is the single most memorable thing you can put in front of a judge on an anti-attention brief. Everyone else's demo ends with more content. Yours ends with the app telling you to leave.

### Moat 3 — Identity drift, honored not fought
The brief says *evolving* identity. Most systems treat drift as churn to be corrected. Praxis detects it and **proposes an identity update the human approves**:

> *Six weeks ago you said "become a better public speaker." Since then you've engaged 4× more with systems-design material and skipped 5 speaking items. Has your aspiration changed? [Update it] [No, hold me to it]*

Human-in-the-loop, cross-session memory, self-correction — three agentic-AI rubric boxes ticked by one interaction.

### Moat 4 — The Growth Hive (stretch, gated to H16 like §15)

Concept borrowed — not code, not copied, see §12a — from the private-silo / shared-hive / promotion pattern in the `memory-hive` project (persistent memory for coding-agent teams, MIT). Their pattern: each agent has a private silo, raw learnings get distilled, and a curator promotes verified lessons into shared knowledge. Applied to *people* instead of coding agents:

- **Your silo** is `self_model.py` — private, per-user, exactly as already spec'd.
- **The Hive** is a small aggregate table: when many users pursuing a similar theme act on the same item (not just consume it — `signals.kind = 'acted'`), that item earns a **promoted** flag for that theme.
- Promoted items get a small, transparent, opt-in bonus in `growth_score` (`+0.05 * promoted`) and a badge in the UI: *"12 people working on public speaking acted on this."* No individual signal is ever shown — only the aggregate count. This is the same raw→distilled→promoted pipeline memory-hive uses for lessons, applied to growth content instead of code learnings.
- **This is where IABTM's own experts and artists earn their place for free.** Their content is exactly what should surface as promoted — real practitioners whose material people act on, not just watch. Say this explicitly in the pitch: *the Hive is how IABTM's own curators become part of the algorithm, not a separate tab.*

Two lines, `engine/hive.py`:
```python
def promote(theme_id, candidate_id, min_actors=3):
    return count_distinct_actors(theme_id, candidate_id, kind="acted") >= min_actors

def hive_bonus(candidate, theme_id): return 0.05 if is_promoted(candidate, theme_id) else 0.0
```

**Gate: build only after §11's core loop is green and rehearsed.** It needs real aggregate signal to demo convincingly — seed 4–5 synthetic users per theme during `/api/demo/seed` so the promotion badge has something to show. If seeding it well eats more than 30 minutes, cut it and keep the line for Q&A instead: *"the architecture supports a promotion layer — same pattern as verified-lesson curation in agent-memory systems — we didn't have real aggregate data to demo it honestly in 24 hours."* That answer is a strength, not an apology.

---

## 3. Hard invariants

**I1 — All time flows through `api/clock.py`.** Never `datetime.now()` anywhere else. Every timestamp read/write uses `clock.now()` (real UTC + stored offset). The time-travel demo depends on it entirely.

**I2 — `api/schemas.py` and `web/lib/types.ts` are the contract.** Kept in sync by hand. Changes get a `CONTRACT:` commit and a message in team chat. Frontend builds against fixtures from hour 1.

**I3 — The LLM never owns state or scoring.** LLMs extract structure and write copy. **The scoring function in `engine/score.py` is pure Python with zero LLM calls.** This is non-negotiable: the moment a judge hears "the LLM decides what's relevant," the objective-function claim collapses. Scores must be arithmetic you can print.

**I4 — Every served item writes a `decision` row** with its full score breakdown and the counterfactual it beat. No item reaches the UI without a recorded reason.

**I5 — Every URL is HEAD-verified before it reaches the UI.** A dead link in front of a judge costs more than a missing feature.

**I6 — No infinite scroll, ever.** The feed is bounded — a small number of items per day, and it ends. The end of the feed is a design statement; make it visible.

**I7 — Latency is a feature.** First curation ≤ 20s with live streaming; every re-curation ≤ 4s. Parallelise with `asyncio.gather`.

---

## 4. The scoring function — the heart of the project

`api/engine/score.py`. Pure, deterministic, printable, unit-tested.

```python
def growth_score(item, self_model, history) -> tuple[float, dict]:
    alignment   = cosine_similarity(item.embedding, self_model.aspiration_embedding)  # 0..1, real
    readiness   = fit_to_level(item.depth, self_model.theme_depth)         # ZPD band
    actionability = item.has_concrete_practice                            # 0/0.5/1
    novelty     = 1 - overlap_with_recent(item, history)
    effort_fit  = fits_available_time(item.minutes, self_model.today_budget)
    trust_weight = source_credibility(item.source)                        # 0.5..1.2, see config/sources.json

    saturation_penalty = consumed_without_action(item.theme, history)     # 0..1

    score = trust_weight * (0.30*alignment + 0.20*readiness + 0.20*actionability
             + 0.15*novelty + 0.15*effort_fit) - 0.40*saturation_penalty
    return score, locals()   # breakdown is rendered in the UI

def engagement_score(item) -> float:      # the adversary, deliberately crude
    return (0.40*norm(item.view_count) + 0.25*clickbait(item.title)
            + 0.20*shortness(item.minutes) + 0.15*recency(item))
```

Two properties to defend on stage: `growth_score` **penalizes** what `engagement_score` rewards (view count, brevity, clickbait), and it can go **negative** — which is what triggers the refusal in §2.

**`trust_weight` — the one idea worth taking from `agentic-ai-curator`'s source registry, written fresh against our own config.** A flat JSON file, `config/sources.json`, mapping source → credibility multiplier — `1.2` for IABTM's own experts/artists/podcast, `1.0` for established creators, `0.8` for an unverified upload, `0.5` floor. This is what lets IABTM's own catalog earn top billing in the feed without hardcoding a special case for them — they're just the highest-trust source, transparently, in a file anyone can read.

Also in `engine/`:
- `self_model.py` — per-theme depth (Beta-Bernoulli over engagement + reflection signals, decaying over 21 days), momentum, saturation, drift score
- `drift.py` — rolling divergence between stated aspirations and revealed engagement; crosses threshold → `DRIFT_DETECTED`
- `events.py` — `SATURATED` · `DRIFT_DETECTED` · `STALLED` (3d inactive) · `BREAKTHROUGH` (acted 3× on a theme) · `BUDGET_EXCEEDED`
- `scheduler.py` — APScheduler, 60s ticks on `clock.now()`: decay → recompute → evaluate triggers → act

**Embeddings, not a vector database.** `item.embedding` and `self_model.aspiration_embedding` are single Gemini embedding calls (`gemini-embedding-001` or current equivalent — verify the exact model string in AI Studio tonight), stored as plain float arrays on the row. Candidate pools are a few dozen items per curation — comparing them is `numpy` dot products in a loop, not an ANN index. **No pgvector, no sqlite-vec, no vector DB of any kind.** This is arithmetic, not infrastructure, and it's what keeps I3 true.

---

## 5. Agent graph (LangGraph, deterministic edges — no LLM supervisor)

| Node | Job | Model |
|---|---|---|
| `interviewer` | drives the structured onboarding interview and any calibration ask — emits one question at a time, never free text; see §5a | flash-lite |
| `intake` | accumulated interview answers → `SelfSpec` (aspirations, themes, habits, constraints, time budget) | 3.6-flash |
| `scout` | theme → candidate pool from YouTube + RSS + grounded search | 3.6-flash + APIs |
| `appraiser` | candidate → structured metadata: themes, depth 1–3, minutes, has_practice, embedding | flash-lite, batched |
| `scorer` | **pure Python**, §4 | none |
| `curator` | assemble the bounded daily set + counterfactuals | none |
| `reflector` | one-tap post-item check-in → signal extraction → self-model update; see §5a | flash-lite |
| `coach` | state → nudge / Do Block / drift proposal / calibration ask, written for a human | flash-lite |

Entry points: `create_self` · `curate_today` · `log_signal` · `answer_check_in` · `tick`.

Every node streams a trace frame `{node, status, ms, summary}` over SSE. Judges watch this. It is a feature, not debug output.

### 5a. Active elicitation — the interaction model, not a chat box

The brief says the brief's own villain is passive consumption. Praxis doesn't infer who you are by watching silently — it asks, the way a mentor asks. **The hard rule: elicitation is always agent-initiated, always structured, and answerable in one tap.** No free-text chat surface anywhere in the product — that's what makes a judge think "this is ChatGPT with a dashboard," which is the exact comparison the whole pitch exists to defeat.

Three touchpoints, all rendered through the *same* `interventions` card component already in §8/§10 — no new UI subsystem:

1. **Onboarding is an interview, not a textarea.** 3–5 short questions, one at a time, mostly tap-chips (time budget, current level, what's blocked you before). One free-text field only for the aspiration itself. Feeds `intake` directly — far higher self-model fidelity than one messy paragraph.
2. **A one-tap check-in after every consumed item.** Not "type your thoughts" — a 2–3 option tap: *too easy / right / too hard*, or *did you act on this?* This is the ZPD readiness signal and the `reflector` input, made primary instead of incidental.
3. **Calibration asks, fired by `coach` whenever self-model confidence is low** (generalizes the existing drift-approval card). When the agent is uncertain rather than wrong, it asks instead of silently guessing. `interventions.type` gains one value: `calibration`.

Pitch line for stage: *we don't infer your identity from scroll time — we ask.*

---

## 6. Where Higgsfield goes — and where it must not

Higgsfield is cinematic video/image generation, ~45s per generation. **Use the official hosted MCP, not a community wrapper.** `https://mcp.higgsfield.ai/mcp` is Higgsfield's own OAuth-based server — you authenticate once in a browser, no API key ever touches your code or `.env`. Third-party repos like `geopopos/higgsfield_ai_mcp` require pip-installing an unfamiliar package and handling raw API credentials yourself — unnecessary risk when the official path is safer *and* less setup. Use the official one.

**Rule: never on the live demo path.** A 45-second blocking call on stage is a lost demo. Every Higgsfield asset in this project is generated *before* the demo, as a batch job, not at request time.

**Hard safety rail — do not generate a photorealistic likeness of the user.** No selfie-to-future-self, no face swap, no "here's what you'll look like." That's a real, identifiable person's image being AI-generated, which is a different and much riskier thing than a mood board — slow, hard to get right in 24h, and one bad frame from creepy instead of inspiring. Keep every generation **symbolic and aesthetic**, built from the aspiration's *themes*, never from a photo of the person.

**"Boosted by Higgsfield" = a full pre-generated visual layer, produced in one dedicated session tonight, referenced as static files everywhere else.** Checklist:

1. **Hero video + brand marks** — pitch open, landing background. Highest value, zero risk.
2. **"Becoming" reveal — the headline use, ties directly to IABTM's own tagline.** A short cinematic mood-piece per aspiration *theme* ("systems design mastery" → focus and craft, atmospheric — never the user's face). Revealed at the first milestone under **"become the self you imagine."**
3. **Per-theme cover art** — a consistent visual treatment for each theme card in the Self Twin grid, so the UI reads as art-directed rather than templated.
4. **Promoted-item badge art** (only if §2.4's Growth Hive ships) — visual distinction for items the Hive has promoted.
5. **Ambient background loop** — a short, subtle looping video for the landing page and/or `/twin` hero background, atmospheric not distracting. Same rule as everything else here: pre-generated, static file, zero live calls.

**All four are pre-generated for the demo's known seed scenarios** (the same 4–5 goals you're already pre-warming YouTube's cache for in BUILD_ORDER.md Phase 5 — extend that one pre-warm step to also cover Higgsfield art, don't build a second mechanism). If a judge types something genuinely novel, the Becoming card falls back to a themed static still — never a live 45s call, never a broken card.

**Context-budget note for the MCP setup:** Higgsfield's server exposes 30+ tools, one per model. Do not add it to your main coding session alongside chrome-devtools/shadcn/context7 — that's 30+ extra tool schemas competing for context on every turn of the actual build. Connect it in a **separate, short-lived Claude Code session dedicated to generating this asset batch**, save the outputs to `web/public/assets/`, then don't reconnect it for the rest of the build.

Do not put Higgsfield in the curation loop or the scoring path. It generates media; the brief asks you to curate the world's media, and I3 already forbids the LLM (or any generator) from touching the score.

---

## 7. Stack

Unchanged from v1 except where noted.

| Layer | Choice |
|---|---|
| Frontend | **Next.js (App Router) + React + TS + Tailwind + shadcn** — this is what's actually on disk; earlier drafts said Vite, corrected here to match reality |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2 async, `sse-starlette` |
| Agents | LangGraph, single framework |
| LLM | `gemini-3.6-flash` (intake, scout, coach) · `gemini-3.5-flash-lite` (appraiser, reflector) |
| Fallback | Ollama `llama3.1:8b`, same interface |
| DB | Postgres (Supabase). No vector store. |
| Sources | YouTube Data API v3 + RSS (`feedparser`, incl. IABTM's own blog/podcast if a feed exists — check tonight) + Gemini search grounding + HEAD verify |
| Scheduler | APScheduler in-process on `clock.now()` |
| Email | Resend |
| Video assets | Higgsfield, offline, pre-generated |

**Gemini 3.x gotcha:** `temperature`, `top_p`, `top_k` are deprecated — do not pass them. Use native structured output. Set thinking effort minimal on `appraiser` and `reflector` (they run in batches).

**YouTube quota is the top technical risk.** `search.list` = 100 units against 10,000/day. Provision **3 keys**, rotate on 403, cache by normalized query, degrade to grounding-only on exhaustion, and **pre-warm the cache for 4–5 aspirations a judge might type.**

---

## 8. Data model

```sql
users(id, name, email, timezone, created_at)
self_specs(id, user_id, raw_input, summary, daily_minutes, created_at)
aspirations(id, self_spec_id, text, status, created_at, retired_at)   -- status: active|drifting|retired
themes(id, self_spec_id, slug, name, alpha, beta, last_engaged_at, momentum, saturation)
candidates(id, theme_id, kind, title, url, provider, minutes, depth,
           has_practice, view_count, verified, appraised_at)
           -- kind: video | essay | book | tool | person | experience
decisions(id, user_id, candidate_id, served_at, growth_score,
          breakdown JSONB, counterfactual_id, counterfactual_score)
signals(id, user_id, candidate_id, kind, value, reflection_text, created_at)
          -- kind: opened | completed | saved | skipped | acted | reflected
interventions(id, user_id, type, tier, body, state JSONB, sent_at, resolved_at)
          -- type: nudge | do_block | drift_proposal | calibration | budget_stop
events(id, user_id, type, payload JSONB, created_at)
clock(id INT PRIMARY KEY DEFAULT 1, virtual_offset_seconds INT DEFAULT 0)
```

Timestamps are written by application code via `clock.now()` — **never** `DEFAULT now()` in SQL.

---

## 9. API

```
POST /api/self/interview/start                                → {question, step, of}
POST /api/self/interview/answer {step, answer}                 → {next_question?} | {user_id}  (last step)
GET  /api/self/{id}                                          → SelfState
GET  /api/self/{id}/stream      SSE trace + invalidations
GET  /api/feed/{user_id}                                     → today's bounded set + counterfactuals
POST /api/signal                {candidate_id, kind, reflection?} → {events[], model_delta}
GET  /api/decisions/{user_id}                                → decision log with breakdowns
POST /api/interventions/{id}/resolve  {accept: bool, answer?} → {result}   (handles nudge/do_block/drift/calibration)
POST /api/demo/advance          {days}   → {events[], interventions[], feed_changes[]}
POST /api/demo/reset · POST /api/demo/seed {scenario}
```

The interview is a handful of small round trips, not one big POST — each answer returns the next question or, on the last step, the created `user_id`. Every question is structured (options or a short scale) except the final free-text aspiration statement.

`SelfState` is one fat object: aspirations, themes with depth/momentum/saturation, today's budget, drift score, recent decisions. One fetch + one SSE subscription. Do not build fifteen chatty endpoints.

---

## 10. UI

Borrow the naming from the MentorPath mock — it's better than ours: **"AI Decision of the Day"**, **"Self Twin"**, and task kinds **Repair / Drill / Project / Check**. Borrow the four-tile layout too.

But **replace the four metrics.** "Burnout 34% / Focus 82%" cannot survive a technical judge asking where the number comes from, and "burnout" is a quasi-clinical claim you can't defend from click logs. Use instead, all computed in `engine/`: **Alignment · Momentum · Saturation · Drift** — each with its top driver in text underneath.

**One card component renders every elicitation moment** — onboarding interview steps, the post-item check-in, and every `interventions` type (nudge, do_block, drift_proposal, calibration). Same shape, same tap interaction, everywhere: a short prompt, 2–4 chip options, done. This is what makes the "agent keeps checking in" behaviour feel deliberate instead of like five different half-built features.

**Still cut the Mentor Chat tab — this is not a contradiction of §5a, it's the same rule.** §5a's interview/check-in/calibration cards are agent-initiated and tap-answered; a chat tab is user-initiated free text. The first is a mentor asking questions. The second is a search bar that makes a judge think "this is ChatGPT with a dashboard." Cut Analytics too; the dashboard is the analytics.

Three screens:
```
/today   bounded feed · each card flips to its counterfactual · the feed visibly ENDS
/twin    aspirations, theme depth grid, momentum, saturation, drift
/why     decision log — every item, its score breakdown, what it beat
```
Dark, dense, instrument-panel. One accent colour for "the agent acted." Framer Motion `layout` so re-curation visibly animates.

**§10a — `/twin` hero: true self / imagined self, in 3D (stretch, gated to H16, same discipline as §6/§2.4).** Two low-poly humanoid busts, distance between them driven directly by the existing `alignment` value from `self_model.py` — this is a new *rendering* of a number that already exists, not a new computation. As alignment rises, they move closer; as it falls, they drift apart.

Build constraints, all hard:
- **Source the model, never sculpt one tonight.** A free, pre-rigged low-poly bust (Sketchfab CC0/CC-BY — search "low poly human bust"), exported `.glb`, rendered with **react-three-fiber** (not vanilla Three.js — it integrates directly with the existing Vite+React stack).
- **Stylized only, never photorealistic** — same rule as Higgsfield's rail in §6. Low-poly reads as intentional and aspirational; a realistic bust reads as uncanny and is slower to get right.
- **No new `.env` entries.** The model is a static client-side asset. Zero API calls happen to render it.
- **Never on `/today` or `/why`.** Those screens need to stay fast and dense for the counterfactual flip and decision log to land — a 3D scene there works against the exact thing that has to land with a judge. This lives on `/twin` only, optionally as static (non-data-driven) brand art on the landing page.
- **WebGL fallback:** if `react-three-fiber`'s canvas fails to mount (weak GPU, driver issue on a venue laptop), fall back to a static rendered screenshot of the same asset. A blank canvas mid-demo is worse than a static image.

---

## 11. Demo script (7 min)

| Time | Beat |
|---|---|
| 0:00 | "My phone knows exactly what I'll watch. It has no idea who I'm trying to become." |
| 0:30 | **Judge answers a 4-question tap interview**, ending with their own aspiration in one line. Self-model + themes + today's feed streams in, trace panel firing. |
| 1:30 | **Flip a card.** Counterfactual side-by-side. *"Same candidate pool. Different objective function. Here's the arithmetic."* Say nothing for three seconds. |
| 2:30 | Consume one, log a reflection. Theme depth updates, tomorrow's feed re-curates live. |
| 3:30 | Advance 5 days with saves and no action → **SATURATED** → the Do Block. *"It just refused to give me content."* |
| 4:30 | Advance again → **drift detected** → identity-update proposal → human approves → feed re-curates around the new self. |
| 5:30 | `/why` — the decision log. *"Every item traces to arithmetic. Nothing here is vibes."* |
| 6:00 | Close: *"Everyone else built a better recommender. We built one that optimizes for a different thing — and shows you the difference."* |

---

## 12. Positioning

Cite **Tebourbi et al., Procedia CS 265 (2025)** (LangGraph/CrewAI adaptive learning; reports 90–148s agent latency), **OpenMAIC** (THU-MAIC, JCST 2026), and **`agentic-ai-curator`** (aylin-jarrahnezhad, CrewAI-based AI-news digest) as the reference architectures we visibly extend. All three are the closest published/public relatives; all three are missing the thing the brief actually asks for. AIA-PAL and OpenMAIC are session-scoped tutors with no cross-session model of the person. `agentic-ai-curator` is the closest architectural shape by far — fetch → normalize → dedupe → score → cluster → summarize maps almost directly onto our scout → appraiser → scorer → curator — but it scores content quality in the abstract (relevance, importance, novelty) with no model of a specific person at all, and its own README admits those scoring dimensions are unvalidated. **OpenMAIC is AGPL-3.0: read it, close the tab, write your own. `agentic-ai-curator` carries no visible license: same rule, harder edge — read its pipeline shape and its weighted trust-tier source registry idea, write our own scoring against our own schema, never fork its CrewAI codebase as the submission's foundation.** The one concrete thing worth taking: its `config/source_registry.json` pattern — per-source credibility weights — adapted into our own scoring so IABTM's own experts and artists can be weighted highest without hardcoding favoritism.

Learning-science grounding: Zuo et al. 2023 (scaffolding meta-analysis), Tabak & Reiser 2022 (scaffolding), Vygotsky's ZPD for the readiness band, Corbett & Anderson 1995 (BKT) for the depth estimator's lineage.

**Why not fitted BKT / pyBKT?** It fits parameters by EM over historical logs; every user here is cold-start on themes generated minutes ago. A Beta-Bernoulli posterior is correct under those conditions — it degrades gracefully at n=1 and reports its own confidence. Fitted models are the roadmap, not the demo.

**§12a — on the Growth Hive's origin (§2.4):** the raw→distilled→promoted pattern is conceptually adapted from `memory-hive` (TJCurnutte, MIT licensed). MIT permits copying, but **we didn't copy any code** — the domains are unrelated (coding-agent memory vs. human growth content) and the implementation is two functions written from scratch against our own schema. If asked, say exactly that: pattern borrowed, code original, license was never actually the constraint here since MIT allows reuse anyway — we just had nothing worth reusing across such different domains.

**Q&A to drill:** *how is this not a recommender · where do your numbers come from · what stops the LLM deciding relevance (nothing does — it never touches scoring) · how do you know the counterfactual is fair · cost at scale · who pays (B2B: platforms already lose money on completion rates; this is the retention layer).*

---

## 13. Working with Claude Code

One session per directory: `api/agents/` · `api/engine/`+`api/routes/` · `web/`. Never two sessions in one directory. Every function in `engine/` gets a unit test — they're pure, tests take two minutes, and they are the parts that must not be wrong on stage. Stuck 15 minutes → stub it, `# TODO(demo)`, move on. Commit every 30 minutes.

## 14. Cut-line (lead calls freeze at H16)

Drop in this order: email delivery → in-app only · drift detection · reflection prompts → implicit signals only · non-video sources → YouTube only.

**Never cut: the counterfactual flip, the refusal, or the demo console.** Those three are the project.