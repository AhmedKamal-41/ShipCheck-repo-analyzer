import { Check, AlertCircle, X } from "lucide-react";

type Status = "pass" | "warn" | "fail";

const config: Record<
  Status,
  { bg: string; text: string; icon: typeof Check }
> = {
  pass: {
    bg: "bg-green-100",
    text: "text-green-800",
    icon: Check,
  },
  warn: {
    bg: "bg-amber-100",
    text: "text-amber-800",
    icon: AlertCircle,
  },
  fail: {
    bg: "bg-red-100",
    text: "text-red-800",
    icon: X,
  },
};

interface StatusPillProps {
  status: Status;
  className?: string;
}

export function StatusPill({ status, className = "" }: StatusPillProps) {
  const { bg, text, icon: Icon } = config[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium uppercase ${bg} ${text} ${className}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {status}
    </span>
  );
}
