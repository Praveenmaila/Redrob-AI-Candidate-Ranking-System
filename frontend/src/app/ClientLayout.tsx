"use client";
import React from "react";
import Navbar from "../components/ui/Navbar";
import Footer from "../components/ui/Footer";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Animated background blobs */}
      <div
        className="fixed inset-0 -z-10 overflow-hidden pointer-events-none"
        aria-hidden="true"
      >
        <div className="blob w-[500px] h-[500px] bg-brand-500 -top-48 -right-48" />
        <div
          className="blob w-[400px] h-[400px] bg-violet-500 bottom-0 -left-48"
          style={{ animationDelay: "3s" }}
        />
        <div
          className="blob w-[300px] h-[300px] bg-cyan-500 top-1/2 left-1/2"
          style={{ animationDelay: "6s" }}
        />
      </div>

      <Navbar />
      <main className="flex-1 pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </div>
      </main>
      <Footer />
    </>
  );
}
