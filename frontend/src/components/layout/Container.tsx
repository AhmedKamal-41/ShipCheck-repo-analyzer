import type { ReactNode } from "react";

interface ContainerProps {
  children: ReactNode;
  className?: string;
  /** "narrow" for sidebar / constrained width */
  variant?: "default" | "narrow";
}

export function Container({
  children,
  className = "",
  variant = "default",
}: ContainerProps) {
  const maxWidth = variant === "narrow" ? "max-w-2xl" : "max-w-6xl";
  return (
    <div
      className={`mx-auto w-full ${maxWidth} px-4 sm:px-6 lg:px-8 ${className}`}
    >
      {children}
    </div>
  );
}
