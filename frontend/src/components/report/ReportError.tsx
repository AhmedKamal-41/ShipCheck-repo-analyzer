"use client";

import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Container } from "@/components/layout/Container";
import { Button } from "@/components/ui/Button";

function Spinner() {
  return (
    <div
      className="h-5 w-5 shrink-0 rounded-full border-2 border-white/40 border-t-white animate-spin"
      aria-hidden
    />
  );
}

interface ReportErrorProps {
  message: string;
  retrying: boolean;
  onRetry: () => void;
  retryError?: string | null;
}

export function ReportError({
  message,
  retrying,
  onRetry,
  retryError,
}: ReportErrorProps) {
  return (
    <Container className="py-12 lg:py-16">
      <div className="mx-auto max-w-md rounded-2xl border border-red-200 bg-red-50 p-6 text-center shadow-sm md:p-8">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
          <AlertCircle className="h-6 w-6 text-red-600" />
        </div>
        <p className="text-lg font-medium text-red-700">{message}</p>
        <p className="mt-2 text-sm text-red-600">
          Something went wrong during the analysis.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Button onClick={onRetry} disabled={retrying} className="w-full">
            {retrying ? <Spinner /> : null}
            {retrying ? "Retrying…" : "Retry Analysis"}
          </Button>
          <Link
            href="/"
            className="text-sm font-medium text-red-700 underline hover:text-red-900"
          >
            Back to home
          </Link>
        </div>
        {retryError && (
          <p className="mt-4 rounded-lg bg-red-100 p-3 text-sm text-red-600" role="alert">
            {retryError}
          </p>
        )}
      </div>
    </Container>
  );
}
