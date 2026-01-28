import { Container } from "@/components/layout/Container";

function Spinner() {
  return (
    <div
      className="h-6 w-6 shrink-0 rounded-full border-2 border-slate-300 border-t-slate-600 animate-spin"
      aria-hidden
    />
  );
}

export function ReportSkeleton() {
  return (
    <>
      <section className="py-10 lg:py-12">
        <Container>
          <div className="mb-6 flex items-center gap-3">
            <Spinner />
            <div>
              <p className="font-medium text-slate-700">Scanning repo…</p>
              <p className="text-sm text-slate-500">This may take a few seconds.</p>
            </div>
          </div>
          <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-400">
            Overview
          </p>
          <div className="grid items-stretch gap-6 lg:grid-cols-2 lg:gap-8">
            <div className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-slate-100/80" />
            <div className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-slate-100/80" />
          </div>
        </Container>
      </section>
      <Container className="pb-16 pt-0">
        <div className="mb-6 h-12 animate-pulse rounded-xl border border-slate-200 bg-slate-100/80 lg:mb-8" />
        <p className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-400">
          Checks
        </p>
        <div className="space-y-6 lg:space-y-8">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-2xl border border-slate-200 bg-slate-100/80"
            />
          ))}
        </div>
      </Container>
    </>
  );
}
