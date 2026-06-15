"use client";
import React, { useEffect, useState } from "react";
import { api } from "../../lib/api";
import ResultsTable from "../../components/ResultsTable";
import CandidateModal from "../../components/CandidateModal";

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
      <h2 className="text-xl font-semibold mb-4">Top 100 Candidates</h2>
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

