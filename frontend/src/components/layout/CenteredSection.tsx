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
      className={`py-14 md:py-16 lg:py-20 ${className}`}
    >
      {children}
    </section>
  );
}
