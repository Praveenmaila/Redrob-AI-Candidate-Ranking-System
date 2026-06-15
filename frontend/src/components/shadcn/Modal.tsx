"use client";
import React from "react";

export default function Modal({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose?: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-md shadow-lg w-full max-w-2xl p-6">
        {children}
      </div>
    </div>
  );
}
