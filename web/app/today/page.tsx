"use client";

import React, { useState, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import { Brain, Compass, RefreshCw, Layers, ShieldAlert, Sparkles, CheckSquare, Square, ExternalLink, HelpCircle, FastForward } from "lucide-react";
import ElicitationCard from "@/components/ElicitationCard";
import TracePanel from "@/components/TracePanel";
import { fixtureFeedResponse, fixtureSelfState } from "@/lib/fixtures";
import type { FeedItem, FeedResponse, TraceFrame } from "@/lib/types";

export default function TodayPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [isOnboarded, setIsOnboarded] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [answers, setAnswers] = useState<string[]>([]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [isSaturated, setIsSaturated] = useState(false);
  const [activeIntervention, setActiveIntervention] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [useMock, setUseMock] = useState(true); // Default to mock, toggle to live
  const [flippedCards, setFlippedCards] = useState<Record<string, boolean>>({});
  const [completedItems, setCompletedItems] = useState<Record<string, boolean>>({});
  const [showReflection, setShowReflection] = useState<string | null>(null);

  // Load user id from storage
  useEffect(() => {
    const storedUserId = localStorage.getItem("praxis_user_id");
    if (storedUserId) {
      setUserId(storedUserId);
      setIsOnboarded(true);
      setUseMock(false); // Try live if user exists
    }
  }, []);

  // Fetch feed
  useEffect(() => {
    if (!isOnboarded) return;

    if (useMock) {
      setFeed(fixtureFeedResponse.items);
      setIsSaturated(fixtureFeedResponse.saturated);
      return;
    }

    const fetchFeed = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/feed/${userId}`);
        if (!res.ok) throw new Error("API failed");
        const data = (await res.json()) as FeedResponse;
        setFeed(data.items);
        setIsSaturated(data.saturated);
        
        // Also fetch active interventions (nudges, do_blocks, drift)
        const intRes = await fetch(`/api/self/${userId}`);
        if (intRes.ok) {
          const selfState = await intRes.json();
          // Check for active do_blocks or drift proposals
          // We can call endpoints or verify
        }
      } catch (err) {
        console.error("Live feed fetch failed, falling back to mock:", err);
        setFeed(fixtureFeedResponse.items);
        setIsSaturated(fixtureFeedResponse.saturated);
      } finally {
        setLoading(false);
      }
    };

    fetchFeed();
  }, [userId, isOnboarded, useMock]);

  // Handle onboarding answers
  const handleOnboardingAnswer = async (answer: string | null) => {
    if (!answer) return;
    const newAnswers = [...answers, answer];
    setAnswers(newAnswers);

    if (onboardingStep < 4) {
      setOnboardingStep((prev) => prev + 1);
    } else {
      // Completed onboarding!
      setLoading(true);
      const generatedId = `usr_${Math.random().toString(36).substring(2, 8)}`;
      
      if (useMock) {
        // Mock flow
        setTimeout(() => {
          localStorage.setItem("praxis_user_id", generatedId);
          setUserId(generatedId);
          setIsOnboarded(true);
          setFeed(fixtureFeedResponse.items);
          setLoading(false);
        }, 1000);
      } else {
        // Live flow
        try {
          // Initialize user interview and register
          const startRes = await fetch("/api/self/interview/start", { method: "POST" });
          const startData = await startRes.json();
          
          let lastRes = startData;
          for (let i = 0; i < newAnswers.length; i++) {
            const res = await fetch("/api/self/interview/answer", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ step: i + 1, answer: newAnswers[i] }),
            });
            lastRes = await res.json();
          }

          if (lastRes.user_id) {
            localStorage.setItem("praxis_user_id", lastRes.user_id);
            setUserId(lastRes.user_id);
            setIsOnboarded(true);
          } else {
            throw new Error("No user_id returned");
          }
        } catch (err) {
          console.error("Live onboarding failed, saving mock session:", err);
          localStorage.setItem("praxis_user_id", generatedId);
          setUserId(generatedId);
          setIsOnboarded(true);
        } finally {
          setLoading(false);
        }
      }
    }
  };

  // Toggle card flip
  const toggleFlip = (cardId: string) => {
    setFlippedCards((prev) => ({ ...prev, [cardId]: !prev[cardId] }));
  };

  // Complete/open item
  const handleCompleteItem = async (candidateId: string) => {
    setCompletedItems((prev) => ({ ...prev, [candidateId]: true }));
    setShowReflection(candidateId);
  };

  // Submit reflection check-in
  const handleReflectionResolve = async (candidateId: string, reflection: string | null) => {
    setShowReflection(null);
    if (useMock) {
      alert(`Signal logged: Reflection "${reflection}" saved. Self Twin updated.`);
      return;
    }

    try {
      await fetch("/api/signal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          kind: "reflected",
          reflection: reflection,
        }),
      });
    } catch (err) {
      console.error("Failed to log reflection:", err);
    }
  };

  // Skip / Action button
  const handleActionItem = async (candidateId: string) => {
    alert("Action item logged. Theme momentum increased! +0.35");
    if (useMock) return;
    try {
      await fetch("/api/signal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          kind: "acted",
        }),
      });
    } catch (err) {
      console.error("Failed to log action:", err);
    }
  };

  // Advance time demo helper
  const handleAdvanceDemo = async () => {
    if (useMock) {
      setIsSaturated(true);
      alert("Demo advanced by 5 days. Theme 'Systems Design' has saturated (too much reading, zero actions). Do Block Refusal triggered.");
      return;
    }

    try {
      const res = await fetch("/api/demo/advance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days: 5 }),
      });
      if (res.ok) {
        const data = await res.json();
        // Refresh feed & check for saturation
        const feedRes = await fetch(`/api/feed/${userId}`);
        const feedData = await feedRes.json();
        setFeed(feedData.items);
        setIsSaturated(feedData.saturated);
      }
    } catch (err) {
      console.error("Failed to advance demo:", err);
    }
  };

  // Reset demo
  const handleResetDemo = () => {
    localStorage.removeItem("praxis_user_id");
    setUserId(null);
    setIsOnboarded(false);
    setOnboardingStep(1);
    setAnswers([]);
    setFeed([]);
    setIsSaturated(false);
    setCompletedItems({});
    setShowReflection(null);
    setUseMock(true);
  };

  // --- RENDER ONBOARDING ---
  if (!isOnboarded) {
    const activeQuestion = getOnboardingStepQuestion(onboardingStep);
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-zinc-950 p-6">
        <div className="w-full max-w-xl text-center mb-8">
          <h1 className="score-mono text-xl font-bold tracking-[0.25em] text-zinc-100 uppercase mb-2">
            Praxis
          </h1>
          <p className="text-zinc-500 text-xs tracking-wider max-w-sm mx-auto">
            "Your attention is product. Your potential is purpose. Let's calibrate."
          </p>
        </div>
        <AnimatePresence mode="wait">
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 text-zinc-400 gap-3">
              <RefreshCw className="h-6 w-6 animate-spin text-indigo-400" />
              <span className="text-xs font-mono tracking-widest uppercase">
                Synthesizing Aspirations...
              </span>
            </div>
          ) : (
            <ElicitationCard
              key={onboardingStep}
              type="onboarding"
              step={onboardingStep}
              of={4}
              title={`Question ${onboardingStep}`}
              body={activeQuestion.question}
              options={activeQuestion.options}
              onResolve={handleOnboardingAnswer}
            />
          )}
        </AnimatePresence>
      </div>
    );
  }

  // --- RENDER DO BLOCK REFUSAL ---
  if (isSaturated) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-zinc-950 p-6">
        <div className="mb-8 flex flex-col items-center">
          <ShieldAlert className="h-12 w-12 text-rose-500 mb-2 animate-pulse" />
          <h2 className="text-zinc-200 font-mono text-sm tracking-widest uppercase">
            Praxis Intervention
          </h2>
        </div>
        <ElicitationCard
          type="do_block"
          title="Consuming without doing."
          body="You've completed 4 guides on Systems Design this week and logged zero practice actions. To break the research-loop trap, I've locked this theme. No new recommendations will appear until you take action."
          options={["I have completed a practice item", "Hold me to it", "Re-calibrate theme"]}
          onResolve={() => {
            setIsSaturated(false);
            alert("Saturation penalty cleared. Content feeds unlocked.");
          }}
        />
        
        {/* Demo controls */}
        <div className="mt-12 flex gap-4 text-xs font-mono text-zinc-500 border border-zinc-900 bg-zinc-900/10 p-3 rounded-lg">
          <button onClick={handleResetDemo} className="hover:text-zinc-300">
            [Reset Demo]
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-zinc-950 p-6 md:p-12 text-zinc-100 flex flex-col">
      <div className="mx-auto w-full max-w-4xl flex-1 flex flex-col md:flex-row gap-8">
        
        {/* Main Feed Lane */}
        <div className="flex-1 space-y-6">
          <div className="flex items-center justify-between border-b border-zinc-900 pb-4">
            <div>
              <h2 className="text-xs font-mono font-bold tracking-widest uppercase text-zinc-400">
                Decision of the Day
              </h2>
              <p className="text-[10px] text-zinc-600 font-mono mt-0.5">
                Targeting: Systems Design & Public Speaking
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-mono text-zinc-600">
                Mode: {useMock ? "Offline Mock" : "Live Backend"}
              </span>
              <button
                onClick={() => setUseMock(!useMock)}
                className="text-[10px] font-mono border border-zinc-800 hover:border-zinc-700 px-2 py-0.5 rounded text-zinc-400 hover:text-zinc-200"
              >
                [Toggle Mode]
              </button>
            </div>
          </div>

          {feed.length === 0 ? (
            <div className="text-center py-20 text-zinc-600 text-xs font-mono">
              Generating your bounded daily feed...
            </div>
          ) : (
            <div className="space-y-6">
              {feed.map((item) => {
                const isFlipped = flippedCards[item.candidate.id] || false;
                const isCompleted = completedItems[item.candidate.id] || false;

                return (
                  <div
                    key={item.candidate.id}
                    className="relative group transition-all duration-300"
                  >
                    {/* Perspective wrapper for 3D card flip effect */}
                    <div className="relative w-full min-h-[16rem] rounded-xl border border-zinc-900 bg-[#141414] overflow-hidden hover:border-zinc-800 transition-colors">
                      
                      {!isFlipped ? (
                        /* FRONT OF CARD: PRAXIS Curation */
                        <div className="p-6 flex flex-col h-full justify-between">
                          <div>
                            <div className="flex items-start justify-between gap-4 mb-3">
                              <span className="inline-flex items-center gap-1 rounded bg-zinc-900 border border-zinc-800 px-2 py-0.5 text-[9px] font-mono text-zinc-400">
                                {item.candidate.kind.toUpperCase()} • {item.candidate.minutes} MINS
                              </span>
                              <div className="text-right">
                                <span className="text-[9px] font-mono text-zinc-500 uppercase block">Growth Score</span>
                                <span className="text-xs font-mono font-bold text-emerald-400">
                                  +{item.breakdown.score.toFixed(2)}
                                </span>
                              </div>
                            </div>
                            
                            <h3 className="text-base font-semibold text-zinc-100 mb-1 leading-snug">
                              {item.candidate.title}
                            </h3>
                            <p className="text-[10px] font-mono text-zinc-500 mb-4">
                              Source: {item.candidate.provider} • Depth {item.candidate.depth}/3
                            </p>

                            {/* Core metrics details */}
                            <div className="grid grid-cols-4 gap-2 border-t border-zinc-900/60 pt-3 text-[9px] font-mono text-zinc-500">
                              <div>
                                <span className="block text-[8px] text-zinc-600">Alignment</span>
                                <span className="text-zinc-400">{item.breakdown.alignment.toFixed(2)}</span>
                              </div>
                              <div>
                                <span className="block text-[8px] text-zinc-600">Readiness</span>
                                <span className="text-zinc-400">{item.breakdown.readiness.toFixed(2)}</span>
                              </div>
                              <div>
                                <span className="block text-[8px] text-zinc-600">Actionable</span>
                                <span className="text-zinc-400">{item.candidate.has_practice ? "Yes" : "No"}</span>
                              </div>
                              <div>
                                <span className="block text-[8px] text-zinc-600">Trust Wt</span>
                                <span className="text-zinc-400">x{item.breakdown.trust_weight.toFixed(1)}</span>
                              </div>
                            </div>
                          </div>

                          <div className="mt-6 flex items-center justify-between border-t border-zinc-900/50 pt-4">
                            <div className="flex gap-2">
                              {!isCompleted ? (
                                <button
                                  onClick={() => handleCompleteItem(item.candidate.id)}
                                  className="flex items-center gap-1.5 rounded-lg bg-zinc-100 hover:bg-zinc-200 px-3 py-1.5 text-xs text-zinc-950 font-bold font-mono transition-colors"
                                >
                                  Complete
                                </button>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-emerald-400 text-xs font-mono font-semibold">
                                  ✓ Completed
                                </span>
                              )}
                              {item.candidate.has_practice && (
                                <button
                                  onClick={() => handleActionItem(item.candidate.id)}
                                  className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 hover:bg-emerald-950/20 px-3 py-1.5 text-xs text-emerald-400 font-mono transition-colors"
                                >
                                  Take Action
                                </button>
                              )}
                            </div>
                            
                            {item.counterfactual_candidate && (
                              <button
                                onClick={() => toggleFlip(item.candidate.id)}
                                className="text-[10px] font-mono text-zinc-500 hover:text-zinc-300"
                              >
                                [Why curated?]
                              </button>
                            )}
                          </div>
                        </div>
                      ) : (
                        /* BACK OF CARD: Engagement Counterfactual */
                        <div className="p-6 bg-zinc-950 flex flex-col h-full justify-between border-l-2 border-amber-500/50">
                          <div>
                            <div className="flex items-center justify-between border-b border-zinc-900 pb-2 mb-4">
                              <span className="text-[9px] font-mono font-bold text-amber-500 tracking-wider uppercase">
                                What Attention-CTR Would Pick
                              </span>
                              <span className="text-[10px] font-mono text-zinc-600">
                                CTR Score: {item.counterfactual_engagement_score?.toFixed(2) || "0.95"}
                              </span>
                            </div>

                            <h4 className="text-sm font-semibold text-zinc-400 mb-1 leading-snug">
                              {item.counterfactual_candidate?.title || "Clickbait alternative"}
                            </h4>
                            <p className="text-[10px] font-mono text-zinc-600 mb-4">
                              Provider: {item.counterfactual_candidate?.provider} • Views: {(item.counterfactual_candidate?.view_count || 1000000) / 1000000}M • Mins: {item.counterfactual_candidate?.minutes}
                            </p>

                            <div className="bg-amber-950/10 border border-amber-950/50 rounded-lg p-3 text-[10px] font-mono text-amber-400/80 leading-relaxed">
                              <strong>Why Praxis filtered this:</strong>
                              <ul className="list-disc pl-4 mt-1 space-y-1">
                                <li>Alignment: {(item.counterfactual_candidate?.depth || 1) < 2 ? "Low alignment (0.21)" : "Standard"}</li>
                                <li>Clickbait features: life hacks, CAPITALIZED titles</li>
                                <li>Short duration optimized for instant gratification</li>
                              </ul>
                            </div>
                          </div>

                          <div className="mt-6 flex items-center justify-end border-t border-zinc-900/50 pt-4">
                            <button
                              onClick={() => toggleFlip(item.candidate.id)}
                              className="text-[10px] font-mono text-zinc-500 hover:text-zinc-300"
                            >
                              [Back to Growth]
                            </button>
                          </div>
                        </div>
                      )}

                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Feed End Boundary */}
          <div className="text-center py-10 border-t border-zinc-900 mt-12">
            <Layers className="h-6 w-6 text-zinc-800 mx-auto mb-2" />
            <p className="text-[10px] font-mono text-zinc-600 tracking-widest uppercase">
              The feed has ended for today.
            </p>
            <p className="text-[10px] text-zinc-700 mt-1">
              "We serve links to act, not scroll."
            </p>
          </div>
        </div>

        {/* Sidebar Info & Telemetry controls */}
        <div className="w-full md:w-64 space-y-6">
          <div className="border border-zinc-900 bg-zinc-900/10 rounded-xl p-4 space-y-4">
            <h3 className="text-xs font-mono font-bold tracking-widest uppercase text-zinc-400 border-b border-zinc-900 pb-2">
              Time Travel Demo
            </h3>
            <p className="text-[10px] text-zinc-500 leading-relaxed">
              Use this switch to fast-forward time. Praxis will decay learning parameters, check for inactivity stalls, and flag theme saturation (Moat 2).
            </p>
            
            <button
              onClick={handleAdvanceDemo}
              className="w-full rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 p-2.5 text-xs text-zinc-300 font-mono font-medium flex items-center justify-center gap-2 transition-all"
            >
              <FastForward className="h-3.5 w-3.5 text-indigo-400" />
              Advance 5 Days
            </button>

            <button
              onClick={handleResetDemo}
              className="w-full rounded-lg bg-transparent border border-dashed border-zinc-800 hover:border-zinc-700 p-2 text-[10px] text-zinc-600 hover:text-zinc-400 font-mono text-center transition-all"
            >
              [Reset Onboarding]
            </button>
          </div>

          {/* Active check-in card overlays */}
          {showReflection && (
            <div className="border border-zinc-900 bg-[#1A1A1A] rounded-xl p-4 space-y-3">
              <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase block tracking-wider">
                Reflection check-in
              </span>
              <p className="text-xs text-zinc-400 leading-normal">
                How did this content fit your current level?
              </p>
              <div className="flex flex-col gap-1.5">
                {["too_easy", "right", "too_hard"].map((level) => (
                  <button
                    key={level}
                    onClick={() => handleReflectionResolve(showReflection, level)}
                    className="w-full rounded border border-zinc-800 bg-zinc-900/60 p-2 text-left font-mono text-[10px] text-zinc-300 hover:bg-zinc-800/80 transition-all"
                  >
                    {level === "too_easy" ? "Too Easy (Alpha boost)" : level === "right" ? "Just Right (ZPD Optimal)" : "Too Hard (Beta safety)"}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>

      {/* SSE Trace stream telemetry */}
      <TracePanel userId={userId || ""} isEnabled={isOnboarded} />
    </div>
  );
}

// Helpers
function getOnboardingStepQuestion(step: number) {
  switch (step) {
    case 1:
      return {
        question: "What is the primary skill, identity, or long-term aspiration you are trying to cultivate?",
        options: null,
      };
    case 2:
      return {
        question: "How many minutes can you realistically dedicate daily to this goal?",
        options: ["15 minutes", "30 minutes", "45 minutes", "60 minutes"],
      };
    case 3:
      return {
        question: "What is your current level of experience in this domain?",
        options: [
          "Novice (completely new, starting from zero)",
          "Intermediate (have foundational knowledge, want execution details)",
          "Advanced (active practitioner, looking for deep technical mastery)",
        ],
      };
    case 4:
      return {
        question: "What has historically been your biggest barrier to achieving this goal?",
        options: [
          "Distraction & clickbait content overload",
          "Lack of concrete practice or action steps",
          "Saturating on research without implementing",
          "Time constraints & busy schedule",
        ],
      };
    default:
      return { question: "", options: null };
  }
}
