interface ScoreCardProps {
  score: number;
  label?: string;
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

export function ScoreCard({ score, label = "Readiness Score" }: ScoreCardProps) {
  const clamped = Math.min(100, Math.max(0, score));
  const dashArray = 2 * Math.PI * 44;
  const dashOffset = dashArray - (clamped / 100) * dashArray;

  return (
    <div className="flex flex-col items-center">
      <div className="relative inline-flex h-32 w-32 items-center justify-center">
        <svg
          className="-rotate-90"
          width="128"
          height="128"
          viewBox="0 0 128 128"
          aria-hidden
        >
          <circle
            cx="64"
            cy="64"
            r="44"
            fill="none"
            stroke="rgb(226 232 240)"
            strokeWidth="8"
          />
          <circle
            cx="64"
            cy="64"
            r="44"
            fill="none"
            strokeWidth="8"
            strokeLinecap="round"
            className={scoreStroke(score)}
            style={{
              strokeDasharray: dashArray,
              strokeDashoffset: dashOffset,
              transition: "stroke-dashoffset 0.5s ease",
            }}
          />
        </svg>
        <span
          className={`absolute text-3xl font-bold ${scoreColor(score)}`}
        >
          {score}
        </span>
      </div>
      <p className="mt-2 text-sm font-medium text-slate-500">{label}</p>
    </div>
  );
}
