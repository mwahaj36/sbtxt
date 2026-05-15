import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/navbar";
import { SyncProvider } from "@/components/SyncProvider";

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
  openGraph: {
    title: "SBTXT",
    description: "Discover cinema through vibes, story, and soul.",
    type: "website",
    images: [
      {
        url: "/preview.png",
        width: 1200,
        height: 630,
        alt: "SBTXT Preview",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SBTXT",
    description: "Discover cinema through vibes, story, and soul.",
    images: ["/preview.png"],
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased overflow-hidden">
      <body className="h-full bg-black text-white flex flex-col overflow-hidden">
        {/* Main Scroll Container */}
        <div className="main-scroll-container flex-1 overflow-y-auto overflow-x-hidden snap-y snap-mandatory scroll-smooth flex flex-col">
          <SyncProvider>
            <Navbar />
            {children}
          </SyncProvider>
        </div>
      </body>
    </html>
  );
}
