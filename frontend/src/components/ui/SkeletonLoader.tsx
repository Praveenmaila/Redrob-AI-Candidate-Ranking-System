"use client";
import React from "react";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "card" | "row" | "circle";
}

export function Skeleton({ className = "", variant = "text" }: SkeletonProps) {
  const base = "skeleton";
  const variants: Record<string, string> = {
    text: "h-4 w-full",
    card: "h-32 w-full",
    row: "h-12 w-full",
    circle: "h-10 w-10 rounded-full",
  };
  return <div className={`${base} ${variants[variant]} ${className}`} />;
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4">
      <div className="flex gap-4 mb-4">
        <Skeleton className="h-10 w-60" />
        <Skeleton className="h-10 w-32 ml-auto" />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="row" />
      ))}
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-[var(--border-color)] p-6 space-y-3">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}
