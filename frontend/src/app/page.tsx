"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  FileInput,
  ScanSearch,
  FileCheck,
  Package,
  TestTube,
  ShieldCheck,
  MessageCircleQuestion,
} from "lucide-react";
import { PageShell } from "@/components/PageShell";
import { HeroInputCard } from "@/components/HeroInputCard";
import { StepCard } from "@/components/StepCard";
import { FeatureCard } from "@/components/FeatureCard";
import { analyzeRepo } from "@/lib/api";
import { validateGitHubUrl } from "@/lib/validate";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const v = validateGitHubUrl(url);
    if (!v.valid) {
      setError(v.error);
      return;
    }
    setLoading(true);
    try {
      const data = await analyzeRepo(url);
      router.push(`/reports/${data.report_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)]">
      <PageShell maxWidth="xl" className="py-12 sm:py-16 lg:py-20">
        <section className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Instant repo readiness report.
          </h1>
          <p className="mt-4 text-lg text-slate-600">
            Analyze runnability, tests, CI, and security—then share a
            recruiter-ready report.
          </p>
          <div className="mt-8">
            <HeroInputCard
              value={url}
              onChange={setUrl}
              onSubmit={handleSubmit}
              loading={loading}
              error={error}
            />
          </div>
        </section>

        <section
          id="how-it-works"
          className="mt-24 scroll-mt-20 sm:mt-32"
          aria-labelledby="how-it-works-heading"
        >
          <h2
            id="how-it-works-heading"
            className="text-center text-2xl font-bold text-slate-900"
          >
            How it works
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            <StepCard
              step={1}
              icon={<FileInput className="h-4 w-4" />}
              title="Paste repo URL"
              description="Enter any public GitHub repository link."
            />
            <StepCard
              step={2}
              icon={<ScanSearch className="h-4 w-4" />}
              title="We scan key files safely"
              description="No code execution. Read-only analysis of public files."
            />
            <StepCard
              step={3}
              icon={<FileCheck className="h-4 w-4" />}
              title="Get score + report + questions"
              description="Readiness score, shareable report, and interview questions."
            />
          </div>
        </section>

        <section
          id="examples"
          className="mt-24 scroll-mt-20 sm:mt-32"
          aria-labelledby="examples-heading"
        >
          <h2
            id="examples-heading"
            className="text-center text-2xl font-bold text-slate-900"
          >
            What we check
          </h2>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <FeatureCard
              icon={<Package className="h-5 w-5" />}
              title="Runability"
              description="Setup clarity, Docker, run instructions."
            />
            <FeatureCard
              icon={<TestTube className="h-5 w-5" />}
              title="Engineering Quality"
              description="Tests, CI, lint, dependency pinning."
            />
            <FeatureCard
              icon={<ShieldCheck className="h-5 w-5" />}
              title="Security Signals"
              description="Secrets hygiene, .env.example."
            />
            <FeatureCard
              icon={<MessageCircleQuestion className="h-5 w-5" />}
              title="Interview Pack"
              description="Questions tailored to the repo."
            />
          </div>
        </section>

        <section className="mt-16 sm:mt-24">
          <div className="rounded-xl border border-slate-200 bg-slate-50/80 px-6 py-4 text-center">
            <p className="text-sm font-medium text-slate-700">
              No code is executed. Read-only analysis of public files.
            </p>
          </div>
        </section>
      </PageShell>
    </div>
  );
}
