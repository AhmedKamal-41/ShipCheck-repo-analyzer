import { Check, X, AlertCircle } from "lucide-react";

type Status = "pass" | "warn" | "fail";

const config: Record<
  Status,
  { className: string; icon: typeof Check }
> = {
  pass: { className: "bg-green-100 text-green-800", icon: Check },
  warn: { className: "bg-amber-100 text-amber-800", icon: AlertCircle },
  fail: { className: "bg-red-100 text-red-800", icon: X },
};

interface BadgeProps {
  status: Status;
  children: React.ReactNode;
}

export function Badge({ status, children }: BadgeProps) {
  const { className, icon: Icon } = config[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium ${className}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {children}
    </span>
  );
}
