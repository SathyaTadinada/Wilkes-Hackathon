import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retrofit Analyzer",
  description: "Hackathon MVP: upload bills or enter usage manually, get retrofit recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}