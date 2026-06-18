"use client";
import React from "react";
import { ArrowRight, BarChart3, ChevronDown, Sparkles } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="relative py-20 md:py-32 overflow-hidden" aria-labelledby="hero-heading">
      {/* Decorative grid dots */}
      <div className="absolute inset-0 pointer-events-none opacity-30" aria-hidden="true">
        <div className="absolute top-20 left-10 w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
        <div className="absolute top-40 right-20 w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" style={{ animationDelay: "0.5s" }} />
        <div className="absolute bottom-32 left-1/4 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/3 right-1/3 w-1 h-1 rounded-full bg-amber-400 animate-pulse" style={{ animationDelay: "1.5s" }} />
      </div>

      <div className="relative z-10 text-center max-w-4xl mx-auto px-4">
        {/* Badge pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400 text-sm font-medium mb-8 animate-fade-in border border-brand-200/50 dark:border-brand-800/30">
          <Sparkles className="w-4 h-4" aria-hidden="true" />
          AI-Powered Recruitment Intelligence
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500" />
          </span>
        </div>

        <h1
          id="hero-heading"
          className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6 animate-slide-up leading-[1.1]"
        >
          Find the{" "}
          <span className="gradient-text">Perfect Candidates</span>
          <br />
          with AI Precision
        </h1>

        <p className="text-lg md:text-xl text-[var(--text-secondary)] max-w-2xl mx-auto mb-12 animate-slide-up stagger-1 leading-relaxed">
          Upload your job description and candidates data. Our AI analyzes skills,
          experience, and semantic fit to rank the top 100 candidates instantly.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up stagger-2">
          <a
            href="#upload"
            className="group inline-flex items-center gap-2.5 px-8 py-4 rounded-2xl bg-gradient-to-r from-brand-600 to-violet-600 text-white font-semibold text-base shadow-xl shadow-brand-500/25 hover:shadow-2xl hover:shadow-brand-500/35 hover:-translate-y-1 transition-all duration-300"
          >
            <BarChart3 className="w-5 h-5" aria-hidden="true" />
            Start Ranking
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </a>
          <a
            href="/results"
            className="group inline-flex items-center gap-2 px-8 py-4 rounded-2xl border border-[var(--border-color)] text-[var(--text-primary)] font-semibold text-base hover:bg-surface-100 dark:hover:bg-surface-800 hover:border-brand-300/50 transition-all duration-300"
          >
            View Results
            <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" aria-hidden="true" />
          </a>
        </div>

        {/* Scroll indicator */}
        <div className="mt-16 animate-bounce-gentle" aria-hidden="true">
          <ChevronDown className="w-6 h-6 mx-auto text-[var(--text-muted)]" />
        </div>
      </div>
    </section>
  );
}
