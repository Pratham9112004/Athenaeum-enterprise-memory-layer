import { clsx } from "clsx";

export type Status = "uploaded" | "processing" | "ready" | "failed";

const labels: Record<Status, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

const dot: Record<Status, string> = {
  uploaded: "bg-status-uploaded",
  processing: "bg-status-processing",
  ready: "bg-status-ready",
  failed: "bg-status-failed",
};

const text: Record<Status, string> = {
  uploaded: "text-status-uploaded",
  processing: "text-status-processing",
  ready: "text-status-ready",
  failed: "text-status-failed",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border border-line",
        "bg-surface px-2.5 py-1 text-2xs font-medium uppercase tracking-wide",
        text[status]
      )}
    >
      <span
        className={clsx(
          "h-1.5 w-1.5 rounded-full",
          dot[status],
          status === "processing" && "animate-pulse"
        )}
      />
      {labels[status]}
    </span>
  );
}
