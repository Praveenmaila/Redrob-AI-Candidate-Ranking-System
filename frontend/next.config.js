/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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
