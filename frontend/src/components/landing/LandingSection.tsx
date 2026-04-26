import type { ReactNode } from "react";
import { Container } from "@/components/layout/Container";

type Bg = "bg" | "soft";

interface LandingSectionProps {
  id?: string;
  bg?: Bg;
  className?: string;
  children: ReactNode;
}

/**
 * Landing-page section primitive. Enforces the page-wide rules:
 *  - 96px vertical padding (py-24)
 *  - Wide container (1200px max)
 *  - 1px top border for rhythm
 *
 * Pages outside the landing flow keep using CenteredSection.
 */
export function LandingSection({
  id,
  bg = "bg",
  className = "",
  children,
}: LandingSectionProps) {
  const bgClass =
    bg === "soft" ? "bg-[var(--surface-soft)]" : "bg-[var(--bg)]";
  return (
    <section
      id={id}
      className={`scroll-mt-20 border-t border-[var(--border)] py-24 ${bgClass} ${className}`}
    >
      <Container variant="wide">{children}</Container>
    </section>
  );
}
