const apiProxyTarget = (
  process.env.NEXT_API_PROXY_TARGET ??
  "http://nginx"
).replace(/\/+$/, "")

const publicCacheSources = [
  "/about/:path*",
  "/academics/:path*",
  "/academic-programmes/:path*",
  "/admissions/:path*",
  "/centers/:path*",
  "/centres/:path*",
  "/contact/:path*",
  "/departments/:path*",
  "/directories/:path*",
  "/events/:path*",
  "/news/:path*",
  "/official-links/:path*",
  "/programmes/:path*",
  "/programs/:path*",
  "/schools/:path*",
  "/services/:path*",
  "/student-life/:path*",
  "/units/:path*",
]

const publicCacheHeaders = [
  {
    key: "Cache-Control",
    value: "public, s-maxage=300, stale-while-revalidate=86400",
  },
]

const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV === "production" ? "" : " 'unsafe-eval'"}`,
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' https://aiu.edu.my data: blob:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
      "frame-src 'none'",
      "upgrade-insecure-requests",
    ].join("; "),
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  {
    key: "X-XSS-Protection",
    value: "0",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=()",
  },
]

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  allowedDevOrigins: ['localhost', '127.0.0.1'],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "aiu.edu.my",
      },
      {
        protocol: "https",
        hostname: "www.aiu.edu.my",
      },
    ],
  },
  async headers() {
    return [
      ...publicCacheSources.map((source) => ({
        source,
        headers: publicCacheHeaders,
      })),
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ]
  },
  async rewrites() {
    return [
      {
        source: "/api",
        destination: `${apiProxyTarget}/api`,
      },
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
