"use client";
import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import ResultsTable from "../../components/ResultsTable";
import CandidateModal from "../../components/CandidateModal";
import { Button } from "../../components/shadcn";

export default function ResultsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<any | null>(null);

  useEffect(() => {
    async function fetchCsv() {
      setLoading(true);
      try {
        const res = await api.get("/download", { responseType: "text" });
        const csv = res.data as string;
        const parsed = parseCsv(csv);
        setRows(parsed);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchCsv();
  }, []);

  function parseCsv(csv: string) {
    const lines = csv.trim().split("\n");
    if (lines.length <= 1) return [];
    const headers = lines[0].split(",").map((h) => h.trim());
    return lines.slice(1).map((l) => {
      // Split only on first 3 commas; the rest is reasoning (may contain commas)
      const parts = l.split(",");
      const obj: any = {};
      obj[headers[0]] = parts[0]; // candidate_id
      obj[headers[1]] = parts[1]; // rank
      obj[headers[2]] = parts[2]; // score
      obj[headers[3]] = parts.slice(3).join(","); // reasoning
      return obj;
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Top 100 Candidates</h2>
        <Button variant="primary" onClick={async () => {
          try {
            const response = await fetch("/submission_top100.csv");
            const blob = await response.blob();

            // Use native Save As dialog - guarantees correct filename
            if ("showSaveFilePicker" in window) {
              const handle = await (window as any).showSaveFilePicker({
                suggestedName: "submission_top100.csv",
                types: [
                  {
                    description: "CSV File",
                    accept: { "text/csv": [".csv"] },
                  },
                ],
              });
              const writable = await handle.createWritable();
              await writable.write(blob);
              await writable.close();
              return;
            }

            // Fallback for browsers without showSaveFilePicker
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
        }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download CSV
        </Button>
      </div>
      {loading ? (
        <div className="p-6 bg-white rounded shadow text-center">
          Loading results...
        </div>
      ) : (
        <ResultsTable rows={rows} onRowClick={(r) => setSelected(r)} />
      )}

      <CandidateModal row={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

