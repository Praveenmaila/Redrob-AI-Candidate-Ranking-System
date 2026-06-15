"use client";
import { useState, useCallback } from "react";
import { api } from "../lib/api";

export function useRanking() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [candidatesFile, setCandidatesFile] = useState<File | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [progressMessages, setProgressMessages] = useState<string[]>([]);

  const startRanking = useCallback(async () => {
    if (!jdFile || !candidatesFile) return;
    setIsRunning(true);
    setStatus("Starting");
    setProgressMessages(["Uploading files..."]);

    try {
      const fd = new FormData();
      fd.append("jd", jdFile);
      fd.append("candidates", candidatesFile);

      const res = await api.post("/rank", fd);

      // start polling status
      setStatus("Analyzing candidates...");
      const poll = async () => {
        try {
          const s = await api.get("/health");
          const data = s.data as any;
          const msg =
            data.progressMessage || data.status || JSON.stringify(data);
          setProgressMessages((prev) => [...prev.slice(-10), String(msg)]);
          setStatus(String(msg));
          if (
            data.status === "done" ||
            data.status === "ready" ||
            data.status === "ok"
          ) {
            setIsRunning(false);
            setStatus("Completed");
            // navigate to results
            window.location.href = "/results";
            return;
          }
        } catch (e) {
          // ignore polling error
          setProgressMessages((prev) => [...prev.slice(-10), "Polling error"]);
        }
        setTimeout(poll, 2000);
      };
      setTimeout(poll, 1500);
    } catch (e: any) {
      let msg = "Failed to start ranking: " + (e.message || String(e));
      // axios error with response
      if (e?.response?.status) {
        msg += ` (status ${e.response.status})`;
        if (e.response.status === 404) {
          msg +=
            " — backend endpoint not found. Is the backend server running at http://localhost:8000 ?";
        }
      }
      setProgressMessages((prev) => [...prev, msg]);
      setIsRunning(false);
      setStatus("Failed");
    }
  }, [jdFile, candidatesFile]);

  return {
    jdFile,
    setJdFile,
    candidatesFile,
    setCandidatesFile,
    startRanking,
    isRunning,
    status,
    progressMessages,
  };
}
