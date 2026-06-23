"use client";
import React from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, FileSpreadsheet, X, CheckCircle2 } from "lucide-react";
import GlassCard from "./ui/GlassCard";

/**
 * Map file extensions to their MIME types for react-dropzone v14.
 * Keys must be valid MIME types; values are arrays of extensions.
 */
const EXTENSION_TO_MIME: Record<string, Record<string, string[]>> = {
  ".txt": { "text/plain": [".txt"] },
  ".pdf": { "application/pdf": [".pdf"] },
  ".docx": {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
      ".docx",
    ],
  },
  ".jsonl": { "application/x-ndjson": [".jsonl"] },
  ".csv": { "text/csv": [".csv"] },
  ".json": { "application/json": [".json"] },
};

function buildAccept(
  extensions: string[],
): Record<string, string[]> {
  const merged: Record<string, string[]> = {};
  for (const ext of extensions) {
    const mapping = EXTENSION_TO_MIME[ext];
    if (mapping) {
      for (const [mime, exts] of Object.entries(mapping)) {
        merged[mime] = [...(merged[mime] || []), ...exts];
      }
    }
  }
  return merged;
}

function getFileIcon(accepted: string[]) {
  if (accepted.some((e) => [".csv", ".jsonl", ".json"].includes(e))) {
    return FileSpreadsheet;
  }
  return FileText;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface Props {
  title: string;
  accepted: string[];
  file: File | null;
  onFile: (f: File | null) => void;
}

export default function UploadCard({ title, accepted, file, onFile }: Props) {
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: buildAccept(accepted),
    multiple: false,
    onDrop: (acceptedFiles) => {
      onFile(acceptedFiles[0] || null);
    },
  });

  const FileIcon = getFileIcon(accepted);

  return (
    <GlassCard className="p-0 overflow-hidden">
      {/* Card header */}
      <div className="px-5 pt-5 pb-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-brand-50 dark:bg-brand-950/30 flex items-center justify-center">
            <FileIcon className="w-4 h-4 text-brand-500" aria-hidden="true" />
          </div>
          <h3 className="font-semibold text-sm">{title}</h3>
        </div>
        {file && (
          <span className="inline-flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
            Uploaded
          </span>
        )}
      </div>

      {/* Drop zone */}
      <div className="px-5 pb-5">
        <div
          {...getRootProps()}
          className={`
            relative rounded-2xl border-2 border-dashed cursor-pointer
            transition-all duration-300 ease-out
            ${file ? "p-4" : "p-8"}
            ${isDragActive
              ? "border-brand-500 bg-brand-50/50 dark:bg-brand-950/20 scale-[1.02] shadow-[var(--shadow-glow)]"
              : isDragReject
              ? "border-red-400 bg-red-50/50 dark:bg-red-950/20"
              : file
              ? "border-emerald-300 dark:border-emerald-800 bg-emerald-50/30 dark:bg-emerald-950/10"
              : "border-surface-200 dark:border-surface-700 hover:border-brand-300 dark:hover:border-brand-700 hover:bg-brand-50/30 dark:hover:bg-brand-950/10"
            }
          `}
          role="button"
          aria-label={`Upload ${title}`}
          tabIndex={0}
        >
          <input {...getInputProps()} aria-label={`Select ${title} file`} />

          {file ? (
            /* File info display */
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 flex items-center justify-center shadow-lg shadow-brand-500/20 shrink-0">
                <FileIcon className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate">{file.name}</p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  {formatFileSize(file.size)} • {file.type || "Unknown type"}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFile(null);
                }}
                className="p-2 rounded-xl text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-all duration-200 shrink-0"
                aria-label={`Remove ${file.name}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            /* Upload prompt */
            <div className="text-center">
              <div className={`
                w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center
                transition-all duration-300
                ${isDragActive
                  ? "bg-gradient-to-br from-brand-500 to-violet-500 shadow-lg shadow-brand-500/25"
                  : "bg-surface-100 dark:bg-surface-800"
                }
              `}>
                <Upload
                  className={`w-6 h-6 transition-all duration-300 ${
                    isDragActive ? "text-white scale-110" : "text-[var(--text-muted)]"
                  }`}
                  aria-hidden="true"
                />
              </div>
              <p className="text-sm font-medium mb-1">
                {isDragActive ? (
                  <span className="text-brand-600 dark:text-brand-400">Drop your file here</span>
                ) : (
                  "Drag & drop a file here, or click to select"
                )}
              </p>
              <p className="text-xs text-[var(--text-muted)]">
                Accepted: {accepted.join(", ")}
              </p>
            </div>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
