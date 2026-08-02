# PRAXIS — Agentic Human Potential Curator

**PRAXIS** is an agentic AI curation engine designed to replace addictive, attention-optimizing algorithms with goal-oriented human potential optimization. Built for the HBTM Hackathon Round 2.

> *"Today's algorithms optimize for attention. Praxis optimizes for human potential."*

**Stack:** Next.js (App Router) · FastAPI · LangGraph · Gemini + Ollama (`llama3.1:8b`) fallback · SQLite (dev) / Postgres (prod)

---
<img width="1089" height="1585" alt="Screenshot_2-8-2026_5526_localhost" src="https://github.com/user-attachments/assets/68d3fdbb-1157-422a-940d-9f28bc122863" />



## 1. The Core Architecture: Dual-Vector Identity Engine

To continuously curate the most relevant resources at the right time in a user's journey, Praxis models and tracks identity using a mathematical **Dual-Vector** model:

$$\vec{V}_{\text{current}} \quad \text{vs} \quad \vec{V}_{\text{target}}$$

- $\vec{V}_{\text{current}}$ represents the user's present skill set, revealed habits, and current level of domain understanding.
- $\vec{V}_{\text{target}}$ represents the user's aspirational self-model (who they are trying to become), extracted during onboarding.
- $\vec{V}_{\delta} = \vec{V}_{\text{target}} - \vec{V}_{\text{current}}$ defines the growth trajectory. Praxis curates candidate media strictly to close this gap.

### Interactive 3D Vector Space (Three.js)
Praxis includes an interactive **3D Vector Space** visualization on the **Self Twin** dashboard. Rendered dynamically via Three.js, it translates this linear algebra into a visual solar system of growth:
- **Blue Center Sphere**: Current Vector ($\vec{V}_{\text{current}}$)
- **Gold Target Sphere**: Target Vector ($\vec{V}_{\text{target}}$)
- **Dashed Laser Line**: Trajectory Delta ($\vec{V}_{\delta}$)
- **Orbital Satellites**: Learning themes (e.g. Systems Design, Public Speaking) revolving around the delta.
  - **Orbit speed** is driven by theme *momentum* (rate of logging actions).
  - **Orbit size/glow** is driven by theme *depth* (Beta-Bernoulli tracing).
  - **Orbital color** turns warning orange/red when theme *saturation* builds up.

---

## 2. The Three Core Moats

### Moat 1: The Counterfactual Feed
Every card in the daily recommendation feed can be flipped to show a side-by-side comparison of **What Praxis Chose** (optimized for growth) vs. **What Attention-CTR Would Pick** (the clickbait alternative) and why we skipped it.
- **Growth Curation**: Alignment, readiness, actionability, and novelty metrics.
- **Engagement Proxy**: View counts, shortness, clickbait titles, and recency bias.

### Moat 2: The Refusal (Do Block)
If a user is consuming heavily in a theme but putting none of it into practice, their saturation metric exceeds the threshold ($S \ge 0.85$). Praxis locks the feed for that theme and issues a **Do Block** refusal:
> *"You've saved 4 things about writing this week and published nothing. No new links today. Open a doc, set 25 minutes, write 300 words. I'll bring you the next piece after that."*

### Moat 3: Identity Drift (Human-in-the-Loop)
If a user skips stated goal items (e.g. Public Speaking) and heavily consumes other domains (e.g. Systems Design), Praxis detects the rolling divergence ($D \ge 0.35$). Instead of treating it as churn, it proposes an active update:
> *"Six weeks ago you said 'become a better public speaker.' Since then you've engaged 4x more with systems-design material. Has your aspiration changed?"*

---

## 3. Learning-Science Grounding

- **Zone of Proximal Development (ZPD)**: Content depth ratings (1-3) are mapped against the user's current estimated depth in a continuous ZPD fit score to serve items that are neither too trivial nor overwhelmingly complex.
- **Beta-Bernoulli Knowledge Tracing (BKT)**: The user level is modeled dynamically using Beta distributions $B(\alpha, \beta)$ starting from a prior of $B(1.0, 1.0)$. 
  - Completed items and reflection check-ins (e.g., "Too Easy", "Just Right", "Too Hard") update parameters.
  - Inactivity decays parameters exponentially back to the prior (21-day half-life).

---

## 4. Tech Stack

- **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS, Three.js, Lucide Icons, Framer Motion.
- **Backend**: FastAPI Async, SQLAlchemy 2.0 Async, SQLite (local dev) / Postgres (production, e.g. Supabase or Neon).
- **Agents Framework**: LangGraph state machine orchestrating 8 specialized nodes:
  - `interviewer` & `intake` (onboarding)
  - `scout` (concurrent ingestion from YouTube API, RSS, and Gemini Search Grounding)
  - `appraiser` (metadata extraction & `text-embedding-004` generation)
  - `scorer` & `curator` (arithmetic scoring and counterfactual grouping)
  - `reflector` & `coach` (check-in processing and intervention updates)
- **LLM**: Gemini (`gemini-3.6-flash` / `gemini-3.5-flash-lite`) as primary, with a local **Ollama (`llama3.1:8b`)** fallback so onboarding still works offline or without API keys.
- **Virtual clock (`clock.py`)**: Enables manual offset advances (`/api/demo/advance`) to showcase saturation blocks and drift updates instantly.

---

## 5. Getting Started

### Backend Setup
1. Set up the Python virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r api/requirements.txt aiosqlite pytest
   ```
2. Copy `.env.example` to `.env` and fill in the keys you have. Leaving `DATABASE_URL` unset is fine for local dev — the backend falls back to a local SQLite file (`praxis.db`) automatically.
3. (Optional but recommended) Pull the local Ollama fallback model, used when Gemini is unreachable or unconfigured:
   ```bash
   ollama pull llama3.1:8b
   ```
4. Run FastAPI. **Port must be 8001** — the frontend's dev proxy (`web/next.config.ts`) forwards `/api/*` to `http://127.0.0.1:8001`, and env vars are only loaded via `--env-file`:
   ```bash
   uvicorn api.main:app --reload --port 8001 --env-file .env
   ```

### Frontend Setup
1. Install node dependencies:
   ```bash
   cd web
   npm install
   ```
2. Run development server:
   ```bash
   npm run dev
   ```
3. Open [http://localhost:3000](http://localhost:3000). Click **Advance 5 Days** in the sidebar to simulate saturation and test the refusal system.

> If you change the backend's port, update the `destination` in `web/next.config.ts`'s `rewrites()` to match — otherwise every `/api/*` call from the frontend will silently 404 against the Next.js dev server instead of reaching FastAPI.
