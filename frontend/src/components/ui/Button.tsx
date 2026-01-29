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
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--link)]/30 focus-visible:ring-offset-0 disabled:opacity-60 disabled:pointer-events-none";
const primary =
  "bg-[var(--link)] text-white hover:bg-[#085ec7] border border-[var(--border)] shadow-[var(--shadow)] h-10 px-4 text-sm active:bg-[#0756b3]";
const secondary =
  "border border-[var(--border)] bg-[var(--surface)] text-[var(--muted)] hover:bg-[var(--surface-2)] h-10 px-4 text-sm";

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
