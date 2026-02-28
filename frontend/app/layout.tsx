import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retrofit Ranking MVP",
  description:
    "Hackathon MVP for ranking home energy retrofit options based on simplified city-level inputs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}