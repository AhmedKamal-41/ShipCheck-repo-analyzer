import { Check, X, AlertCircle } from "lucide-react";

type Status = "pass" | "warn" | "fail";

const config: Record<
  Status,
  { className: string; icon: typeof Check }
> = {
  pass: {
    className: "bg-[#dafbe1] text-[#1f883d] border border-[#aceebb]",
    icon: Check,
  },
  warn: {
    className: "bg-[#fff8c5] text-[#9a6700] border border-[#f2e088]",
    icon: AlertCircle,
  },
  fail: {
    className: "bg-[#ffebe9] text-[#cf222e] border border-[#ffcecb]",
    icon: X,
  },
};

interface BadgeProps {
  status: Status;
  children: React.ReactNode;
}

export function Badge({ status, children }: BadgeProps) {
  const { className, icon: Icon } = config[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${className}`}
    >
      <Icon className="h-3 w-3 shrink-0" aria-hidden />
      {children}
    </span>
  );
}
