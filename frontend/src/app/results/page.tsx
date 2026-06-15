"use client";
import React, { useEffect, useState } from "react";
import axios from "axios";
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
        const res = await axios.get("/download", { responseType: "text" });
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
      const cols = l.split(",");
      const obj: any = {};
      headers.forEach((h, i) => (obj[h] = cols[i]));
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
