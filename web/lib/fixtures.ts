// Fixture data for Lane W (BUILD_ORDER Phase 1) — build the whole /today, /twin,
// /why UI against this before any network call exists. Shapes match lib/types.ts.
//
// Scenario: a learner whose stated aspiration is public speaking but whose revealed
// engagement has drifted toward systems design (CLAUDE.md Moat 3), and whose top
// feed card is the Moat 1 counterfactual worked example (deliberate-practice essay
// vs. a clickbait productivity video).

import type {
  Aspiration,
  Candidate,
  Decision,
  FeedItem,
  FeedResponse,
  SelfState,
  Theme,
} from "./types";

const NOW = "2026-08-01T09:00:00Z";

export const fixtureAspirations: Aspiration[] = [
  {
    id: "asp_1",
    self_spec_id: "ss_demo",
    text: "become a confident public speaker",
    status: "drifting",
    created_at: "2026-06-20T09:00:00Z",
    retired_at: null,
  },
];

export const fixtureThemes: Theme[] = [
  {
    id: "th_public_speaking",
    self_spec_id: "ss_demo",
    slug: "public-speaking",
    name: "Public Speaking",
    alpha: 3,
    beta: 5,
    last_engaged_at: "2026-07-24T18:00:00Z",
    momentum: 0.18,
    saturation: 0.1,
    depth: 3 / 8,
  },
  {
    id: "th_systems_design",
    self_spec_id: "ss_demo",
    slug: "systems-design",
    name: "Systems Design",
    alpha: 9,
    beta: 4,
    last_engaged_at: NOW,
    momentum: 0.74,
    saturation: 0.3,
    depth: 9 / 13,
  },
];

export const fixtureCandidates: Record<string, Candidate> = {
  deliberatePracticeEssay: {
    id: "cand_deliberate_practice",
    theme_id: "th_systems_design",
    kind: "essay",
    title: "The Making of an Expert: 22 Minutes on Deliberate Practice",
    url: "https://example.com/deliberate-practice",
    provider: "Farnam Street",
    minutes: 22,
    depth: 3,
    has_practice: true,
    view_count: 4200,
    verified: true,
    appraised_at: NOW,
  },
  productivityHacksVideo: {
    id: "cand_productivity_hacks",
    theme_id: "th_systems_design",
    kind: "video",
    title: "10 PRODUCTIVITY HACKS THAT WILL CHANGE YOUR LIFE 🔥",
    url: "https://example.com/productivity-hacks",
    provider: "YouTube",
    minutes: 8,
    depth: 1,
    has_practice: false,
    view_count: 4_200_000,
    verified: true,
    appraised_at: NOW,
  },
  replicationNotes: {
    id: "cand_replication_notes",
    theme_id: "th_systems_design",
    kind: "essay",
    title: "Designing Data-Intensive Applications — Ch. 5: Replication",
    url: "https://example.com/ddia-replication",
    provider: "O'Reilly",
    minutes: 35,
    depth: 3,
    has_practice: false,
    view_count: 12_000,
    verified: true,
    appraised_at: NOW,
  },
  vocalVarietyDrill: {
    id: "cand_vocal_variety",
    theme_id: "th_public_speaking",
    kind: "video",
    title: "The 7 Rules of Vocal Variety",
    url: "https://example.com/vocal-variety",
    provider: "YouTube",
    minutes: 14,
    depth: 2,
    has_practice: true,
    view_count: 89_000,
    verified: true,
    appraised_at: NOW,
  },
};

export const fixtureDecisions: Decision[] = [
  {
    id: "dec_1",
    user_id: "u_demo",
    candidate_id: "cand_deliberate_practice",
    served_at: NOW,
    growth_score: 0.85,
    breakdown: {
      alignment: 0.91,
      readiness: 0.84,
      actionability: 1,
      novelty: 0.8,
      effort_fit: 0.7,
      trust_weight: 1.0,
      saturation_penalty: 0.05,
      score: 0.85,
    },
    counterfactual_id: "cand_productivity_hacks",
    counterfactual_score: -0.01,
  },
  {
    id: "dec_2",
    user_id: "u_demo",
    candidate_id: "cand_replication_notes",
    served_at: NOW,
    growth_score: 0.55,
    breakdown: {
      alignment: 0.72,
      readiness: 0.6,
      actionability: 0.5,
      novelty: 0.65,
      effort_fit: 0.4,
      trust_weight: 1.0,
      saturation_penalty: 0.1,
      score: 0.55,
    },
    counterfactual_id: null,
    counterfactual_score: null,
  },
];

export const fixtureFeed: FeedItem[] = [
  {
    candidate: fixtureCandidates.deliberatePracticeEssay,
    breakdown: fixtureDecisions[0].breakdown,
    counterfactual_candidate: fixtureCandidates.productivityHacksVideo,
    counterfactual_engagement_score: 0.93,
  },
  {
    candidate: fixtureCandidates.replicationNotes,
    breakdown: fixtureDecisions[1].breakdown,
    counterfactual_candidate: null,
    counterfactual_engagement_score: null,
  },
];

export const fixtureFeedResponse: FeedResponse = {
  user_id: "u_demo",
  date: "2026-08-01",
  items: fixtureFeed,
  saturated: false,
};

export const fixtureSelfState: SelfState = {
  user_id: "u_demo",
  aspirations: fixtureAspirations,
  themes: fixtureThemes,
  today_budget_minutes: 45,
  drift_score: 0.67,
  recent_decisions: fixtureDecisions,
};
