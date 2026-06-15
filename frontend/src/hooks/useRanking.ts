"use client";
import { useState, useCallback } from "react";
import { api, BASE_URL } from "../lib/api";

export function useRanking() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [candidatesFile, setCandidatesFile] = useState<File | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState("");
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [lastError, setLastError] = useState<string | null>(null);

  const startRanking = useCallback(async () => {
    if (!jdFile || !candidatesFile) return;
    setIsRunning(true);
    setStatus("Starting");
    setProgressMessages(["Uploading files..."]);
    setLastError(null);

    // upload with automatic retries for transient network errors
    const maxUploadAttempts = 3;
    const uploadBaseDelay = 1000; // ms

    function isTransientError(err: any) {
      if (!err) return false;
      // network error (no response)
      if (!err.response) return true;
      const st = err.response.status;
      return [429, 502, 503, 504].includes(st);
    }

    try {
      const fd = new FormData();
      fd.append("jd", jdFile);
      fd.append("candidates", candidatesFile);

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
          const msg = `Upload attempt ${attempt} failed${transient ? " (transient)" : ""}: ${err?.message || String(err)}`;
          setProgressMessages((prev) => [...prev, msg]);
          if (!transient || attempt >= maxUploadAttempts) break;
          const delay = uploadBaseDelay * Math.pow(2, attempt - 1);
          await new Promise((res) => setTimeout(res, delay));
        }
      }

      if (!uploaded) {
        // surface detailed error
        let msg =
          "Failed to start ranking: " +
          (lastUploadErr?.message || String(lastUploadErr));
        try {
          if (lastUploadErr?.config?.url)
            msg += ` | url=${lastUploadErr.config.url}`;
          if (lastUploadErr?.response?.status)
            msg += ` | status=${lastUploadErr.response.status}`;
          if (lastUploadErr?.response?.data)
            msg += ` | data=${JSON.stringify(lastUploadErr.response.data).slice(0, 500)}`;
        } catch (err) {}
        if (lastUploadErr?.response?.status === 404) {
          msg += ` — backend endpoint not found. Is the backend server running at ${BASE_URL} ?`;
        }
        setProgressMessages((prev) => [...prev, msg]);
        setLastError(msg);
        setIsRunning(false);
        setStatus("Failed");
        return;
      }

      // start polling status with retry tolerance for transient poll failures
      setStatus("Analyzing candidates...");
      let pollErrors = 0;
      const maxPollErrors = 6;
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
            window.location.href = "/results";
            return;
          }
          if (data.status === "error") {
            setIsRunning(false);
            setStatus("Failed");
            setLastError(data.progressMessage || "Ranking failed on the backend");
            return;
          }
          pollErrors = 0;
        } catch (e: any) {
          pollErrors += 1;
          setProgressMessages((prev) => [
            ...prev.slice(-10),
            `Polling error (#${pollErrors}): ${e?.message || String(e)}`,
          ]);
          if (pollErrors >= maxPollErrors) {
            const msg = `Polling failed ${pollErrors} times; aborting.`;
            setProgressMessages((prev) => [...prev, msg]);
            setLastError(msg);
            setIsRunning(false);
            setStatus("Failed");
            return;
          }
        }
        setTimeout(poll, 2000);
      };
      setTimeout(poll, 1500);
    } catch (e: any) {
      let msg = "Failed to start ranking: " + (e.message || String(e));
      try {
        if (e?.config?.url) msg += ` | url=${e.config.url}`;
        if (e?.response?.status) msg += ` | status=${e.response.status}`;
        if (e?.response?.data)
          msg += ` | data=${JSON.stringify(e.response.data).slice(0, 500)}`;
      } catch (err) {}
      setProgressMessages((prev) => [...prev, msg]);
      setLastError(msg);
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
    // alias for manual retry from the UI
    retry: startRanking,
    isRunning,
    status,
    progressMessages,
    backendUrl: BASE_URL,
    lastError,
  };
}
