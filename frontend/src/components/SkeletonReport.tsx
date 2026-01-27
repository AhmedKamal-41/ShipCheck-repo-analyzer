export function SkeletonReport() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-slate-200 bg-white p-8 sm:flex-row sm:justify-around">
        <div className="h-32 w-32 animate-pulse rounded-full bg-slate-200" />
        <div className="flex flex-1 flex-col gap-2">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-4 w-full max-w-xs animate-pulse rounded bg-slate-200"
            />
          ))}
        </div>
      </div>
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-16 w-full animate-pulse rounded-xl bg-slate-100"
          />
        ))}
      </div>
    </div>
  );
}
