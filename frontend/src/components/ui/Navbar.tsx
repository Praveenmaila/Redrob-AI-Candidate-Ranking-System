"use client";
import React, { useEffect, useState } from "react";
import { Brain, Menu, X } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

const navLinks = [
  { href: "/", label: "Dashboard" },
  { href: "/results", label: "Results" },
  { href: "/analytics", label: "Analytics" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activePath, setActivePath] = useState("/");

  useEffect(() => {
    setActivePath(window.location.pathname);
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close mobile menu on Escape
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [mobileOpen]);

  return (
    <header
      className={`
        fixed top-0 left-0 right-0 z-50 transition-all duration-300
        ${scrolled
          ? "glass-strong shadow-[var(--shadow-md)]"
          : "bg-transparent"
        }
      `}
      role="banner"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="/" className="flex items-center gap-2.5 group" aria-label="Redrob AI Home">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-violet-600 flex items-center justify-center shadow-lg shadow-brand-500/25 transition-transform duration-300 group-hover:scale-110 group-hover:shadow-brand-500/40">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold hidden sm:block">
              <span className="gradient-text">Redrob</span>
              <span className="text-[var(--text-muted)] font-normal ml-1.5 text-sm">AI</span>
            </span>
          </a>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1" role="navigation" aria-label="Main navigation">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className={`
                  relative px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200
                  ${activePath === link.href
                    ? "text-brand-600 dark:text-brand-400"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-surface-100 dark:hover:bg-surface-800"
                  }
                `}
                aria-current={activePath === link.href ? "page" : undefined}
              >
                {link.label}
                {/* Active indicator bar */}
                {activePath === link.href && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 rounded-full bg-gradient-to-r from-brand-500 to-violet-500" />
                )}
              </a>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            {/* Mobile menu button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-800 text-[var(--text-primary)] transition-colors"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          id="mobile-nav"
          className="md:hidden glass-strong animate-slide-down border-t border-[var(--border-color)]"
        >
          <nav className="px-4 py-3 space-y-1" role="navigation" aria-label="Mobile navigation">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className={`
                  block px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                  ${activePath === link.href
                    ? "bg-brand-50 dark:bg-brand-950/30 text-brand-600 dark:text-brand-400 border-l-2 border-brand-500"
                    : "text-[var(--text-secondary)] hover:bg-surface-100 dark:hover:bg-surface-800"
                  }
                `}
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}
