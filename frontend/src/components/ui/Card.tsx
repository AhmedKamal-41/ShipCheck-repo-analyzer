import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow)] transition-shadow hover:border-[#8c959f] hover:shadow-md lg:p-6 ${className}`}
    >
      {children}
    </div>
  );
}
