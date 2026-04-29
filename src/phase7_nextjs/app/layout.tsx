import type { Metadata } from "next";
import { Outfit, Inter } from "next/font/google";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit", weight: ["300","400","600","800"] });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", weight: ["400","500","700"] });

export const metadata: Metadata = {
  title: "AI Restaurant Recommender",
  description: "Discover your next favourite meal, powered by AI and real Zomato data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${inter.variable}`}>{children}</body>
    </html>
  );
}
