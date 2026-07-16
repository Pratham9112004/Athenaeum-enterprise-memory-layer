import { AlertCircle, CheckCircle2, Info } from "lucide-react";

import { clsx } from "clsx";

type Tone = "error" | "success" | "info";

const config: Record<Tone, { icon: typeof Info; classes: string }> = {
  error: {
    icon: AlertCircle,
    classes: "bg-status-failed/8 text-status-failed border-status-failed/25",
  },
  success: {
    icon: CheckCircle2,
    classes: "bg-brand/8 text-brand-700 border-brand/25",
  },
  info: {
    icon: Info,
    classes: "bg-slate-500/8 text-slate-500 border-slate-300/40",
  },
};

export function Alert({ tone = "info", children }: { tone?: Tone; children: React.ReactNode }) {
  const { icon: Icon, classes } = config[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={clsx(
        "flex items-start gap-2.5 rounded-md border px-3.5 py-3 text-sm",
        classes
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="leading-relaxed">{children}</div>
    </div>
  );
}
