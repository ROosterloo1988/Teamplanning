/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    // Proxied server-side so the browser only ever talks to this app's own
    // origin: no CORS, and a reverse proxy/SSL-offloader in front only needs
    // a single upstream (this service's port). rewrites() is resolved once
    // at `next build` time (baked into .next/routes-manifest.json), not
    // re-evaluated per request, so BACKEND_INTERNAL_URL must be set at
    // build time (Dockerfile ARG/ENV, docker-compose build.args) even
    // though it isn't a NEXT_PUBLIC_* var.
    const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
