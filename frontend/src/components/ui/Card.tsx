import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white/80 p-6 shadow-sm backdrop-blur transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 lg:p-7 ${className}`}
    >
      {children}
    </div>
  );
}
