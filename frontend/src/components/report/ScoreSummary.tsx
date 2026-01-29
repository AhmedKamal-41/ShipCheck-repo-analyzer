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
  if (score >= 70) return "text-[#1f883d]";
  if (score >= 40) return "text-[#9a6700]";
  return "text-[#cf222e]";
}

function scoreStroke(score: number) {
  if (score >= 70) return "stroke-[#1f883d]";
  if (score >= 40) return "stroke-[#9a6700]";
  return "stroke-[#cf222e]";
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
        <p className="mb-4 text-xs font-medium uppercase tracking-wider text-[#57606a]">
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
                    stroke="#d0d7de"
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
                <p className="font-heading text-lg font-semibold text-[#1f2328]">Readiness Score</p>
                {lastAnalyzed && (
                  <p className="mt-1 text-sm text-[#57606a]">
                    Last analyzed: {lastAnalyzed}
                  </p>
                )}
                {commitSha && (
                  <code className="mt-2 inline-block rounded border border-[#d0d7de] bg-[#f6f8fa] px-2 py-1 font-mono text-xs text-[#57606a]">
                    {commitSha.slice(0, 7)}
                  </code>
                )}
              </div>
            </div>
          </Card>
          <Card className="flex h-full flex-col hover:translate-y-0">
            <p className="mb-4 text-xs font-medium uppercase tracking-wider text-[#57606a]">
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
