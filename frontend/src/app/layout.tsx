import "../styles/globals.css";
import React from "react";
import { Metadata } from "next";
import ClientLayout from "./ClientLayout";

export const metadata: Metadata = {
  title: "Redrob AI — Candidate Ranking System",
  description:
    "AI-powered candidate ranking system that analyzes resumes, extracts skills, and provides semantic matching for intelligent hiring decisions.",
  keywords: ["AI", "candidate ranking", "recruitment", "hiring", "resume analysis"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-grid-pattern min-h-screen flex flex-col">
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
