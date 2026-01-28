import { Container } from "@/components/layout/Container";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export type HighlightItem = {
  label: string;
  status: "pass" | "warn" | "fail";
};

interface ScoreSummaryProps {
  score: number;
  lastAnalyzed?: string;
  commitSha?: string | null;
  highlights: HighlightItem[];
}

function scoreColor(score: number) {
  if (score >= 70) return "text-green-600";
  if (score >= 40) return "text-amber-600";
  return "text-red-600";
}

function scoreStroke(score: number) {
  if (score >= 70) return "stroke-green-500";
  if (score >= 40) return "stroke-amber-500";
  return "stroke-red-500";
}

export function ScoreSummary({
  score,
  lastAnalyzed,
  commitSha,
  highlights,
}: ScoreSummaryProps) {
  const clamped = Math.min(100, Math.max(0, score));
  const r = 48;
  const dashArray = 2 * Math.PI * r;
  const dashOffset = dashArray - (clamped / 100) * dashArray;

  return (
    <section className="py-10 lg:py-12">
      <Container>
        <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-500">
          Overview
        </p>
        <div className="grid items-stretch gap-6 lg:grid-cols-2 lg:gap-8">
          <Card className="flex h-full flex-col hover:translate-y-0">
            <div className="flex flex-1 items-center gap-6">
              <div className="relative flex h-28 w-28 shrink-0 items-center justify-center">
                <svg
                  className="-rotate-90"
                  width={112}
                  height={112}
                  viewBox="0 0 112 112"
                  aria-hidden
                >
                  <circle
                    cx="56"
                    cy="56"
                    r={r}
                    fill="none"
                    stroke="rgb(226 232 240)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="56"
                    cy="56"
                    r={r}
                    fill="none"
                    strokeWidth="8"
                    strokeLinecap="round"
                    className={scoreStroke(score)}
                    style={{
                      strokeDasharray: dashArray,
                      strokeDashoffset: dashOffset,
                    }}
                  />
                </svg>
                <span className={`font-heading absolute text-2xl font-bold ${scoreColor(score)}`}>
                  {score}
                </span>
              </div>
              <div>
                <p className="font-heading text-lg font-semibold text-slate-900">Readiness Score</p>
                {lastAnalyzed && (
                  <p className="mt-1 text-sm text-slate-500">
                    Last analyzed: {lastAnalyzed}
                  </p>
                )}
                {commitSha && (
                  <code className="mt-2 inline-block rounded bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600">
                    {commitSha.slice(0, 7)}
                  </code>
                )}
              </div>
            </div>
          </Card>
          <Card className="flex h-full flex-col hover:translate-y-0">
            <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-500">
              Highlights
            </p>
            <div className="flex flex-1 flex-wrap content-start gap-2">
              {highlights.map((h) => (
                <Badge key={h.label} status={h.status}>
                  {h.label}
                </Badge>
              ))}
            </div>
          </Card>
        </div>
      </Container>
    </section>
  );
}
