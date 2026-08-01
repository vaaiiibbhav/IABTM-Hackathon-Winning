// PRAXIS API contract — TypeScript mirror of api/schemas.py, field-for-field (I2).
// Any change here needs a matching CONTRACT: commit on the Python side.

export type AspirationStatus = "active" | "drifting" | "retired";
export type CandidateKind = "video" | "essay" | "book" | "tool" | "person" | "experience";
export type SignalKind = "opened" | "completed" | "saved" | "skipped" | "acted" | "reflected";
export type InterventionType = "nudge" | "do_block" | "drift_proposal" | "calibration" | "budget_stop";
export type EventType = "SATURATED" | "DRIFT_DETECTED" | "STALLED" | "BREAKTHROUGH" | "BUDGET_EXCEEDED";
export type TraceStatus = "started" | "ok" | "error";

// ---- entities (§8 data model) ----

export interface User {
  id: string;
  name: string;
  email: string;
  timezone: string;
  created_at: string; // ISO datetime
}

export interface SelfSpec {
  id: string;
  user_id: string;
  raw_input: string;
  summary: string;
  daily_minutes: number;
  created_at: string;
}

export interface Aspiration {
  id: string;
  self_spec_id: string;
  text: string;
  status: AspirationStatus;
  created_at: string;
  retired_at: string | null;
}

export interface Theme {
  id: string;
  self_spec_id: string;
  slug: string;
  name: string;
  alpha: number;
  beta: number;
  last_engaged_at: string | null;
  momentum: number;
  saturation: number;
  depth: number; // posterior mean alpha/(alpha+beta)
}

export interface Candidate {
  id: string;
  theme_id: string;
  kind: CandidateKind;
  title: string;
  url: string;
  provider: string;
  minutes: number;
  depth: number; // 1-3 content depth, unrelated to Theme.depth
  has_practice: boolean;
  view_count: number;
  verified: boolean;
  appraised_at: string | null;
}

// locals() from engine/score.py::growth_score (§4)
export interface ScoreBreakdown {
  alignment: number;
  readiness: number;
  actionability: number;
  novelty: number;
  effort_fit: number;
  trust_weight: number;
  saturation_penalty: number;
  score: number;
}

export interface Decision {
  id: string;
  user_id: string;
  candidate_id: string;
  served_at: string;
  growth_score: number;
  breakdown: ScoreBreakdown;
  counterfactual_id: string | null;
  counterfactual_score: number | null;
}

export interface Signal {
  id: string;
  user_id: string;
  candidate_id: string;
  kind: SignalKind;
  value: string | null;
  reflection_text: string | null;
  created_at: string;
}

export interface Intervention {
  id: string;
  user_id: string;
  type: InterventionType;
  tier: number;
  body: string;
  state: Record<string, unknown>;
  sent_at: string;
  resolved_at: string | null;
}

export interface Event {
  id: string;
  user_id: string;
  type: EventType;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface Clock {
  id: number;
  virtual_offset_seconds: number;
}

// ---- composite response shapes (§9 API) ----

// One served candidate plus what the engagement objective would have picked instead (Moat 1)
export interface FeedItem {
  candidate: Candidate;
  breakdown: ScoreBreakdown;
  counterfactual_candidate: Candidate | null;
  counterfactual_engagement_score: number | null;
}

export interface FeedResponse {
  user_id: string;
  date: string;
  items: FeedItem[];
  saturated: boolean;
}

// The one fat object §9 says to fetch — no chatty per-field endpoints
export interface SelfState {
  user_id: string;
  aspirations: Aspiration[];
  themes: Theme[];
  today_budget_minutes: number;
  drift_score: number;
  recent_decisions: Decision[];
}

// One SSE frame per agent-graph node (§5)
export interface TraceFrame {
  node: string;
  status: TraceStatus;
  ms: number;
  summary: string;
}

export interface InterviewQuestion {
  question: string;
  step: number;
  of: number;
  options: string[] | null; // null => free text (aspiration step only, §5a)
}

export interface InterviewAnswerRequest {
  step: number;
  answer: string;
}

export interface InterviewAnswerResponse {
  next_question: InterviewQuestion | null;
  user_id: string | null; // set on the final step
}

export interface SignalRequest {
  candidate_id: string;
  kind: SignalKind;
  reflection: string | null;
}

export interface SignalResponse {
  events: Event[];
  model_delta: Record<string, unknown>;
}

export interface InterventionResolveRequest {
  accept: boolean;
  answer: string | null;
}

export interface InterventionResolveResponse {
  result: Record<string, unknown>;
}

export interface DemoAdvanceRequest {
  days: number;
}

export interface DemoAdvanceResponse {
  events: Event[];
  interventions: Intervention[];
  feed_changes: FeedItem[];
}

export interface DemoSeedRequest {
  scenario: string;
}
