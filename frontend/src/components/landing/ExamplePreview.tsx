import { Check, X } from "lucide-react";
import { Container } from "@/components/layout/Container";
import { CenteredSection } from "@/components/layout/CenteredSection";
import { CenteredSectionHeader } from "@/components/ui/CenteredSectionHeader";
import { Badge } from "@/components/ui/Badge";

export function ExamplePreview() {
  return (
    <CenteredSection id="example" className="scroll-mt-20">
      <Container>
        <CenteredSectionHeader
          title="Example report"
          subtitle="A product-style preview of what you get."
        />
        <div className="mx-auto max-w-5xl pt-8 md:pt-12">
          <div className="rounded-3xl border border-slate-200 bg-white/70 p-6 shadow-sm md:p-10">
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-2xl font-bold text-slate-800">
                82
              </div>
              <div>
                <p className="font-semibold text-slate-900">Readiness Score</p>
                <p className="text-sm text-slate-500">example-repo</p>
              </div>
            </div>
            <div className="mt-6 flex flex-wrap gap-2">
              <Badge status="pass">CI found</Badge>
              <Badge status="fail">Tests missing</Badge>
              <Badge status="pass">Docker ready</Badge>
            </div>
            <ul className="mt-6 space-y-2">
              {["README install/run", "CI config", "Test directory"].map(
                (item) => (
                  <li
                    key={item}
                    className="flex items-center gap-2 text-sm text-slate-700"
                  >
                    <Check className="h-4 w-4 shrink-0 text-green-600" />
                    {item}
                  </li>
                )
              )}
              <li className="flex items-center gap-2 text-sm text-slate-700">
                <X className="h-4 w-4 shrink-0 text-red-500" />
                Dependency lockfile
              </li>
            </ul>
            <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Evidence snippet
              </p>
              <pre className="mt-2 max-h-32 overflow-auto font-mono text-xs leading-relaxed text-slate-700">
                {`# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt`}
              </pre>
            </div>
          </div>
        </div>
      </Container>
    </CenteredSection>
  );
}
