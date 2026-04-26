import { LandingSection } from "./LandingSection";
import { LandingSectionHeader } from "./LandingSectionHeader";

const AUDIENCES = [
  {
    title: "Hiring managers",
    items: [
      "Filter a candidate pool down to substantive repos in minutes.",
      "Generate tailored interview questions grounded in the candidate's own code.",
      "Carry concrete evidence into hiring decisions: file paths, line ranges, the rule that fired.",
    ],
  },
  {
    title: "Engineers",
    items: [
      "Audit your own portfolio before a single recruiter clicks Apply.",
      "See exactly which gaps are visible from outside: README, CI, lockfile, tests.",
      "Score yourself on the same rubric a reviewer would use.",
    ],
  },
] as const;

export function Audiences() {
  return (
    <LandingSection id="audiences" bg="bg">
      <LandingSectionHeader
        eyebrow="Who it's for"
        title="Built for two audiences."
        subtitle="One side filtering. One side preparing. Same rubric on both."
        align="center"
      />

      <div className="mx-auto mt-12 grid max-w-[960px] grid-cols-1 gap-6 md:grid-cols-2">
        {AUDIENCES.map((a) => (
          <article
            key={a.title}
            className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 transition-all duration-200 ease-out hover:border-[#8c959f] hover:shadow-md"
          >
            <h3 className="font-heading text-xl font-semibold text-[var(--text)]">
              {a.title}
            </h3>
            <ul className="mt-4 space-y-3">
              {a.items.map((item) => (
                <li
                  key={item}
                  className="flex gap-3 text-sm leading-relaxed text-[var(--text)]"
                >
                  <span
                    className="mt-2 h-1 w-1 shrink-0 rounded-full bg-[var(--muted)]"
                    aria-hidden
                  />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </LandingSection>
  );
}
