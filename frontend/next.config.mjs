/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    // Proxied server-side so the browser only ever talks to this app's own
    // origin: no CORS, and a reverse proxy/SSL-offloader in front only needs
    // a single upstream (this service's port). BACKEND_INTERNAL_URL is a
    // runtime env var (not NEXT_PUBLIC_*), read when the server starts.
    const backend = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
