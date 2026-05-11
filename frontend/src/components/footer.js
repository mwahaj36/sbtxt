"use client";
import React from 'react';

export default function Footer() {
    return (
        <footer className="py-12 px-12 flex flex-col md:flex-row justify-between items-end gap-8 border-t border-white/5 bg-black/40 backdrop-blur-xl w-full">
            <div className="flex flex-col gap-4">
                <div className="w-28 h-8 bg-white group-hover:bg-[var(--primary)] transition-all duration-500 transform [mask-image:url(/file.svg)] [mask-size:contain] [mask-repeat:no-repeat] [mask-position:center]" />
                <p className="text-[10px] font-bold uppercase tracking-widest text-gray-700">© 2026 SBTXT. All Rights Reserved.</p>
            </div>
            
            <div className="flex flex-col items-end gap-6">
                <div className="flex gap-8 text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    {/* <a href="#" className="hover:text-white transition-colors">Twitter</a> */}
                    {/* <a href="#" className="hover:text-white transition-colors">Letterboxd</a> */}
                    {/* <a href="#" className="hover:text-white transition-colors">Privacy</a> */}
                </div>

                <div className="flex flex-col items-end gap-2 max-w-[200px]">
                    <a href="https://www.themoviedb.org/" target="_blank" rel="noopener noreferrer" className="hover:scale-105 transition-transform">
                        <img src="/tmdb.svg" alt="TMDB Logo" className="h-4" />
                    </a>
                    <p className="text-[7px] font-bold uppercase tracking-tighter text-gray-600 text-right leading-tight">
                        This product uses the TMDB API but is not endorsed or certified by TMDB.
                    </p>
                </div>
            </div>
        </footer>
    );
}
