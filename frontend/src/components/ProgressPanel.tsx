"use client";
import React, { useEffect, useState } from "react";
import { Button } from "../components/shadcn";

interface Props {
  status: string;
  isRunning: boolean;
  messages: string[];
  backendUrl?: string;
  lastError?: string | null;
  onRetry?: () => void;
}

export default function ProgressPanel({
  status,
  isRunning,
  messages,
  backendUrl,
  lastError,
  onRetry,
}: Props) {
  const [visibleBackendUrl, setVisibleBackendUrl] = useState<string | null>(null);
  useEffect(() => {
    if (backendUrl) setVisibleBackendUrl(backendUrl);
  }, [backendUrl]);

  return (
    <div className="mt-6 bg-white rounded-md shadow p-4">
      <div className="flex items-center space-x-3">
        <div className="flex-1">
          <div className="text-sm text-gray-600">Status</div>
          <div className="font-medium text-gray-800">
            {status || (isRunning ? "Running" : "Idle")}
          </div>
        </div>
        <div>
          {isRunning ? (
            <div className="animate-spin h-5 w-5 border-2 border-indigo-600 border-t-transparent rounded-full" />
          ) : null}
        </div>
      </div>

      <div className="mt-3">
        {visibleBackendUrl ? (
          <div className="text-xs text-gray-500 mb-2">
            Backend: <a href={visibleBackendUrl} className="underline" target="_blank" rel="noreferrer">{visibleBackendUrl}</a>
          </div>
        ) : null}
        {lastError ? (
          <div className="mb-2 p-2 bg-red-50 border border-red-100 text-sm text-red-700 rounded">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium">Last error</div>
                <div className="whitespace-pre-wrap text-xs mt-1">
                  {lastError}
                </div>
              </div>
              {onRetry ? (
                <div className="ml-4">
                  <Button variant="ghost" onClick={onRetry}>
                    Retry
                  </Button>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
        {messages && messages.length ? (
          <ul className="text-sm text-gray-600 list-disc list-inside">
            {messages.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-gray-500">No activity yet.</div>
        )}
      </div>
    </div>
  );
}
