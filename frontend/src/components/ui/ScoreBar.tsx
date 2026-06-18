"use client";
import React from "react";

interface ScoreBarProps {
  score: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
}

export default function ScoreBar({ score, max = 1, className = "", showLabel = true }: ScoreBarProps) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  // Color interpolation: red(0%) → amber(50%) → emerald(80%+)
  let color = "from-red-500 to-orange-500";
  if (pct >= 80) color = "from-emerald-500 to-green-400";
  else if (pct >= 60) color = "from-brand-500 to-violet-400";
  else if (pct >= 40) color = "from-amber-500 to-yellow-400";

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-2 rounded-full bg-gray-200 dark:bg-surface-800 overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-medium text-[var(--text-secondary)] w-12 text-right tabular-nums">
          {score.toFixed(4)}
        </span>
      )}
    </div>
  );
}
