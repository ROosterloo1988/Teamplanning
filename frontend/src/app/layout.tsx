import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Teamplanning - De Gouv",
  description: "Beschikbaarheid en opstelling voor dartteam De Gouv",
  manifest: "/manifest.webmanifest",
  icons: {
    icon: "/favicon-32.png",
    apple: "/apple-touch-icon.png",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "De Gouv",
  },
};

export const viewport: Viewport = {
  themeColor: "#1d4ed8",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="nl">
      <body className="min-h-screen">
        <AuthProvider>
          <div className="mx-auto max-w-md sm:max-w-2xl px-4 py-6">{children}</div>
        </AuthProvider>
      </body>
    </html>
  );
}
