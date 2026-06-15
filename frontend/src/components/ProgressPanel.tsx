"use client";
import React from "react";

interface Props {
  status: string;
  isRunning: boolean;
  messages: string[];
  backendUrl?: string;
  lastError?: string | null;
}

export default function ProgressPanel({ status, isRunning, messages, backendUrl, lastError }: Props) {
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
        {backendUrl ? (
          <div className="text-xs text-gray-500 mb-2">
            Backend: <a href={backendUrl} className="underline">{backendUrl}</a>
          </div>
        ) : null}
        {lastError ? (
          <div className="mb-2 p-2 bg-red-50 border border-red-100 text-sm text-red-700 rounded">
            <div className="font-medium">Last error</div>
            <div className="whitespace-pre-wrap text-xs mt-1">{lastError}</div>
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
