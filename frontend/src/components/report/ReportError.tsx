"use client";

import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

function Spinner() {
  return (
    <div
      className="h-4 w-4 shrink-0 rounded-full border-2 border-white/40 border-t-white animate-spin"
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
    <Card className="mx-4 my-6 max-w-xl border-[#ffcecb] bg-[#ffebe9] p-6 md:mx-0">
      <div className="flex flex-col items-center text-center">
        <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-[#ffcecb] bg-[#ffebe9]">
          <AlertCircle className="h-5 w-5 text-[#cf222e]" />
        </div>
        <p className="text-sm font-medium text-[#cf222e]" role="alert">{message}</p>
        <p className="mt-1 text-xs text-[#cf222e]">
          Something went wrong during the analysis.
        </p>
        <div className="mt-4 flex flex-col gap-2">
          <Button onClick={onRetry} disabled={retrying} className="w-full">
            {retrying ? <Spinner /> : null}
            {retrying ? "Retrying…" : "Retry Analysis"}
          </Button>
          <Link
            href="/"
            className="text-xs font-medium text-[#0969da] underline hover:text-[#085ec7]"
          >
            Back to home
          </Link>
        </div>
        {retryError && (
          <p className="mt-3 rounded-md border border-[#ffcecb] bg-[#ffebe9] p-2 text-xs text-[#cf222e]" role="alert">
            {retryError}
          </p>
        )}
      </div>
    </Card>
  );
}
