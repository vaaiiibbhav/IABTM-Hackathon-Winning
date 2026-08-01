import Link from "next/link";
import { ElicitationCard } from "@/components/elicitation-card";

// The onboarding interview is agent-initiated and tap-answered, never a chat box
// (§5a). This is a static preview of the first step — inline mock, no fixture
// exists for the interview endpoint yet.
const FIRST_INTERVIEW_STEP = {
  question: "How much time can you give this, most days?",
  step: 1,
  of: 4,
  options: ["10 minutes", "25 minutes", "45 minutes", "an hour+"],
};

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-6 py-16">
      <p className="text-sm tracking-wide text-muted-foreground uppercase">Praxis</p>
      <h1 className="mt-2 max-w-lg text-3xl leading-tight font-semibold text-foreground sm:text-4xl">
        Your feed knows exactly what you&apos;ll watch. It has no idea who you&apos;re
        trying to become.
      </h1>
      <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground">
        Praxis scores every candidate against a model of your growth aspiration instead of
        your attention — and shows you the arithmetic it used to choose. It is also
        willing to serve you nothing.
      </p>

      <Link
        href="/today"
        className="mt-6 inline-flex w-fit items-center gap-2 rounded-md bg-agent px-4 py-2 text-sm font-medium text-agent-foreground transition-opacity hover:opacity-90"
      >
        Open today&apos;s feed
      </Link>

      <div className="mt-12">
        <p className="mb-2 text-[0.7rem] tracking-wide text-muted-foreground uppercase">
          This is how it starts — a tap interview, not a textarea
        </p>
        <ElicitationCard
          meta={`Step ${FIRST_INTERVIEW_STEP.step} of ${FIRST_INTERVIEW_STEP.of}`}
          prompt={FIRST_INTERVIEW_STEP.question}
          options={FIRST_INTERVIEW_STEP.options.map((label) => ({ label, value: label }))}
        />
      </div>
    </main>
  );
}
