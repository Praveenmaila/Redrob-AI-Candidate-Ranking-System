"use client";
import { useState, useCallback, useEffect } from "react";
import { api, BASE_URL } from "../lib/api";
import type { DatasetInfo } from "../types";

export function useRanking() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [datasetFile, setDatasetFile] = useState<File | null>(null);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [selectedDataset, setSelectedDataset] = useState("");
  const [isUploadingDataset, setIsUploadingDataset] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [lastError, setLastError] = useState<string | null>(null);

  // Structured stage data from backend
  const [currentStage, setCurrentStage] = useState("idle");
  const [stageLabel, setStageLabel] = useState("Idle");
  const [progressPct, setProgressPct] = useState(0);
  const [candidatesProcessed, setCandidatesProcessed] = useState(0);

  // Keep a minimal list of user-friendly messages (not raw subprocess output)
  const [progressMessages, setProgressMessages] = useState<string[]>([]);

  const refreshDatasets = useCallback(async () => {
    const res = await api.get("/datasets");
    const list = res.data as DatasetInfo[];
    setDatasets(list);
    setSelectedDataset((current) => {
      if (current && list.some((dataset) => dataset.name === current)) return current;
      return list[0]?.name || "";
    });
  }, []);

  useEffect(() => {
    refreshDatasets().catch(() => {
      setDatasets([]);
    });
  }, [refreshDatasets]);

  const uploadDataset = useCallback(async () => {
    if (!datasetFile) return;
    setIsUploadingDataset(true);
    setLastError(null);
    try {
      const fd = new FormData();
      fd.append("file", datasetFile);
      const res = await api.post("/datasets/upload", fd);
      const uploaded = res.data as DatasetInfo;
      await refreshDatasets();
      setSelectedDataset(uploaded.name);
      setDatasetFile(null);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Failed to upload dataset.";
      setLastError(msg);
    } finally {
      setIsUploadingDataset(false);
    }
  }, [datasetFile, refreshDatasets]);

  const startRanking = useCallback(async () => {
    if (!jdFile || !selectedDataset) return;
    setIsRunning(true);
    setStatus("Starting");
    setProgressMessages(["Uploading job description..."]);
    setLastError(null);
    setCurrentStage("loading_model");
    setStageLabel("Starting...");
    setProgressPct(0);
    setCandidatesProcessed(0);

    const maxUploadAttempts = 3;
    const uploadBaseDelay = 1000;

    function isTransientError(err: any) {
      if (!err) return false;
      if (!err.response) return true;
      const st = err.response.status;
      return [429, 502, 503, 504].includes(st);
    }

    try {
      const fd = new FormData();
      fd.append("jd", jdFile);
      fd.append("dataset", selectedDataset);

      let uploaded = false;
      let attempt = 0;
      let lastUploadErr: any = null;
      while (!uploaded && attempt < maxUploadAttempts) {
        attempt += 1;
        try {
          await api.post("/rank", fd);
          uploaded = true;
        } catch (err: any) {
          lastUploadErr = err;
          const transient = isTransientError(err);
          if (!transient || attempt >= maxUploadAttempts) break;
          const delay = uploadBaseDelay * Math.pow(2, attempt - 1);
          await new Promise((res) => setTimeout(res, delay));
        }
      }

      if (!uploaded) {
        const msg =
          lastUploadErr?.response?.status === 404
            ? "Backend not reachable. Please ensure the API server is running."
            : "Failed to start ranking. Please check your connection and try again.";
        setProgressMessages((prev) => [...prev, msg]);
        setLastError(msg);
        setIsRunning(false);
        setStatus("Failed");
        setCurrentStage("error");
        setStageLabel("Error");
        return;
      }

      // Start polling status
      setStatus("Analyzing candidates...");
      setProgressMessages((prev) => [...prev, "Ranking pipeline started"]);
      let pollErrors = 0;
      const maxPollErrors = 6;

      const poll = async () => {
        try {
          const s = await api.get("/health");
          const data = s.data as any;

          // Update structured stage data
          setCurrentStage(data.stage || "idle");
          setStageLabel(data.stageLabel || data.progressMessage || "Processing...");
          setProgressPct(data.progressPct || 0);
          setCandidatesProcessed(data.candidatesProcessed || 0);
          setStatus(data.stageLabel || "Processing...");

          if (data.status === "done" || data.status === "ready" || data.status === "ok") {
            setIsRunning(false);
            setStatus("Completed");
            setCurrentStage("completed");
            setStageLabel("Completed");
            setProgressPct(100);
            window.location.href = "/results";
            return;
          }
          if (data.status === "error") {
            setIsRunning(false);
            setStatus("Failed");
            setCurrentStage("error");
            setStageLabel("Error");
            const userMsg = data.error || data.progressMessage || "Ranking failed";
            setLastError(userMsg);
            return;
          }
          pollErrors = 0;
        } catch (e: any) {
          pollErrors += 1;
          if (pollErrors >= maxPollErrors) {
            setLastError("Lost connection to the backend. Please check the server and try again.");
            setIsRunning(false);
            setStatus("Failed");
            setCurrentStage("error");
            setStageLabel("Error");
            return;
          }
        }
        setTimeout(poll, 2000);
      };
      setTimeout(poll, 1500);
    } catch (e: any) {
      const msg = "Failed to start ranking. Please check your connection and try again.";
      setProgressMessages((prev) => [...prev, msg]);
      setLastError(msg);
      setIsRunning(false);
      setStatus("Failed");
      setCurrentStage("error");
      setStageLabel("Error");
    }
  }, [jdFile, selectedDataset]);

  return {
    jdFile,
    setJdFile,
    datasetFile,
    setDatasetFile,
    datasets,
    selectedDataset,
    setSelectedDataset,
    uploadDataset,
    refreshDatasets,
    isUploadingDataset,
    startRanking,
    retry: startRanking,
    isRunning,
    status,
    progressMessages,
    backendUrl: BASE_URL,
    lastError,
    // Structured stage data
    currentStage,
    stageLabel,
    progressPct,
    candidatesProcessed,
  };
}
