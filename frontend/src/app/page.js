"use client";
import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <main className="min-h-screen text-white flex flex-col items-center justify-center p-4">
      <div className="mesh-gradient" />
      {/* <div className="grain" /> ADD THIS LINE */}

      <h1 className="text-5xl font-bold mb-8">Subtext</h1>
    </main>
  );
}
