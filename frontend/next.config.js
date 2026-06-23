/** @type {import('next').NextConfig} */
const BACKEND_TARGET =
  process.env.NEXT_PUBLIC_BACKEND_TARGET || "http://localhost:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      // Proxy /api/* -> backend so the browser never has to know the
      // backend's host:port. This avoids CORS, works when the frontend
      // is accessed from a remote machine, and keeps the dev workflow
      // simple: both uvicorn (8000) and next dev (3000) just need to be
      // running on the same host.
      { source: "/api/:path*", destination: `${BACKEND_TARGET}/:path*` },
    ];
  },
  async headers() {
    return [
      {
        source: "/submission_top100.csv",
        headers: [
          {
            key: "Content-Disposition",
            value: 'attachment; filename="submission_top100.csv"',
          },
          {
            key: "Content-Type",
            value: "text/csv; charset=utf-8",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
