"use client";
import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Home, ChevronLeft, Film } from 'lucide-react';

export default function NotFound() {
    return (
        <main className="h-screen w-full bg-black text-white flex flex-col items-center justify-center px-4 relative overflow-hidden">
            {/* Background Atmosphere */}
            <div className="mesh-gradient opacity-30 fixed inset-0 pointer-events-none" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[var(--primary)]/10 rounded-full blur-[120px] pointer-events-none" />

            <div className="relative z-10 text-center">
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="mb-8"
                >
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-white/5 border border-white/10 rounded-full mb-6">
                        <Film size={40} className="text-[var(--primary)]" />
                    </div>
                    <h1 className="font-['Arkhip'] text-8xl md:text-9xl tracking-tighter leading-none mb-4 uppercase text-transparent bg-clip-text bg-gradient-to-b from-white to-white/20">
                        404
                    </h1>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.8 }}
                >
                    <h2 className="text-xl md:text-2xl font-black uppercase tracking-[0.3em] mb-4 text-[var(--primary)]">
                        Outside the Frame
                    </h2>
                    <p className="max-w-md mx-auto text-gray-400 text-sm md:text-base font-light tracking-wide mb-10 px-4">
                        This scene wasn't in the script. You've wandered into a cinematic void where the story doesn't exist.
                    </p>

                    <div className="flex flex-col md:flex-row gap-4 justify-center items-center">
                        <Link 
                            href="/" 
                            className="group flex items-center gap-3 px-8 py-4 bg-white text-black font-black uppercase tracking-widest text-[10px] rounded-full transition-all hover:scale-105 active:scale-95"
                        >
                            <Home size={14} />
                            <span>Return Home</span>
                        </Link>
                        <button 
                            onClick={() => window.history.back()}
                            className="flex items-center gap-3 px-8 py-4 border border-white/10 hover:border-white/30 backdrop-blur-md rounded-full text-[10px] font-black uppercase tracking-widest transition-all hover:bg-white/5"
                        >
                            <ChevronLeft size={14} />
                            <span>Go Back</span>
                        </button>
                    </div>
                </motion.div>
            </div>

            {/* Decorative Elements */}
            <div className="absolute bottom-10 left-10 flex flex-col gap-1 opacity-20 pointer-events-none">
                <div className="h-px w-24 bg-white" />
                <span className="text-[8px] font-black uppercase tracking-widest">Error Code: SCENE_NOT_FOUND</span>
            </div>
            
            <div className="absolute top-1/2 right-0 -translate-y-1/2 text-[15rem] font-black opacity-[0.02] select-none pointer-events-none whitespace-nowrap rotate-90">
                VOID VOID VOID
            </div>
        </main>
    );
}
