"use client";
import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import ResultsTable from "../../components/ResultsTable";
import CandidateModal from "../../components/CandidateModal";
import GlassCard from "../../components/ui/GlassCard";
import SkeletonLoader from "../../components/ui/SkeletonLoader";
import { Button } from "../../components/shadcn";
import {
  Download,
  Trophy,
  TrendingUp,
  Users,
  BarChart3,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import type { CandidateRow, ResultsMetadata } from "../../types";

export default function ResultsPage() {
  const [rows, setRows] = useState<CandidateRow[]>([]);
  const [metadata, setMetadata] = useState<ResultsMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CandidateRow | null>(null);

  useEffect(() => {
    async function fetchResults() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get("/results");
        const data = res.data as { candidates: CandidateRow[]; metadata: ResultsMetadata };
        setRows(data.candidates || []);
        setMetadata(data.metadata || null);
      } catch (e: any) {
        // Fallback to CSV parsing if /results endpoint not available
        try {
          const res = await api.get("/download", { responseType: "text" });
          const csv = res.data as string;
          const parsed = parseCsv(csv);
          setRows(parsed);
        } catch {
          setError("No results available. Run the ranking pipeline first.");
        }
      } finally {
        setLoading(false);
      }
    }
    fetchResults();
  }, []);

  function parseCsv(csv: string): CandidateRow[] {
    const lines = csv.trim().split("\n");
    if (lines.length <= 1) return [];
    return lines.slice(1).map((l, idx) => {
      const parts = l.split(",");
      return {
        candidate_id: parts[0] || "",
        rank: parseInt(parts[1]) || idx + 1,
        score: parseFloat(parts[2]) || 0,
        reasoning: parts.slice(3).join(",").replace(/^"|"$/g, ""),
        semantic_match_pct: 0,
        skill_match_pct: 0,
        experience_match_pct: 0,
        key_strengths: [],
        concerns: [],
        title: "Candidate",
        years_experience: 0,
      };
    });
  }

  async function handleDownload() {
    try {
      const response = await api.get("/download", { responseType: "blob" });
      const blob = response.data as Blob;
      if ("showSaveFilePicker" in window) {
        const handle = await (window as any).showSaveFilePicker({
          suggestedName: "submission_top100.csv",
          types: [{ description: "CSV File", accept: { "text/csv": [".csv"] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        return;
      }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "submission_top100.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      if (e.name !== "AbortError") console.error("Download failed", e);
    }
  }

  return (
    <div className="page-enter">
      {/* Page Header */}
      <section className="mb-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 text-xs font-medium mb-3 border border-brand-200/50 dark:border-brand-800/30">
              <Sparkles className="w-3 h-3" aria-hidden="true" />
              AI-Ranked Results
            </div>
            <h1 className="text-3xl md:text-4xl font-bold">
              Top <span className="gradient-text">100</span> Candidates
            </h1>
            <p className="text-[var(--text-secondary)] mt-2 text-sm">
              Ranked by semantic matching, skill alignment, and experience relevance.
            </p>
          </div>
          <Button
            variant="gradient"
            size="lg"
            onClick={handleDownload}
            leftIcon={<Download className="w-4 h-4" />}
            disabled={rows.length === 0}
            id="download-csv-btn"
          >
            Download CSV
          </Button>
        </div>
      </section>

      {/* Stats Bar */}
      {metadata && !loading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <GlassCard className="p-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center mx-auto mb-2 shadow-lg">
              <Users className="w-5 h-5 text-white" />
            </div>
            <div className="text-xl font-bold tabular-nums">{metadata.total_candidates}</div>
            <div className="text-xs text-[var(--text-muted)]">Candidates Ranked</div>
          </GlassCard>
          <GlassCard className="p-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center mx-auto mb-2 shadow-lg">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <div className="text-xl font-bold tabular-nums">{metadata.max_score.toFixed(4)}</div>
            <div className="text-xs text-[var(--text-muted)]">Top Score</div>
          </GlassCard>
          <GlassCard className="p-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mx-auto mb-2 shadow-lg">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div className="text-xl font-bold tabular-nums">{metadata.avg_score.toFixed(4)}</div>
            <div className="text-xs text-[var(--text-muted)]">Average Score</div>
          </GlassCard>
          <GlassCard className="p-4 text-center">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-pink-500 flex items-center justify-center mx-auto mb-2 shadow-lg">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div className="text-xl font-bold tabular-nums">
              {(metadata.max_score - metadata.min_score).toFixed(4)}
            </div>
            <div className="text-xs text-[var(--text-muted)]">Score Range</div>
          </GlassCard>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <GlassCard className="p-6">
          <SkeletonLoader rows={8} />
        </GlassCard>
      ) : error ? (
        <GlassCard className="p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-amber-50 dark:bg-amber-950/30 flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-amber-500" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
          <p className="text-sm text-[var(--text-muted)] max-w-md mx-auto mb-6">{error}</p>
          <Button variant="primary" onClick={() => (window.location.href = "/")}>
            Go to Dashboard
          </Button>
        </GlassCard>
      ) : (
        <ResultsTable rows={rows} onRowClick={(r) => setSelected(r as CandidateRow)} />
      )}

      <CandidateModal row={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
