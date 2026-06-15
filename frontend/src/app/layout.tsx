import "./styles/globals.css";
import React from "react";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Candidate Ranking System",
  description: "Dashboard for generating and reviewing candidate rankings",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="w-full bg-white shadow-sm">
          <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
            <h1 className="text-lg font-semibold">
              AI Candidate Ranking System
            </h1>
            <nav>
              <a
                href="/"
                className="text-sm text-gray-700 hover:underline mr-4"
              >
                Dashboard
              </a>
              <a
                href="/results"
                className="text-sm text-gray-700 hover:underline"
              >
                Results
              </a>
            </nav>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
