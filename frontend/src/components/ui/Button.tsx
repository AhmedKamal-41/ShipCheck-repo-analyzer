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
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-all duration-200 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-0 disabled:opacity-60 disabled:pointer-events-none disabled:hover:scale-100";
const primary =
  "bg-[var(--link)] text-white hover:bg-[#0860c4] hover:scale-[1.02] border border-[var(--border)] shadow-[var(--shadow)] h-10 px-4 text-sm active:bg-[#0756b3] active:scale-[0.99]";
const secondary =
  "border border-[var(--border)] bg-[var(--surface)] text-[var(--muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text)] h-10 px-4 text-sm";

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
