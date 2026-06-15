"use client";
import React from "react";
import UploadCard from "../components/UploadCard";
import ProgressPanel from "../components/ProgressPanel";
import { useRanking } from "../hooks/useRanking";
import { Button } from "../components/shadcn";

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
    backendUrl,
    lastError,
    retry,
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
        <Button
          variant="primary"
          disabled={!jdFile || !candidatesFile || isRunning}
          onClick={() => startRanking()}
        >
          Run Ranking
        </Button>
        <a href="/results" className="text-sm text-gray-600 hover:underline">
          View latest results
        </a>
      </div>

      <ProgressPanel
        status={status}
        isRunning={isRunning}
        messages={progressMessages}
        backendUrl={backendUrl}
        lastError={lastError}
        onRetry={retry}
      />
    </div>
  );
}
