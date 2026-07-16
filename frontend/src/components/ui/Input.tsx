import { type InputHTMLAttributes, forwardRef, useId } from "react";

import { clsx } from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ invalid = false, className, ...rest }, ref) => (
    <input
      ref={ref}
      className={clsx(
        "w-full rounded-md border bg-surface px-3 py-2.5 text-sm text-ink",
        "placeholder:text-slate-400",
        "focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/30",
        "disabled:cursor-not-allowed disabled:bg-paper",
        invalid ? "border-status-failed" : "border-line",
        className
      )}
      {...rest}
    />
  )
);

Input.displayName = "Input";

interface FormFieldProps {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  children: (id: string) => React.ReactNode;
}

/** Label + input + inline error, wired with a stable id for accessibility. */
export function FormField({ label, error, hint, children }: FormFieldProps) {
  const id = useId();
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children(id)}
      {error ? (
        <p className="text-sm text-status-failed">{error}</p>
      ) : hint ? (
        <p className="text-sm text-slate-400">{hint}</p>
      ) : null}
    </div>
  );
}
