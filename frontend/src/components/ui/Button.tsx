import type { ReactNode } from "react";

interface ButtonProps {
  children: ReactNode;
  variant?: "primary" | "secondary";
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-xl font-medium shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:opacity-60 disabled:pointer-events-none";
const primary =
  "bg-accent text-white hover:bg-accent/90 h-11 px-5 sm:h-12 sm:px-6";
const secondary =
  "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 h-11 px-5 sm:h-12 sm:px-6";

export function Button({
  children,
  variant = "primary",
  type = "button",
  disabled,
  onClick,
  className = "",
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${base} ${variant === "primary" ? primary : secondary} ${className}`}
    >
      {children}
    </button>
  );
}
