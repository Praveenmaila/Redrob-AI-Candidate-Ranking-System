"use client";
import React from "react";
import { Button } from "./shadcn";

interface Props {
  row: any | null;
  onClose: () => void;
}

export default function CandidateModal({ row, onClose }: Props) {
  if (!row) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-md shadow-lg w-full max-w-2xl p-6">
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-semibold">Candidate Details</h3>
          <Button onClick={onClose} variant="ghost">
            Close
          </Button>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-500">Candidate ID</div>
            <div className="font-medium">
              {row.candidate_id || row["candidate_id"]}
            </div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Score</div>
            <div className="font-medium">{row.score}</div>
          </div>

          <div className="md:col-span-2">
            <div className="text-sm text-gray-500">Reasoning</div>
            <div className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
              {row.reasoning || row.Reason}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
