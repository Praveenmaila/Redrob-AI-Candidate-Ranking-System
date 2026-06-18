"use client";
import React from "react";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
  as?: React.ElementType;
  id?: string;
}

export default function GlassCard({
  children,
  className = "",
  hover = false,
  gradient = false,
  as: Component = "div",
  id,
}: GlassCardProps) {
  return (
    <Component
      id={id}
      className={`
        rounded-2xl border transition-all duration-300
        bg-white/70 dark:bg-surface-800/70
        backdrop-blur-xl
        border-white/20 dark:border-surface-800/50
        shadow-[var(--shadow-md)]
        ${hover ? "hover:shadow-[var(--shadow-lg)] hover:-translate-y-1 hover:border-brand-300/30 dark:hover:border-brand-500/30" : ""}
        ${gradient ? "gradient-border" : ""}
        ${className}
      `}
    >
      {children}
    </Component>
  );
}
