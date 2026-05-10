// Subtext v1.0
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "SBTXT",
  description: "Discover cinema through vibes, story, and soul.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased overflow-hidden">
      <body className="h-full bg-black text-white flex flex-col overflow-hidden">
        {/* Main Scroll Container */}
        <div className="main-scroll-container flex-1 overflow-y-auto overflow-x-hidden snap-y snap-mandatory scroll-smooth flex flex-col">
          <Navbar />
          {children}
        </div>
      </body>
    </html>
  );
}
