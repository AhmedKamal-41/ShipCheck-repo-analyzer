import { LandingSection } from "./LandingSection";
import { LandingSectionHeader } from "./LandingSectionHeader";

const AST_SNIPPET = `radon.cc_visit(src)
# → Function(name="handler",
#            complexity=11)`;

const SCORING_SNIPPET = `Runability        20%
Testing & CI      20%
Security & Deps   20%
Maintainability   15%
Architecture      15%
Documentation     10%`;

const READONLY_SNIPPET = `GET /repos/:owner/:repo
GET /repos/:owner/:repo/git/trees
GET /repos/:owner/:repo/contents/...`;

const PILLARS = [
  {
    title: "AST-based",
    description:
      "Python via radon. JS/TS via tree-sitter. Import graphs via networkx. Every finding is reproducible from the same input.",
    snippet: AST_SNIPPET,
  },
  {
    title: "Categorical scoring",
    description:
      "Six weighted categories totaling 100%. Severity, confidence, and scope-factor weight each finding before the average.",
    snippet: SCORING_SNIPPET,
  },
  {
    title: "Read-only by design",
    description:
      "Only repo metadata and key files via the GitHub REST API. Code is never downloaded in full and never executed.",
    snippet: READONLY_SNIPPET,
  },
] as const;

export function HowItWorks() {
  return (
    <LandingSection id="how-it-works" bg="bg">
      <LandingSectionHeader
        eyebrow="How it works"
        title="Real static analysis. No LLMs. No code execution."
        subtitle="Three layers between a GitHub URL and a score. Each is deterministic and auditable."
        align="left"
      />

      <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3 md:gap-6">
        {PILLARS.map((p) => (
          <article
            key={p.title}
            className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 transition-all duration-200 ease-out hover:border-[#8c959f] hover:shadow-md"
          >
            <h3 className="text-base font-semibold text-[var(--text)]">
              {p.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
              {p.description}
            </p>
            <pre className="mt-4 overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--surface-2)] p-3 font-mono text-xs leading-relaxed text-[var(--text)]">
              {p.snippet}
            </pre>
          </article>
        ))}
      </div>
    </LandingSection>
  );
}
