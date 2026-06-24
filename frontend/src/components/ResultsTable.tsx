"use client";
import React, { useMemo, useState } from "react";
import { Button } from "./shadcn";
import GlassCard from "./ui/GlassCard";
import ScoreBar from "./ui/ScoreBar";
import Badge from "./ui/Badge";
import { Search, ChevronLeft, ChevronRight, ArrowUpDown, User } from "lucide-react";
import type { CandidateRow } from "../types";

interface Props {
  rows: CandidateRow[];
  onRowClick?: (r: CandidateRow) => void;
}

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Badge variant="gold">#1</Badge>;
  if (rank === 2) return <Badge variant="silver">#2</Badge>;
  if (rank === 3) return <Badge variant="bronze">#3</Badge>;
  if (rank <= 10)
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-brand-50 dark:bg-brand-950/30 text-brand-600 dark:text-brand-400 text-xs font-bold">
        {rank}
      </span>
    );
  return (
    <span className="text-sm text-[var(--text-muted)] font-medium tabular-nums">{rank}</span>
  );
}

function MiniBar({ pct, color }: { pct: number; color: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 h-1.5 rounded-full bg-surface-100 dark:bg-surface-800 overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-500`}
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>
      <span className="text-[10px] text-[var(--text-muted)] tabular-nums w-7 text-right">{pct}%</span>
    </div>
  );
}

export default function ResultsTable({ rows, onRowClick }: Props) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>({
    key: "rank",
    dir: "asc",
  });
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let out: CandidateRow[] = rows;
    if (q) {
      out = out.filter(
        (r) =>
          r.candidate_id?.toLowerCase().includes(q) ||
          r.title?.toLowerCase().includes(q) ||
          r.reasoning?.toLowerCase().includes(q)
      );
    }
    if (sort) {
      out = [...out].sort((a, b) => {
        const av = (a as any)[sort.key];
        const bv = (b as any)[sort.key];
        if (!isNaN(Number(av)) && !isNaN(Number(bv))) {
          return sort.dir === "asc" ? Number(av) - Number(bv) : Number(bv) - Number(av);
        }
        return sort.dir === "asc"
          ? String(av).localeCompare(String(bv))
          : String(bv).localeCompare(String(av));
      });
    }
    return out;
  }, [rows, query, sort]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageRows = filtered.slice(page * pageSize, page * pageSize + pageSize);

  function toggleSort(key: string) {
    if (!sort || sort.key !== key) setSort({ key, dir: "desc" });
    else setSort({ key, dir: sort.dir === "asc" ? "desc" : "asc" });
  }

  function SortHeader({ label, sortKey }: { label: string; sortKey: string }) {
    const isActive = sort?.key === sortKey;
    return (
      <th
        className="px-3 py-3 cursor-pointer select-none group whitespace-nowrap"
        onClick={() => toggleSort(sortKey)}
      >
        <div className="flex items-center gap-1">
          <span>{label}</span>
          <ArrowUpDown
            className={`w-3 h-3 transition-opacity ${
              isActive ? "opacity-100 text-brand-500" : "opacity-0 group-hover:opacity-50"
            }`}
          />
        </div>
      </th>
    );
  }

  return (
    <GlassCard className="p-0 overflow-hidden" id="results-table">
      {/* Toolbar */}
      <div className="px-5 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[var(--border-color)]">
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="Search candidates..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-[var(--border-color)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 transition-all"
            id="results-search"
          />
        </div>
        <div className="flex items-center gap-3 text-sm text-[var(--text-muted)]">
          <span className="tabular-nums">
            {filtered.length} candidate{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full table-auto border-collapse" id="candidates-table">
          <thead className="sticky-header">
            <tr className="text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider border-b border-[var(--border-color)]">
              <SortHeader label="Rank" sortKey="rank" />
              <SortHeader label="Candidate" sortKey="candidate_id" />
              <SortHeader label="Score" sortKey="score" />
              <th className="px-3 py-3 hidden lg:table-cell">Semantic</th>
              <th className="px-3 py-3 hidden lg:table-cell">Skills</th>
              <th className="px-3 py-3 hidden lg:table-cell">Experience</th>
              <th className="px-3 py-3 hidden md:table-cell">Strengths</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((r, i) => (
              <tr
                key={r.candidate_id || i}
                className="table-row-hover cursor-pointer border-b border-[var(--border-color)] last:border-b-0"
                onClick={() => onRowClick && onRowClick(r)}
              >
                {/* Rank */}
                <td className="px-3 py-3">
                  <RankBadge rank={r.rank} />
                </td>

                {/* Candidate info */}
                <td className="px-3 py-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500/10 to-violet-500/10 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-brand-500" />
                    </div>
                    <div>
                      <div className="text-sm font-medium truncate max-w-[140px]">
                        {r.title || "Candidate"}
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] font-mono">
                        {r.candidate_id}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Score */}
                <td className="px-3 py-3 w-36">
                  <ScoreBar score={r.score} max={1} />
                </td>

                {/* Semantic Match */}
                <td className="px-3 py-3 hidden lg:table-cell">
                  <MiniBar pct={r.semantic_match_pct || 0} color="from-blue-500 to-cyan-500" />
                </td>

                {/* Skill Match */}
                <td className="px-3 py-3 hidden lg:table-cell">
                  <MiniBar pct={r.skill_match_pct || 0} color="from-emerald-500 to-green-500" />
                </td>

                {/* Experience */}
                <td className="px-3 py-3 hidden lg:table-cell">
                  <MiniBar pct={r.experience_match_pct || 0} color="from-amber-500 to-orange-500" />
                </td>

                {/* Strengths */}
                <td className="px-3 py-3 hidden md:table-cell">
                  <div className="flex flex-wrap gap-1 max-w-[200px]">
                    {(r.key_strengths || []).slice(0, 2).map((s, j) => (
                      <span
                        key={j}
                        className="inline-flex px-1.5 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 text-[10px] font-medium whitespace-nowrap"
                      >
                        {s}
                      </span>
                    ))}
                    {(r.key_strengths || []).length > 2 && (
                      <span className="text-[10px] text-[var(--text-muted)]">
                        +{(r.key_strengths || []).length - 2}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-5 py-3 flex items-center justify-between border-t border-[var(--border-color)]">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            leftIcon={<ChevronLeft className="w-3 h-3" />}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount - 1}
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            rightIcon={<ChevronRight className="w-3 h-3" />}
          >
            Next
          </Button>
        </div>
        <span className="text-xs text-[var(--text-muted)] tabular-nums">
          Page {page + 1} of {pageCount}
        </span>
      </div>
    </GlassCard>
  );
}
