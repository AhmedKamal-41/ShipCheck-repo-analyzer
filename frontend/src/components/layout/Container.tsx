import type { ReactNode } from "react";

interface ContainerProps {
  children: ReactNode;
  className?: string;
  /** "narrow" for sidebar / constrained width; "wide" (1200px) for landing sections */
  variant?: "default" | "narrow" | "wide";
}

export function Container({
  children,
  className = "",
  variant = "default",
}: ContainerProps) {
  const maxWidth =
    variant === "narrow"
      ? "max-w-2xl"
      : variant === "wide"
        ? "max-w-[1200px]"
        : "max-w-6xl";
  return (
    <div
      className={`mx-auto w-full ${maxWidth} px-4 sm:px-6 lg:px-8 ${className}`}
    >
      {children}
    </div>
  );
}
