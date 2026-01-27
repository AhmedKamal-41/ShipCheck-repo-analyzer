import type { ReactNode } from "react";

interface StepCardProps {
  step: number;
  icon: ReactNode;
  title: string;
  description: string;
}

export function StepCard({ step, icon, title, description }: StepCardProps) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
          {icon}
        </span>
        <span className="text-sm font-semibold text-slate-400">
          Step {step}
        </span>
      </div>
      <h3 className="mb-2 text-lg font-semibold text-slate-900">{title}</h3>
      <p className="text-sm text-slate-600">{description}</p>
    </div>
  );
}
