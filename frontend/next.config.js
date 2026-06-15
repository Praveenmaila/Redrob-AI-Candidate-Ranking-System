/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow eval() in dev mode for Next.js fast refresh / source maps
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              process.env.NODE_ENV === "development"
                ? "script-src 'self' 'unsafe-eval' 'unsafe-inline';"
                : "",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
