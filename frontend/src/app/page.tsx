"use client";
import React from "react";
import UploadCard from "../components/UploadCard";
import ProgressPanel from "../components/ProgressPanel";
import { useRanking } from "../hooks/useRanking";

export default function DashboardPage() {
  const {
    jdFile,
    setJdFile,
    candidatesFile,
    setCandidatesFile,
    startRanking,
    status,
    progressMessages,
    isRunning,
  } = useRanking();

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <UploadCard
          title="Job Description"
          accepted={[".txt", ".docx"]}
          file={jdFile}
          onFile={setJdFile}
        />

        <UploadCard
          title="Candidates Dataset"
          accepted={[".jsonl", ".csv"]}
          file={candidatesFile}
          onFile={setCandidatesFile}
        />
      </div>

      <div className="flex items-center space-x-4">
        <button
          disabled={!jdFile || !candidatesFile || isRunning}
          onClick={() => startRanking()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md shadow hover:bg-indigo-700 disabled:opacity-50"
        >
          Run Ranking
        </button>
        <a href="/results" className="text-sm text-gray-600 hover:underline">
          View latest results
        </a>
      </div>

      <ProgressPanel
        status={status}
        isRunning={isRunning}
        messages={progressMessages}
      />
    </div>
  );
}
