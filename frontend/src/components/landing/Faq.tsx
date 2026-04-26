import { LandingSection } from "./LandingSection";
import { LandingSectionHeader } from "./LandingSectionHeader";

const FAQ = [
  {
    q: "Does ShipCheck need access to my private repos?",
    a: "No. Public repos only, via the GitHub REST API. There is no OAuth flow and no app installation.",
  },
  {
    q: "Does it execute my code?",
    a: "Never. Static analysis only: AST parsing, regex pattern matches, and import-graph traversal. No subprocess, no sandbox, no runtime.",
  },
  {
    q: "How are scores computed?",
    a: "Six weighted categories sum to 100%. Each finding is weighted by severity, confidence, and scope-factor before contributing to its category. The full rubric is in the docs.",
  },
  {
    q: "Can I customize the rubric for my org?",
    a: "Not yet. Every repo is scored on the same rubric so reports are comparable across candidates. Per-org weights are on the roadmap.",
  },
  {
    q: "Why no LLMs?",
    a: "Determinism. Reviewers and candidates can both verify findings against the source. LLM-assisted second opinions are coming as an opt-in layer on top, never as the default.",
  },
] as const;

export function Faq() {
  return (
    <LandingSection id="faq" bg="bg">
      <LandingSectionHeader
        eyebrow="FAQ"
        title="Questions"
        align="center"
      />

      <dl className="mx-auto mt-12 max-w-[760px]">
        {FAQ.map((item, i) => (
          <div
            key={item.q}
            className={`grid grid-cols-1 gap-2 py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] md:gap-8 ${
              i === 0 ? "" : "border-t border-[var(--border)]"
            }`}
          >
            <dt className="text-base font-semibold text-[var(--text)]">
              {item.q}
            </dt>
            <dd className="text-base leading-relaxed text-[var(--muted)]">
              {item.a}
            </dd>
          </div>
        ))}
      </dl>
    </LandingSection>
  );
}
