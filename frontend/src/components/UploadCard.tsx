"use client";
import React from "react";
import { Button } from "./shadcn";
import { useDropzone } from "react-dropzone";

interface Props {
  title: string;
  accepted: string[];
  file: File | null;
  onFile: (f: File | null) => void;
}

export default function UploadCard({ title, accepted, file, onFile }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: accepted.reduce(
      (acc, ext) => {
        // map extensions to mime-agnostic matcher
        acc[ext] = [];
        return acc;
      },
      {} as Record<string, string[]>,
    ),
    multiple: false,
    onDrop: (acceptedFiles) => {
      onFile(acceptedFiles[0] || null);
    },
  });

  return (
    <div className="bg-white rounded-md shadow p-4">
      <h3 className="font-medium mb-2">{title}</h3>
      <div
        {...getRootProps()}
        className={`p-6 border-dashed border-2 rounded-md cursor-pointer ${isDragActive ? "border-indigo-500" : "border-gray-200"}`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div>
            <div className="text-sm font-semibold">{file.name}</div>
            <div className="text-xs text-gray-500">
              {(file.size / 1024).toFixed(1)} KB
            </div>
            <Button
              variant="ghost"
              className="mt-2 text-sm text-red-600"
              onClick={(e) => {
                e.stopPropagation();
                onFile(null);
              }}
            >
              Remove
            </Button>
          </div>
        ) : (
          <div className="text-center text-sm text-gray-500">
            Drag & drop a file here, or click to select
            <div className="text-xs mt-2">Accepted: {accepted.join(", ")}</div>
          </div>
        )}
      </div>
    </div>
  );
}
