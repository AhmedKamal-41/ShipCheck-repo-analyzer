import type { ReactNode } from "react";

interface CenteredSectionProps {
  children: ReactNode;
  id?: string;
  className?: string;
}

export function CenteredSection({
  children,
  id,
  className = "",
}: CenteredSectionProps) {
  return (
    <section
      id={id}
      className={`border-t border-[var(--border)] py-10 sm:py-12 lg:py-16 ${className}`}
    >
      {children}
    </section>
  );
}
