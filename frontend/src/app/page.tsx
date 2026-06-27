"use client";
import React from "react";
import HeroSection from "../components/dashboard/HeroSection";
import FeatureCards from "../components/dashboard/FeatureCards";
import StatsSection from "../components/dashboard/StatsSection";
import UploadCard from "../components/UploadCard";
import ProgressPanel from "../components/ProgressPanel";
import { useRanking } from "../hooks/useRanking";
import { Button } from "../components/shadcn";
import { Play, ArrowRight, Sparkles } from "lucide-react";
import GlassCard from "../components/ui/GlassCard";

export default function DashboardPage() {
  const {
    jdFile,
    setJdFile,
    datasetFile,
    setDatasetFile,
    datasets,
    selectedDataset,
    setSelectedDataset,
    uploadDataset,
    isUploadingDataset,
    startRanking,
    status,
    progressMessages,
    isRunning,
    lastError,
    retry,
    currentStage,
    stageLabel,
    progressPct,
    candidatesProcessed,
  } = useRanking();

  return (
    <div className="page-enter">
      {/* Hero */}
      <HeroSection />

      {/* Features */}
      <FeatureCards />

      {/* Stats */}
      <StatsSection />

      {/* Upload Section */}
      <section id="upload" className="py-16 md:py-20 scroll-mt-20" aria-labelledby="upload-heading">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 text-xs font-medium mb-4 border border-brand-200/50 dark:border-brand-800/30">
            <Sparkles className="w-3 h-3" aria-hidden="true" />
            Get Started
          </div>
          <h2 id="upload-heading" className="text-3xl md:text-4xl font-bold mb-4">
            Upload Your <span className="gradient-text">Data</span>
          </h2>
          <p className="text-[var(--text-secondary)] max-w-lg mx-auto">
            Provide a job description and candidate dataset to begin the AI-powered ranking process.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="space-y-4">
              <UploadCard
                title="Candidate Dataset"
                accepted={[".jsonl", ".csv"]}
                file={datasetFile}
                onFile={setDatasetFile}
              />
              <GlassCard className="p-4">
                <div className="flex flex-col gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[var(--text-muted)] mb-1">
                      Dataset
                    </label>
                    <select
                      className="w-full rounded-xl border border-surface-200 dark:border-surface-700 bg-white/80 dark:bg-surface-900/80 px-3 py-2 text-sm outline-none focus:border-brand-400"
                      value={selectedDataset}
                      onChange={(e) => setSelectedDataset(e.target.value)}
                    >
                      <option value="">Select a dataset</option>
                      {datasets.map((dataset) => (
                        <option key={dataset.name} value={dataset.name}>
                          {dataset.name} ({dataset.size})
                        </option>
                      ))}
                    </select>
                  </div>
                  <Button
                    variant="outline"
                    size="md"
                    disabled={!datasetFile || isUploadingDataset || isRunning}
                    isLoading={isUploadingDataset}
                    onClick={() => uploadDataset()}
                  >
                    {isUploadingDataset ? "Uploading..." : "Upload Dataset"}
                  </Button>
                </div>
              </GlassCard>
            </div>
            <UploadCard
              title="Job Description"
              accepted={[".txt", ".docx", ".pdf"]}
              file={jdFile}
              onFile={setJdFile}
            />
          </div>

          {/* Action Bar */}
          <GlassCard className="p-4 md:p-5">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className={`w-2.5 h-2.5 rounded-full ${jdFile && selectedDataset ? "bg-emerald-500 animate-pulse" : "bg-surface-300 dark:bg-surface-600"}`} />
                <span className="text-sm text-[var(--text-secondary)]">
                  {!jdFile && !selectedDataset
                    ? "Select a dataset and upload a job description"
                    : !jdFile
                    ? "Job description required"
                    : !selectedDataset
                    ? "Dataset selection required"
                    : "Ready to analyze"}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="gradient"
                  size="lg"
                  disabled={!jdFile || !selectedDataset || isRunning}
                  isLoading={isRunning}
                  onClick={() => startRanking()}
                  leftIcon={!isRunning ? <Play className="w-4 h-4" /> : undefined}
                >
                  {isRunning ? "Processing..." : "Run Ranking"}
                </Button>
                <a
                  href="/results"
                  className="hidden sm:inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-brand-500 transition-colors"
                >
                  View results
                  <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                </a>
              </div>
            </div>
          </GlassCard>

          {/* Progress */}
          <ProgressPanel
            status={status}
            isRunning={isRunning}
            messages={progressMessages}
            stage={currentStage}
            stageLabel={stageLabel}
            progressPct={progressPct}
            candidatesProcessed={candidatesProcessed}
            lastError={lastError}
            onRetry={retry}
          />
        </div>
      </section>
    </div>
  );
}
