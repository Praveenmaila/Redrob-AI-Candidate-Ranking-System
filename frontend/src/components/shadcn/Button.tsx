"use client";
import React from "react";
import { Loader2 } from "lucide-react";

type ButtonVariant = "default" | "ghost" | "primary" | "gradient" | "danger" | "outline";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
};

const variantStyles: Record<ButtonVariant, string> = {
  default:
    "bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200 hover:bg-surface-200 dark:hover:bg-surface-700 border border-[var(--border-color)]",
  ghost:
    "bg-transparent text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/30",
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 shadow-lg shadow-brand-500/25 hover:shadow-xl hover:shadow-brand-500/30",
  gradient:
    "bg-gradient-to-r from-brand-600 to-violet-600 text-white shadow-lg shadow-brand-500/25 hover:shadow-xl hover:shadow-brand-500/30 hover:-translate-y-0.5",
  danger:
    "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-500/25",
  outline:
    "bg-transparent border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-surface-100 dark:hover:bg-surface-800",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs rounded-lg gap-1.5",
  md: "px-4 py-2 text-sm rounded-xl gap-2",
  lg: "px-6 py-3 text-base rounded-xl gap-2.5",
};

export default function Button({
  variant = "default",
  size = "md",
  isLoading = false,
  leftIcon,
  rightIcon,
  className = "",
  children,
  disabled,
  type,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || isLoading;

  return (
    <button
      // Default to type="button" so the element is never treated as a
      // form-submit target. Without this, browser password managers and
      // some extensions inject `fdprocessedid` and other attributes that
      // differ between SSR and the client, breaking React hydration.
      // `suppressHydrationWarning` absorbs any such attribute injection
      // (e.g. fdprocessedid, data-1p-ignore) that happens between the
      // server render and the client hydration.
      type={type ?? "button"}
      suppressHydrationWarning
      className={`
        inline-flex items-center justify-center font-medium
        transition-all duration-200 ease-out
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${isDisabled ? "opacity-50 cursor-not-allowed pointer-events-none" : "cursor-pointer"}
        ${className}
      `}
      disabled={isDisabled}
      aria-busy={isLoading}
      {...rest}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
      ) : leftIcon ? (
        <span aria-hidden="true">{leftIcon}</span>
      ) : null}
      {children}
      {rightIcon && !isLoading && <span aria-hidden="true">{rightIcon}</span>}
    </button>
  );
}
