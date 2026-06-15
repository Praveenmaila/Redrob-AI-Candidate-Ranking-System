"use client";
import React, { useMemo, useState } from "react";
import { Button } from "./shadcn";

interface Props {
  rows: any[];
  onRowClick?: (r: any) => void;
}

export default function ResultsTable({ rows, onRowClick }: Props) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(
    { key: "score", dir: "desc" },
  );
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let out = rows;
    if (q) {
      out = out.filter((r) =>
        Object.values(r).join(" ").toLowerCase().includes(q),
      );
    }
    if (sort) {
      out = [...out].sort((a, b) => {
        const av = a[sort.key];
        const bv = b[sort.key];
        if (!isNaN(Number(av)) && !isNaN(Number(bv))) {
          return sort.dir === "asc"
            ? Number(av) - Number(bv)
            : Number(bv) - Number(av);
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

  return (
    <div className="bg-white rounded shadow p-4">
      <div className="flex items-center justify-between mb-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
          className="border px-3 py-2 rounded w-60"
        />
        <div className="text-sm text-gray-600">Total: {rows.length}</div>
      </div>

      <table className="w-full table-auto border-collapse">
        <thead>
          <tr className="text-left text-sm text-gray-600">
            <th
              className="px-2 py-2 cursor-pointer"
              onClick={() => toggleSort("Rank")}
            >
              Rank
            </th>
            <th
              className="px-2 py-2 cursor-pointer"
              onClick={() => toggleSort("candidate_id")}
            >
              Candidate ID
            </th>
            <th
              className="px-2 py-2 cursor-pointer"
              onClick={() => toggleSort("score")}
            >
              Score
            </th>
            <th className="px-2 py-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {pageRows.map((r, i) => (
            <tr
              key={i}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => onRowClick && onRowClick(r)}
            >
              <td className="px-2 py-2">{r.rank || r.Rank || ""}</td>
              <td className="px-2 py-2">
                {r.candidate_id || r["candidate_id"] || ""}
              </td>
              <td className="px-2 py-2">{r.score}</td>
              <td className="px-2 py-2">{r.reasoning || r.Reason || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-4 flex items-center justify-between">
        <div>
          <Button
            variant="default"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="mr-2"
          >
            Previous
          </Button>
          <Button
            variant="default"
            disabled={page >= pageCount - 1}
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
          >
            Next
          </Button>
        </div>
        <div className="text-sm text-gray-600">
          Page {page + 1} / {pageCount}
        </div>
      </div>
    </div>
  );
}
