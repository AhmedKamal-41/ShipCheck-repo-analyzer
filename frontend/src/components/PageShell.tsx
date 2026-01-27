import type { ReactNode } from "react";

interface PageShellProps {
  children: ReactNode;
  className?: string;
  maxWidth?: "md" | "lg" | "xl" | "4xl";
}

const maxWidthClass = {
  md: "max-w-2xl",
  lg: "max-w-3xl",
  xl: "max-w-4xl",
  "4xl": "max-w-5xl",
} as const;

export function PageShell({
  children,
  className = "",
  maxWidth = "xl",
}: PageShellProps) {
  return (
    <div
      className={`mx-auto w-full px-6 ${maxWidthClass[maxWidth]} ${className}`}
    >
      {children}
    </div>
  );
}
