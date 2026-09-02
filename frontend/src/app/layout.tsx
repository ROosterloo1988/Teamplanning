import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "Teamplanning - De Gouv",
  description: "Beschikbaarheid en opstelling voor tafeltennisteam De Gouv",
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
