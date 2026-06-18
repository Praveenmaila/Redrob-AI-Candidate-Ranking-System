"use client";
import React from "react";
import { Brain, ExternalLink } from "lucide-react";

const footerLinks = {
  Product: [
    { label: "Dashboard", href: "/" },
    { label: "Results", href: "/results" },
    { label: "Analytics", href: "/analytics" },
  ],
  Resources: [
    { label: "Documentation", href: "#" },
    { label: "Methodology", href: "#" },
    { label: "API Reference", href: "#" },
  ],
};

export default function Footer() {
  return (
    <footer className="relative mt-20" role="contentinfo">
      {/* Gradient divider */}
      <div className="gradient-divider" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
          {/* Brand column */}
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-violet-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="text-base font-bold">
                <span className="gradient-text">Redrob</span>
                <span className="text-[var(--text-muted)] font-normal ml-1 text-sm">
                  AI Candidate Ranking
                </span>
              </span>
            </div>
            <p className="text-sm text-[var(--text-muted)] max-w-sm leading-relaxed mb-4">
              AI-powered candidate ranking system that analyzes resumes,
              extracts skills, and provides semantic matching for intelligent
              hiring decisions.
            </p>
            <a
              href="https://github.com/Praveenmaila/Redrob-AI-Candidate-Ranking-System"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-sm text-[var(--text-muted)] hover:text-brand-500 transition-colors duration-200"
              aria-label="GitHub repository"
            >
              View on GitHub
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-4">
                {category}
              </h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-[var(--text-secondary)] hover:text-brand-500 transition-colors duration-200"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-10 pt-6 border-t border-[var(--border-color)] flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-[var(--text-muted)]">
            © {new Date().getFullYear()} Redrob AI. Built with Next.js & AI.
          </p>
          <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
            <span className="inline-flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Operational
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
