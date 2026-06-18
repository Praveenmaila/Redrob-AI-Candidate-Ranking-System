"use client";
import React from "react";
import { Users, Target, Zap, Clock } from "lucide-react";
import AnimatedCounter from "../ui/AnimatedCounter";
import GlassCard from "../ui/GlassCard";

const stats = [
  { icon: Users, label: "Candidates Analyzed", value: 500, suffix: "+", color: "from-brand-500 to-violet-500", iconBg: "bg-brand-50 dark:bg-brand-950/30" },
  { icon: Target, label: "Average AI Score", value: 0.62, decimals: 2, color: "from-emerald-500 to-green-500", iconBg: "bg-emerald-50 dark:bg-emerald-950/30" },
  { icon: Zap, label: "Skills Extracted", value: 150, suffix: "+", color: "from-amber-500 to-orange-500", iconBg: "bg-amber-50 dark:bg-amber-950/30" },
  { icon: Clock, label: "Processing Time", value: 30, suffix: "s", color: "from-rose-500 to-pink-500", iconBg: "bg-rose-50 dark:bg-rose-950/30" },
];

export default function StatsSection() {
  return (
    <section className="py-12 md:py-16" aria-label="Platform statistics">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
        {stats.map((s, i) => (
          <GlassCard
            key={s.label}
            className="p-5 md:p-6 text-center group hover:shadow-[var(--shadow-lg)] transition-all duration-300"
          >
            <div
              className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${s.color} flex items-center justify-center mx-auto mb-4 shadow-lg transition-transform duration-300 group-hover:scale-110`}
            >
              <s.icon className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div className="text-2xl md:text-3xl font-bold mb-1.5 tracking-tight">
              <AnimatedCounter
                end={s.value}
                suffix={s.suffix || ""}
                decimals={s.decimals || 0}
              />
            </div>
            <div className="text-xs md:text-sm text-[var(--text-muted)] font-medium">{s.label}</div>
          </GlassCard>
        ))}
      </div>
    </section>
  );
}
