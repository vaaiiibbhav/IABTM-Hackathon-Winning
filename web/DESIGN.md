# PRAXIS — DESIGN.md

> Instrument-panel UI for a growth curator. Adapted from [Raycast](https://raycast.com) dark-canvas patterns via [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — surface ladder, hairline borders, no drop shadows — merged with PRAXIS warm-dark tokens and a single reserved **agent amber** accent.

## Philosophy

- **Dark only.** Product ships with `className="dark"` on `<html>`. No light-mode toggle in the demo.
- **Density over decoration.** Every number has a driver underneath it. Cards are tight (16–20px padding), not marketing-hero spacious.
- **One accent color.** `--agent` (warm amber/gold) fires only when the agent acted: growth scores, counterfactual flip, resolved elicitations, intervention CTAs. Never use it for generic highlights.
- **Elevation = surface ladder, not shadows.** `background` → `card` → `secondary` → hairline `border`. No box-shadow on cards.
- **The feed ends.** `/today` has a visible terminus — that boundary is part of the design.

## Colors (CSS variables in `app/globals.css`)

| Token | Role |
|-------|------|
| `--background` | Page canvas — warm near-black (`oklch(0.16 0.006 75)`) |
| `--card` | Elevated panel — one step lighter |
| `--secondary` | In-card wells, chip backgrounds |
| `--border` | Hairline dividers — `oklch(1 0 0 / 10%)` |
| `--foreground` | Primary text |
| `--muted-foreground` | Labels, metadata, drivers |
| `--agent` | **Reserved** — agent-acted moments only |
| `--agent-foreground` | Text on agent-filled buttons |

## Typography

- **Sans:** Geist (via `next/font`) — UI copy, headings
- **Mono:** Geist Mono — scores, percentages, breakdown arithmetic
- **Label caps:** `text-[0.7rem] font-medium tracking-[0.08em] uppercase text-muted-foreground` — section headers, field names
- **Hero / page title:** `text-2xl font-semibold` (pages), `text-3xl–4xl` (landing only)

## Radius & spacing

- Cards: `rounded-lg` (10px) — not pill, not sharp
- Chips / elicitation options: `rounded-full`
- Page gutter: `px-6 py-10`, max-width `max-w-2xl` (feed) / `max-w-3xl` (twin, why)
- Card gap: `gap-3` or `gap-4`

## Components

### `panel`
Standard elevated surface: `rounded-lg border border-border bg-card`. Use for cards, elicitation, metric tiles.

### `FeedCard` — Moat 1
- Front: growth score in `--agent`, flip CTA with agent border tint
- Back: two-column grid — "What Praxis chose" (agent border) vs "What engagement would pick" (neutral)
- **Flip animation:** GSAP `rotateY` 3D flip — not opacity crossfade. Agent accent pulses on reveal.

### `ElicitationCard`
One component for interview, check-in, intervention. Chip options; resolved state shows agent pill with checkmark.

### `ScoreBreakdownGrid`
7 fields + final score in mono. Saturation penalty prefixed with `-`. Score row uses `--agent`.

### Nav
Sticky, `backdrop-blur`, hairline bottom border. Wordmark `PRAXIS` tracked uppercase. Active route: `bg-secondary`.

## Motion

| Moment | Library | Rule |
|--------|---------|------|
| Counterfactual flip | **GSAP** | 3D flip, ~0.55s, `power2.inOut` |
| Feed re-curation / layout shift | **Framer Motion** | `layout` on list items |
| Elicitation resolve | Framer | subtle `layout` on card |

Respect `prefers-reduced-motion`: skip GSAP flip rotation, instant swap.

## Do / Don't

**Do**
- Show score breakdown arithmetic on every served item
- Keep counterfactual side-by-side legible at `sm:` breakpoint
- End `/today` with the "That's it for today" terminator

**Don't**
- Use `--agent` for nav links, generic buttons, or decorative gradients
- Add infinite scroll or "load more"
- Add a chat textarea — elicitation is tap-only (except aspiration free-text step)

## Attribution

Visual patterns informed by Raycast's dark instrument-panel system ([awesome-design-md/design-md/raycast](https://github.com/VoltAgent/awesome-design-md)). PRAXIS tokens, copy, and component structure are original.
