"use client";
import React from "react";
import GlassCard from "./ui/GlassCard";
import Badge from "./ui/Badge";
import { Button } from "./shadcn";
import {
  Upload,
  Brain,
  Database,
  Cpu,
  Search,
  Trophy,
  FileDown,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RotateCcw,
} from "lucide-react";

const STAGE_CONFIG: Record<string, { icon: React.ElementType; color: string }> = {
  idle: { icon: Loader2, color: "from-surface-400 to-surface-500" },
  loading_model: { icon: Brain, color: "from-violet-500 to-purple-600" },
  loading_dataset: { icon: Database, color: "from-blue-500 to-cyan-500" },
  building_embeddings: { icon: Cpu, color: "from-amber-500 to-orange-500" },
  processing_jd: { icon: Upload, color: "from-brand-500 to-violet-500" },
  semantic_matching: { icon: Search, color: "from-emerald-500 to-green-500" },
  ranking: { icon: Trophy, color: "from-rose-500 to-pink-500" },
  exporting_results: { icon: FileDown, color: "from-brand-600 to-violet-600" },
  completed: { icon: CheckCircle2, color: "from-emerald-500 to-green-500" },
  error: { icon: AlertCircle, color: "from-red-500 to-rose-600" },
};

interface Props {
  status: string;
  isRunning: boolean;
  messages: string[];
  stage?: string;
  stageLabel?: string;
  progressPct?: number;
  candidatesProcessed?: number;
  lastError?: string | null;
  onRetry?: () => void;
}

export default function ProgressPanel({
  status,
  isRunning,
  stage = "idle",
  stageLabel,
  progressPct = 0,
  candidatesProcessed = 0,
  lastError,
  onRetry,
}: Props) {
  // Don't render when idle and no error
  if (!isRunning && !lastError && stage === "idle") return null;

  const config = STAGE_CONFIG[stage] || STAGE_CONFIG.idle;
  const StageIcon = config.icon;
  const isError = stage === "error" || !!lastError;
  const isComplete = stage === "completed" || status === "Completed";
  const pct = Math.max(0, Math.min(100, progressPct));

  const displayLabel =
    stageLabel || (isComplete ? "Completed" : isRunning ? "Processing..." : status || "Idle");

  return (
    <GlassCard className="mt-6 p-0 overflow-hidden" id="progress-panel">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl bg-gradient-to-br ${config.color} flex items-center justify-center shadow-lg ${
              isRunning ? "animate-pulse" : ""
            }`}
          >
            <StageIcon
              className={`w-5 h-5 text-white ${isRunning && stage !== "error" ? "animate-spin" : ""}`}
              style={isRunning && stage !== "error" ? { animationDuration: "2s" } : undefined}
            />
          </div>
          <div>
            <h3 className="font-semibold text-sm">{displayLabel}</h3>
            {candidatesProcessed > 0 && (
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                {candidatesProcessed.toLocaleString()} candidates processed
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isComplete && (
            <Badge variant="success" size="sm">
              Complete
            </Badge>
          )}
          {isRunning && !isError && (
            <Badge variant="info" size="sm">
              {pct}%
            </Badge>
          )}
          {isError && (
            <Badge variant="error" size="sm">
              Failed
            </Badge>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {(isRunning || isComplete) && !isError && (
        <div className="px-5 pb-3">
          <div className="h-2 rounded-full bg-surface-100 dark:bg-surface-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r ${config.color} ${
                isRunning ? "progress-bar-animated" : ""
              }`}
              style={{ width: `${pct}%` }}
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${displayLabel} progress`}
            />
          </div>
        </div>
      )}

      {/* Pipeline stages indicator */}
      {isRunning && (
        <div className="px-5 pb-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {Object.entries(STAGE_CONFIG)
              .filter(([key]) => !["idle", "error", "completed"].includes(key))
              .map(([key, cfg]) => {
                const Icon = cfg.icon;
                const isActive = key === stage;
                const stageOrder = Object.keys(STAGE_CONFIG).indexOf(key);
                const currentOrder = Object.keys(STAGE_CONFIG).indexOf(stage);
                const isDone = currentOrder > stageOrder;
                return (
                  <div
                    key={key}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-all duration-300 whitespace-nowrap ${
                      isActive
                        ? "bg-brand-50 dark:bg-brand-950/30 text-brand-600 dark:text-brand-400"
                        : isDone
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-[var(--text-muted)]"
                    }`}
                  >
                    <Icon className="w-3 h-3 shrink-0" />
                    {isActive && <span className="hidden sm:inline">{key.replace(/_/g, " ")}</span>}
                    {isDone && <CheckCircle2 className="w-3 h-3 text-emerald-500" />}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && lastError && (
        <div className="mx-5 mb-4 p-4 rounded-xl bg-red-50/50 dark:bg-red-950/20 border border-red-200/50 dark:border-red-800/30">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
                <span className="text-sm font-medium text-red-700 dark:text-red-400">
                  An error occurred
                </span>
              </div>
              <p className="text-xs text-red-600/80 dark:text-red-400/70 leading-relaxed line-clamp-3">
                {lastError.split("\n")[0]}
              </p>
            </div>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                leftIcon={<RotateCcw className="w-3 h-3" />}
                className="shrink-0 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30"
              >
                Retry
              </Button>
            )}
          </div>
        </div>
      )}
    </GlassCard>
  );
}
