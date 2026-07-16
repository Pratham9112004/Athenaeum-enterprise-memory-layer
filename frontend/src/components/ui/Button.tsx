import { type ButtonHTMLAttributes, forwardRef } from "react";

import { clsx } from "clsx";

import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  fullWidth?: boolean;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-brand text-white hover:bg-brand-700 active:bg-brand-700 disabled:bg-brand/50",
  secondary:
    "bg-surface text-ink border border-line hover:bg-paper disabled:opacity-50",
  ghost: "text-slate-500 hover:text-ink hover:bg-paper disabled:opacity-50",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", loading = false, fullWidth = false, className, children, disabled, ...rest },
    ref
  ) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2.5",
        "text-sm font-semibold transition-colors",
        "disabled:cursor-not-allowed",
        variants[variant],
        fullWidth && "w-full",
        className
      )}
      {...rest}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
);

Button.displayName = "Button";
