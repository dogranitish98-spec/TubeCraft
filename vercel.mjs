const backend = (process.env.TUBECRAFT_BACKEND_URL || '').trim().replace(/\/$/, '')

export default {
  "$schema": "https://openapi.vercel.sh/vercel.json",
  // Vercel builds the same committed Vue/Vite source into static/.
  buildCommand: 'npm --prefix frontend ci --no-audit --no-fund && npm --prefix frontend run build:vercel',
  outputDirectory: 'static',
  cleanUrls: false,
  rewrites: [
    // The Vite bundle keeps /static/ for compatibility with the standalone
    // FastAPI server. In the Vercel static output, static/ is the site root.
    { source: '/static/:path*', destination: '/:path*' },
    // Browser calls stay same-origin /api/*; Vercel forwards them to the
    // persistent Agnes engine. This keeps API keys on the backend.
    ...(backend
      ? [{ source: '/api/:path*', destination: `${backend}/api/:path*` }]
      : []),
  ],
  headers: [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Cache-Control', value: 'no-store, no-cache, must-revalidate' },
      ],
    },
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
      ],
    },
    {
      source: '/sw.js',
      headers: [
        { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
        { key: 'Service-Worker-Allowed', value: '/' },
        { key: 'Content-Type', value: 'application/javascript; charset=utf-8' },
      ],
    },
    {
      source: '/manifest.webmanifest',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=3600' },
        { key: 'Content-Type', value: 'application/manifest+json; charset=utf-8' },
      ],
    },
    {
      source: '/assets/(.*)',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
      ],
    },
  ],
}
