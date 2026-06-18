"use client";
import React from "react";
import { Trophy, Medal, Award } from "lucide-react";

type BadgeVariant = "gold" | "silver" | "bronze" | "success" | "warning" | "error" | "info";

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  icon?: boolean;
}

const styles: Record<BadgeVariant, string> = {
  gold: "bg-gradient-to-r from-amber-400 to-yellow-500 text-amber-950 shadow-amber-200/50",
  silver: "bg-gradient-to-r from-slate-300 to-gray-400 text-slate-900 shadow-slate-200/50",
  bronze: "bg-gradient-to-r from-orange-400 to-amber-600 text-orange-950 shadow-orange-200/50",
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  error: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  info: "bg-brand-100 text-brand-800 dark:bg-brand-900/30 dark:text-brand-400",
};

const icons: Partial<Record<BadgeVariant, React.ReactNode>> = {
  gold: <Trophy className="w-3 h-3" />,
  silver: <Medal className="w-3 h-3" />,
  bronze: <Award className="w-3 h-3" />,
};

export default function Badge({ variant, children, className = "", icon = true }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold
        shadow-sm transition-all duration-200
        ${styles[variant]}
        ${className}
      `}
    >
      {icon && icons[variant]}
      {children}
    </span>
  );
}
