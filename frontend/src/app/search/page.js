"use client";
import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';
export default function Home() {
    const [query, SetQuery] = useState("")
    const [movies, setMovies] = useState([])
    const [loading, setLoading] = useState(false)
    const [isSearched, setIsSearched] = useState(false)

    const handleSearch = async () => {
        if (!query) return;
        setLoading(true);
        setIsSearched(true)

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            console.log("Backend sent this:", data);
            setMovies(data);
        } catch (error) {
            console.error("Search failedd", error)
        } finally {
            setLoading(false)
        }

    }

    return (
        <main className="min-h-screen text-white flex flex-col items-center justify-center p-7">
            <div className="mesh-gradient" />
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={isSearched
                    ? { scale: 0.8, y: 0, opacity: 1 }
                    : { scale: 1, y: 0, opacity: 1 }
                } transition={{ duration: 1.2, ease: "easeOut" }}
                className="relative w-full max-w-2xl group"
            >
                <h1 className="items-center font-['Biysk'] text-8xl text-center"> Movies, Semantically.</h1>
                <div className=' relative flex gap-4 items-stretch'>
                    <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[--primary] transition-colors z-10">
                        <Search size={20} />
                    </div>
                    <input
                        type="text"
                        placeholder='Enter the Vibe of Movie You want to search?'
                        value={query}
                        onChange={(e) => SetQuery(e.target.value)}
                        className="flex-1 bg-[--surface] border border-white/10 backdrop-blur-xl px-14 py-4 rounded-2xl outline-none focus:border-[--primary] transition-all text-lg placeholder:text-gray-500"
                    />
                    <div className="absolute -inset-1 bg-gradient-to-r from-[--primary] to-[--secondary] rounded-2xl blur opacity-0 group-focus-within:opacity-20 transition-opacity -z-10" />
                    <button className="bg-[var(--primary)] px-8 rounded-xl font-bold hover:brightness-110 hover:bg-[var(--surface)] bordere border-2 border-transparent hover:border-[var(--primary)] active:scale-95 transition-all" onClick={handleSearch}>
                        Search
                    </button>
                </div>
            </motion.div>
            <div
                className="w-full max-w-2xl mx-auto overflow-hidden mt-6 relative"
                style={{
                    maskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)',
                    WebkitMaskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)'
                }}
            >
                <motion.div
                    className="flex gap-4 whitespace-nowrap"
                    animate={{ x: ["0%", "-50%"] }}
                    transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                >
                    {[
                        "Dystopian synthwave city",
                        "Heartfelt rural coming-of-age",
                        "Jazz-fueled heist banter",
                        "Cosmic horror isolation",
                        "Ghibli-esque nostalgia",
                        "Hyper-violent neon revenge",
                        "Dystopian synthwave city",
                        "Heartfelt rural coming-of-age",
                        "Jazz-fueled heist banter",
                        "Cosmic horror isolation",
                        "Ghibli-esque nostalgia",
                        "Hyper-violent neon revenge"
                    ].map((vibe, index) => (
                        <button
                            key={index}
                            onClick={() => SetQuery(vibe)}
                            className="px-6 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm text-sm text-gray-400 hover:text-white hover:border-[--primary]/50 hover:bg-[--primary]/10 transition-all"
                        >
                            {vibe}
                        </button>
                    ))}
                </motion.div>
            </div>
            {isSearched && (
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="w-full mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pb-20"
                >
                    {movies.map((movie, index) => (
                        <div key={index} className="bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-md">
                            <h3 className='text-xl font-bold'>
                                {movie.title}
                            </h3>
                        </div>
                    ))}
                </motion.div>
            )}
        </main >
    );
}