"use client";
import React, { useState } from 'react';
import { Search, Filter, Star, Globe, Calendar } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import VibeSpinner from '@/components/spinner';

export default function Home() {
    const [query, SetQuery] = useState("")
    const [movies, setMovies] = useState([])
    const [loading, setLoading] = useState(false)
    const [isSearched, setIsSearched] = useState(false)
    const [showFilters, setShowFilters] = useState(false)
    
    // Filter States
    const [minYear, setMinYear] = useState("")
    const [maxYear, setMaxYear] = useState("")
    const [language, setLanguage] = useState("")
    const [minVote, setMinVote] = useState("")
    const [resultCount, setResultCount] = useState(25)

    const handleSearch = async () => {
        if (!query) return;
        setLoading(true);
        setIsSearched(true)

        try {
            let url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/search?q=${encodeURIComponent(query)}`;
            if (minYear) url += `&min_year=${minYear}`;
            if (maxYear) url += `&max_year=${maxYear}`;
            if (language) url += `&language=${language}`;
            if (minVote) url += `&min_vote=${minVote}`;
            if (resultCount) url += `&k=${resultCount}`;

            const response = await fetch(url);
            const data = await response.json();
            console.log("Backend sent this:", data);
            setMovies(data);
        } catch (error) {
            console.error("Search failed", error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="min-h-screen text-white flex flex-col items-center justify-start p-7 pt-20">
            <div className="mesh-gradient" />
            
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={movies.length>0
                    ? { scale: 0.85, y: -20, opacity: 1 }
                    : { scale: 1, y: 0, opacity: 1 }
                } transition={{ duration: 1.2, ease: "easeOut" }}
                className="relative w-full max-w-2xl group z-50"
            >
                <h1 className="items-center font-['Biysk'] text-8xl text-center mb-8  text-foreground"> 
                    Movies, Semantically.
                </h1>
                
                <div className='relative flex gap-4 items-stretch'>
                    <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[--primary] transition-colors z-10">
                        <Search size={20} />
                    </div>
                    <input
                        type="text"
                        placeholder='What kind of story are you looking for?'
                        value={query}
                        onChange={(e) => SetQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="flex-1 bg-white/5 border border-white/10 backdrop-blur-2xl px-14 py-5 rounded-2xl outline-none focus:border-[--primary]/50 focus:ring-4 ring-[--primary]/10 transition-all text-lg placeholder:text-gray-500 shadow-2xl"
                    />
                    <button 
                        onClick={() => setShowFilters(!showFilters)}
                        className={`px-4 rounded-xl border border-white/10 transition-all ${showFilters ? 'bg-[--primary]/20 border-[--primary]/50 text-[--primary]' : 'bg-white/5 hover:bg-white/10'}`}
                    >
                        <Filter size={20} />
                    </button>
                    <button 
className={`bg-[var(--primary)] px-8 rounded-xl font-bold transition-all shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ${loading ? 'opacity-50 cursor-not-allowed grayscale' : 'hover:brightness-110 active:scale-95'}`}                        onClick={handleSearch}
                        disabled={loading}
                    >
                        {loading ? "..." : "Search"}
                    </button>
                </div>

                <AnimatePresence>
                    {showFilters && (
                        <motion.div 
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden mt-4 grid grid-cols-5 gap-4 p-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl"
                        >
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Calendar size={12} /> Min Year
                                </label>
                                <input 
                                    type="number" 
                                    placeholder="1990"
                                    value={minYear}
                                    onChange={(e) => setMinYear(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[--primary]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Calendar size={12} /> Max Year
                                </label>
                                <input 
                                    type="number" 
                                    placeholder="2024"
                                    value={maxYear}
                                    onChange={(e) => setMaxYear(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[--primary]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Globe size={12} /> Language
                                </label>
                                <input 
                                    type="text" 
                                    placeholder="en, ko, ja"
                                    value={language}
                                    onChange={(e) => setLanguage(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[--primary]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Star size={12} /> Min Rating
                                </label>
                                <input 
                                    type="number" 
                                    step="0.1"
                                    placeholder="7.5"
                                    value={minVote}
                                    onChange={(e) => setMinVote(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[--primary]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-xs text-gray-500 uppercase tracking-widest flex items-center gap-2">
                                    <Star size={12} /> Results
                                </label>
                                <input 
                                    type="number" 
                                    min="10"
                                    max="100"
                                    value={resultCount}
                                    onChange={(e) => setResultCount(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[--primary]/50 outline-none"
                                />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

                
                {loading && <VibeSpinner />}



            {!isSearched && !loading &&(
                <div
                    className="w-full max-w-2xl mx-auto overflow-hidden mt-8 relative"
                    style={{
                        maskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)',
                        WebkitMaskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)'
                    }}
                >
                    <motion.div
                        className="flex gap-4 whitespace-nowrap"
                        animate={{ x: ["0%", "-50%"] }}
                        transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
                    >
                        {[
                            "Dystopian synthwave city", "Heartfelt rural coming-of-age",
                            "Jazz-fueled heist banter", "Cosmic horror isolation",
                            "Ghibli-esque nostalgia", "Hyper-violent neon revenge",
                            "Dystopian synthwave city", "Heartfelt rural coming-of-age",
                            "Jazz-fueled heist banter", "Cosmic horror isolation",
                            "Ghibli-esque nostalgia", "Hyper-violent neon revenge"
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
            )}

            {isSearched && !loading &&(
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="flex flex-wrap justify-center gap-10 w-full max-w-7xl mx-auto mt-16 pb-20"
                >
                    {movies.map((movie, index) => (
                        <motion.div
                            key={index}
                            whileHover={{ y: -12, scale: 1.05 }}
                            className="w-[200px] flex-shrink-0 group cursor-pointer"
                        >
                            <div className="relative transition-all duration-500 rounded-3xl group-hover:shadow-[0_0_50px_rgba(var(--primary-rgb),0.5)]">
                                <div className="relative aspect-[2/3] rounded-3xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-md shadow-2xl transition-all duration-500 ">
                                {movie.poster_path ? (
                                    <img
                                        src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`}
                                        alt={movie.title}
                                        className='w-full h-full object-cover group-hover:scale-110 transition-transform duration-700'
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-gray-500 italic p-4 text-center">
                                        No Poster Available
                                    </div>
                                )}
                            </div>

                            <div className="absolute -inset-px rounded-3xl bg-gradient-to-t from-black via-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-6 text-center z-10">
                                <div className="flex items-center justify-center gap-2 mb-3">
                                    <div className="px-3 py-1 bg-[--primary] text-[--foreground] text-xs font-black rounded-full uppercase tracking-tighter">
                                        {Math.round(movie.score * 100)}% Match
                                    </div>
                                </div>
                                <p className="text-white/80 text-xs leading-relaxed font-medium italic">
                                    "{movie.reason}"
                                </p>
                            </div>
                        </div>

                        <h3 className='text-xl font-black mt-5 text-center group-hover:text-[--primary] transition-colors line-clamp-1 tracking-tight'>
                                {movie.title} ({movie.year})
                            </h3>
                            <div className="flex gap-2 justify-center mt-2 overflow-hidden">
                                {movie.genres?.slice(0, 2).map((g, i) => (
                                    <span key={i} className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">
                                        {g}
                                    </span>
                                ))}
                            </div>
                        </motion.div>
                    ))}
                </motion.div>
            )}
        </main >
    );
}