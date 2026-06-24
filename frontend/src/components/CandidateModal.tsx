"use client";
import React from "react";
import Modal from "./shadcn/Modal";
import ScoreBar from "./ui/ScoreBar";
import Badge from "./ui/Badge";
import {
  User,
  Briefcase,
  Target,
  Brain,
  TrendingUp,
  AlertTriangle,
  Sparkles,
} from "lucide-react";
import type { CandidateRow } from "../types";

interface Props {
  row: CandidateRow | null;
  onClose: () => void;
}

function ScoreGauge({ value, label, icon: Icon, color }: {
  value: number;
  label: string;
  icon: React.ElementType;
  color: string;
}) {
  const pct = Math.min(100, Math.max(0, value));
  const circumference = 2 * Math.PI * 32;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 72 72">
          <circle
            cx="36"
            cy="36"
            r="32"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            className="text-surface-100 dark:text-surface-800"
          />
          <circle
            cx="36"
            cy="36"
            r="32"
            fill="none"
            strokeWidth="4"
            strokeLinecap="round"
            className={color}
            style={{
              strokeDasharray: circumference,
              strokeDashoffset: offset,
              transition: "stroke-dashoffset 0.8s ease-out",
            }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold tabular-nums">{pct}%</span>
        </div>
      </div>
      <div className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
        <Icon className="w-3 h-3" />
        <span>{label}</span>
      </div>
    </div>
  );
}

export default function CandidateModal({ row, onClose }: Props) {
  if (!row) return null;

  return (
    <Modal title="Candidate Details" onClose={onClose} size="lg">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-lg shadow-brand-500/20 shrink-0">
            <User className="w-7 h-7 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-xl font-bold truncate">{row.title || "Candidate"}</h4>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-sm text-[var(--text-muted)] font-mono">{row.candidate_id}</span>
              <Badge variant={row.rank <= 3 ? "gold" : row.rank <= 10 ? "info" : "success"}>
                Rank #{row.rank}
              </Badge>
            </div>
          </div>
        </div>

        {/* Score overview */}
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-brand-500" />
            <h5 className="text-sm font-semibold">Overall Score</h5>
          </div>
          <div className="mb-4">
            <ScoreBar score={row.score} max={1} />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <ScoreGauge
              value={row.semantic_match_pct || 0}
              label="Semantic"
              icon={Brain}
              color="stroke-blue-500"
            />
            <ScoreGauge
              value={row.skill_match_pct || 0}
              label="Skills"
              icon={Target}
              color="stroke-emerald-500"
            />
            <ScoreGauge
              value={row.experience_match_pct || 0}
              label="Experience"
              icon={Briefcase}
              color="stroke-amber-500"
            />
          </div>
        </div>

        {/* Details grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Experience */}
          <div className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Briefcase className="w-4 h-4 text-amber-500" />
              <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                Experience
              </span>
            </div>
            <p className="text-lg font-semibold">
              {row.years_experience ? `${row.years_experience} years` : "N/A"}
            </p>
          </div>

          {/* Final Score */}
          <div className="glass rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-brand-500" />
              <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                Final Score
              </span>
            </div>
            <p className="text-lg font-semibold tabular-nums">{row.score.toFixed(4)}</p>
          </div>
        </div>

        {/* Key Strengths */}
        {row.key_strengths && row.key_strengths.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-emerald-500" />
              <h5 className="text-sm font-semibold">Key Strengths</h5>
            </div>
            <div className="flex flex-wrap gap-2">
              {row.key_strengths.map((s, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 text-sm font-medium border border-emerald-200/50 dark:border-emerald-800/30"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Concerns */}
        {row.concerns && row.concerns.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <h5 className="text-sm font-semibold">Concerns</h5>
            </div>
            <div className="flex flex-wrap gap-2">
              {row.concerns.map((c, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/20 text-amber-700 dark:text-amber-400 text-sm font-medium border border-amber-200/50 dark:border-amber-800/30"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Reasoning */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-brand-500" />
            <h5 className="text-sm font-semibold">AI Reasoning</h5>
          </div>
          <div className="glass rounded-xl p-4">
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {row.reasoning || "No reasoning available."}
            </p>
          </div>
        </div>
      </div>
    </Modal>
  );
}
