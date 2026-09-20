import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Market Intelligence Terminal",
  description: "Dashboard analisis pasar crypto berbasis data real-time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body className="bg-neutral-950 antialiased">{children}</body>
    </html>
  );
}
