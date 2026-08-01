// Small display helpers shared across /today and /why — pure formatting,
// no logic that belongs in engine/score.py (I3: scoring stays server-side).

export function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function views(count: number): string {
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M views`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K views`;
  return `${count} views`;
}

export function signed(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}
