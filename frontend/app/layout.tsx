import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Retrofit Hackathon Frontend",
  description: "Frontend shell for preparing and sending retrofit analysis data.",
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