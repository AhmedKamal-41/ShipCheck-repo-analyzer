import { Container } from "@/components/layout/Container";
import { ReportTabs } from "./ReportTabs";

function Spinner() {
  return (
    <div
      className="h-5 w-5 shrink-0 rounded-full border-2 border-[#d0d7de] border-t-[#0969da] animate-spin"
      aria-hidden
    />
  );
}

export function ReportSkeleton() {
  return (
    <>
      <ReportTabs activeId="overview" onChange={() => {}} />
      <Container className="py-4">
        <div className="flex gap-6 lg:gap-8">
          <div className="min-w-0 flex-1">
            <div className="mb-4 flex items-center gap-3">
              <Spinner />
              <div>
                <p className="text-sm font-medium text-[#1f2328]">Scanning repo…</p>
                <p className="text-xs text-[#57606a]">This may take a few seconds.</p>
              </div>
            </div>
            <div className="mb-4 h-10 animate-pulse rounded-md border border-[#d0d7de] bg-[#f6f8fa]" />
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-24 animate-pulse rounded-lg border border-[#d0d7de] bg-[#f6f8fa]"
                />
              ))}
            </div>
          </div>
          <div className="hidden w-72 shrink-0 lg:block">
            <div className="space-y-4">
              <div className="h-28 animate-pulse rounded-lg border border-[#d0d7de] bg-[#f6f8fa]" />
              <div className="h-24 animate-pulse rounded-lg border border-[#d0d7de] bg-[#f6f8fa]" />
              <div className="h-20 animate-pulse rounded-lg border border-[#d0d7de] bg-[#f6f8fa]" />
            </div>
          </div>
        </div>
      </Container>
    </>
  );
}
