"use client";
import React from "react";
import { FileText, Brain, Code2, Trophy, Download } from "lucide-react";
import GlassCard from "../ui/GlassCard";

const features = [
  {
    icon: FileText,
    title: "Resume Analysis",
    description: "Parses and analyzes candidate resumes to extract key qualifications, experience, and education background.",
    color: "from-blue-500 to-cyan-500",
    shadowColor: "shadow-blue-500/20",
    bgLight: "bg-blue-50 dark:bg-blue-950/30",
  },
  {
    icon: Brain,
    title: "Semantic Matching",
    description: "Uses NLP to match candidate profiles against job descriptions with deep contextual understanding.",
    color: "from-brand-500 to-violet-500",
    shadowColor: "shadow-brand-500/20",
    bgLight: "bg-brand-50 dark:bg-brand-950/30",
  },
  {
    icon: Code2,
    title: "Skill Extraction",
    description: "Automatically identifies and categorizes technical skills, certifications, tools, and frameworks.",
    color: "from-emerald-500 to-green-500",
    shadowColor: "shadow-emerald-500/20",
    bgLight: "bg-emerald-50 dark:bg-emerald-950/30",
  },
  {
    icon: Trophy,
    title: "AI Ranking",
    description: "Multi-signal scoring combining semantic fit, skills match, and experience relevance for accurate rankings.",
    color: "from-amber-500 to-orange-500",
    shadowColor: "shadow-amber-500/20",
    bgLight: "bg-amber-50 dark:bg-amber-950/30",
  },
  {
    icon: Download,
    title: "CSV Export",
    description: "Export ranked results as CSV with detailed scores and AI-generated reasoning for each candidate.",
    color: "from-rose-500 to-pink-500",
    shadowColor: "shadow-rose-500/20",
    bgLight: "bg-rose-50 dark:bg-rose-950/30",
  },
];

export default function FeatureCards() {
  return (
    <section className="py-16 md:py-20" aria-labelledby="features-heading">
      <div className="text-center mb-14">
        <h2 id="features-heading" className="text-3xl md:text-4xl font-bold mb-4">
          Powerful <span className="gradient-text">Features</span>
        </h2>
        <p className="text-[var(--text-secondary)] max-w-lg mx-auto text-base">
          Everything you need to streamline your candidate evaluation process.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
        {features.map((f, i) => (
          <GlassCard
            key={f.title}
            hover
            as="article"
            className={`p-6 md:p-7 opacity-0 animate-slide-up group`}
          >
            <div
              className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.color} ${f.shadowColor} shadow-lg flex items-center justify-center mb-5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}
            >
              <f.icon className="w-6 h-6 text-white" aria-hidden="true" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {f.description}
            </p>
          </GlassCard>
        ))}
      </div>
    </section>
  );
}
