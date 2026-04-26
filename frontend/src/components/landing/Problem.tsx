import { LandingSection } from "./LandingSection";

const COMPARISON = [
  { value: "15 min", label: "per repo, manual" },
  { value: "12 sec", label: "per repo, ShipCheck" },
] as const;

export function Problem() {
  return (
    <LandingSection id="problem" bg="bg">
      <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:gap-16">
        <div className="max-w-[640px]">
          <p className="eyebrow">The problem</p>
          <h2 className="font-heading mt-3 text-[2.5rem] font-semibold leading-[1.05] tracking-tight text-[var(--text)] sm:text-[2.75rem]">
            Manual repo review doesn&apos;t scale.
          </h2>
          <div className="mt-6 space-y-4 text-base leading-relaxed text-[var(--text)]">
            <p>
              Hiring managers spend{" "}
              <span className="mono-inline">15+ minutes</span> per candidate
              clicking through repos to spot tests, CI, Docker, and README
              quality.
            </p>
            <p>
              Multiplied across a candidate pool of{" "}
              <span className="mono-inline">50</span>, that&apos;s a full work
              week before any interviews start.
            </p>
            <p className="text-[var(--muted)]">
              ShipCheck does the first pass deterministically, in seconds, with
              evidence you can point at.
            </p>
          </div>
        </div>

        <aside
          className="grid grid-cols-2 items-start gap-x-6 sm:gap-x-10 lg:gap-x-12"
          aria-label="Time per repo"
        >
          {COMPARISON.map((c, i) => (
            <div
              key={c.value}
              className={
                i === 0
                  ? "pr-6 sm:pr-10 lg:pr-12 border-r border-[var(--border)]"
                  : ""
              }
            >
              <span className="display-stat">{c.value}</span>
              <span className="eyebrow mt-3 block">{c.label}</span>
            </div>
          ))}
        </aside>
      </div>
    </LandingSection>
  );
}
