# TASK SPECIFICATION: Aspirant Engine Architectural Overhaul

You are acting as a Principal AI Systems Architect. Your task is to refactor and transform this repository into the **Aspirant Engine**—a local-first, agentic curation platform designed to replace addictive, attention-optimizing algorithms with goal-oriented human potential optimization.

---

## 1. Core Mission & Philosophy
Traditional algorithms optimize for **Click-Through Rate (CTR)** and **dopaminergic retention**. The **Aspirant Engine** replaces this paradigm with a **Dual-Vector Identity Engine** and a **Human Potential Scoring System**.

### The "Better Than Me" Dual-Vector Concept
- $\vec{V}_{\text{current}}$: Captures the user's present skill set, established habits, and current cognitive state.
- $\vec{V}_{\text{target}}$: Captures the user's aspirational identity, target skills, and long-term values.
- $\vec{V}_{\text{delta}} = \vec{V}_{\text{target}} - \vec{V}_{\text{current}}$: Represents the growth trajectory. Content is curated strictly to bridge this gap.

---

## 2. Mandatory Directory Restructuring
Purge all existing UI files, web interface wrappers, and generic scraping boilerplate. Re-organize the codebase into the following clean modular architecture:

```text
aspirant-engine/
├── core/
│   ├── identity/
│   │   ├── __init__.py
│   │   ├── dynamic_profile.py      # Dual-vector (Current vs Target) state models
│   │   └── delta_analyzer.py       # Trajectory computation and skill gap extraction
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── potential_scorer.py     # Mathematical scoring against goal vectors
│   │   └── anti_sensationalism.py  # Clickbait & rage-bait filtering mechanics
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ingester.py             # Multi-source ingestion (RSS, Web, ArXiv, Podcasts)
│   │   ├── evaluator.py            # High-signal filtering & vector alignment
│   │   └── synthesizer.py          # Digest synthesis & actionable insight extraction
│   │
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── reflection_agent.py     # "Better Than Me" self-assessment prompts
│   │   └── habit_bridge.py         # Converts consumed content into micro-habits
│   │
│   └── pipeline.py                 # Core multi-agent orchestration workflow
│
├── config/
│   └── settings.yaml               # Engine hyperparameters & scoring weights
├── data/                           # Local persistence for state vectors
├── main.py                         # Clean CLI entry point
└── README.md                       # Architectural documentation