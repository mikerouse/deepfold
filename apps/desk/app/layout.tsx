import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Deepfold · Editorial pipeline",
  description: "Human-in-the-loop newsroom pipeline for Conservative Post and UK local titles. Pitch first; draft only after Go.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700&family=Public+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
