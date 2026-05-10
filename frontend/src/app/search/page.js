"use client";
import React, { useState, useEffect, useMemo } from 'react';
import { Search, Filter, Calendar, Star, Globe, ListOrdered, AlertCircle, Loader2, X, Share2, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import VibeSpinner from '@/components/spinner';

// --- MovieCard Component with Living Poster Effect ---
const MovieCard = ({ movie, index, onGenreClick }) => {
    const [isHovered, setIsHovered] = useState(false);
    const [variants, setVariants] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loadingVariants, setLoadingVariants] = useState(false);

    useEffect(() => {
        let interval;
        if (isHovered && variants.length > 1) {
            interval = setInterval(() => {
                setCurrentIndex((prev) => (prev + 1) % variants.length);
            }, 2500); // Cycle every 2.5s
        } else if (!isHovered) {
            setCurrentIndex(0);
        }
        return () => clearInterval(interval);
    }, [isHovered, variants]);

    const handleMouseEnter = async () => {
        setIsHovered(true);
        if (variants.length === 0 && !loadingVariants) {
            setLoadingVariants(true);
            try {
                const apiKey = process.env.NEXT_PUBLIC_TMDB_API_KEY;
                const response = await fetch(`https://api.themoviedb.org/3/movie/${movie.id}/images?api_key=${apiKey}&include_image_language=en,null`);
                const data = await response.json();
                if (data.posters && data.posters.length > 1) {
                    // Take up to 4 high-quality variants
                    const paths = data.posters.slice(0, 4).map(p => p.file_path);
                    setVariants(paths);
                }
            } catch (err) {
                console.error("Failed to fetch variants", err);
            } finally {
                setLoadingVariants(false);
            }
        }
    };

    const currentPoster = variants.length > 0 && isHovered 
        ? `https://image.tmdb.org/t/p/w500${variants[currentIndex]}` 
        : `https://image.tmdb.org/t/p/w500${movie.poster_path}`;

    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, duration: 0.8 }}
            whileHover={{ y: -12, scale: 1.05 }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={() => setIsHovered(false)}
            className="w-[220px] flex-shrink-0 group cursor-pointer"
        >
            <div className="relative transition-all duration-500 rounded-3xl group-hover:shadow-[0_0_60px_rgba(var(--primary-rgb),0.4)]">
                <div className="relative aspect-[2/3] rounded-3xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-md shadow-2xl transition-all duration-500 ">
                    <AnimatePresence mode='wait'>
                        <motion.img
                            key={currentPoster}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.8 }}
                            src={currentPoster}
                            alt={movie.title}
                            className='w-full h-full object-cover group-hover:scale-110 transition-transform duration-700'
                        />
                    </AnimatePresence>
                    
                    {loadingVariants && isHovered && (
                        <div className="absolute top-2 right-2 p-1.5 bg-black/50 backdrop-blur-md rounded-full">
                            <Loader2 size={12} className="animate-spin text-[var(--primary)]" />
                        </div>
                    )}
                </div>

                <div className="absolute -inset-px rounded-3xl bg-gradient-to-t from-black via-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-6 text-center z-10">
                    <div className="flex items-center justify-center gap-2 mb-3">
                        <div className="px-3 py-1 bg-[var(--primary)] text-black text-[10px] font-black rounded-full uppercase tracking-tighter">
                            {Math.round(movie.score * 100)}% Match
                        </div>
                    </div>
                    <p className="text-white/90 text-[10px] leading-relaxed font-bold italic tracking-tight">
                        "{movie.reason}"
                    </p>
                </div>
            </div>

            <h3 className='text-base font-black mt-4 text-center group-hover:text-[var(--primary)] transition-all duration-300 line-clamp-2 leading-tight tracking-tight px-2 min-h-[2.5rem] flex items-center justify-center'>
                {movie.title}
            </h3>
            <div className="flex gap-2 justify-center items-center mt-1">
                <span className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{movie.year}</span>
                <span className="w-1 h-1 bg-gray-800 rounded-full" />
                {movie.genres?.slice(0, 2).map((g, i) => (
                    <button 
                        key={i} 
                        onClick={(e) => {
                            e.stopPropagation();
                            onGenreClick(g);
                        }}
                        className="text-[10px] uppercase tracking-widest text-gray-600 font-bold hover:text-[var(--primary)] transition-colors"
                    >
                        {g}
                    </button>
                ))}
            </div>
        </motion.div>
    );
};

export default function SearchPage() {
    const inputRef = React.useRef(null);
    const [query, SetQuery] = useState("");
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(false);
    const [isSearched, setIsSearched] = useState(false);
    const [sortBy, setSortBy] = useState("match"); // match, year, rating
    const [tmdbLanguages, setTmdbLanguages] = useState([{ name: "All Languages", value: "" }]);
    
    // Advanced Filters
    const [showFilters, setShowFilters] = useState(false);
    const [minYear, setMinYear] = useState("");
    const [maxYear, setMaxYear] = useState("");
    const [language, setLanguage] = useState("");
    const [minVote, setMinVote] = useState("");
    const [resultCount, setResultCount] = useState(25);

    const resultOptions = [10, 25, 50, 100];

    useEffect(() => {
        async function fetchLanguages() {
            try {
                const apiKey = process.env.NEXT_PUBLIC_TMDB_API_KEY;
                const response = await fetch(`https://api.themoviedb.org/3/configuration/languages?api_key=${apiKey}`);
                const data = await response.json();
                if (Array.isArray(data)) {
                    const formatted = data.map(l => ({
                        name: l.english_name,
                        value: l.iso_639_1
                    })).sort((a, b) => a.name.localeCompare(b.name));
                    setTmdbLanguages([{ name: "All Languages", value: "" }, ...formatted]);
                }
            } catch (error) {
                setTmdbLanguages([
                    { name: "All Languages", value: "" },
                    { name: "English", value: "en" },
                    { name: "Korean", value: "ko" },
                    { name: "Japanese", value: "ja" },
                    { name: "French", value: "fr" },
                    { name: "Spanish", value: "es" }
                ]);
            }
        }
        fetchLanguages();

        // 1. Auto-focus on load
        inputRef.current?.focus();

        // 2. Keyboard Shortcut (/)
        const handleKeyPress = (e) => {
            if (e.key === '/' && document.activeElement !== inputRef.current) {
                e.preventDefault();
                inputRef.current?.focus();
            }
        };
        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, []);

    const clearFilters = () => {
        setMinYear("");
        setMaxYear("");
        setLanguage("");
        setMinVote("");
        setResultCount(25);
    };

    const handleGenreClick = (genre) => {
        SetQuery(genre);
        // Trigger search immediately after state update (using a small timeout or just calling handleSearch with the new value)
        // For simplicity here, we'll let the user hit Enter or click Search, 
        // but we could also auto-trigger. Let's auto-trigger for better UX.
        setTimeout(() => {
            handleSearch(genre);
        }, 100);
    };

    const handleSearch = async (overrideQuery = null) => {
        const searchQuery = overrideQuery || query;
        if (!searchQuery.trim()) return;
        setLoading(true);
        setIsSearched(true);
        try {
            // We now call our OWN internal proxy instead of the backend directly
            // This bypasses CORS and keeps your HF Token secret!
            let url = `/api/search?q=${encodeURIComponent(query)}`;
            if (minYear) url += `&min_year=${minYear}`;
            if (maxYear) url += `&max_year=${maxYear}`;
            if (language) url += `&language=${language}`;
            if (minVote) url += `&min_vote=${minVote}`;
            if (resultCount) url += `&k=${resultCount}`;

            console.log("🚀 [Search] Fetching from proxy:", url);

            const response = await fetch(url);
            console.log("📡 [Search] Status:", response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error("❌ [Search] Backend Error:", errorText);
                setMovies([]);
                return;
            }

            const data = await response.json();
            console.log("✅ [Search] Results received:", data?.length || 0);
            setMovies(data);
        } catch (error) {
            console.error("🚨 [Search] Critical Connection Failure:", error);
            setMovies([]);
        } finally {
            setLoading(false)
        }
    }

    const sortedMovies = useMemo(() => {
        if (!movies) return [];
        const sorted = [...movies];
        if (sortBy === "year") {
            return sorted.sort((a, b) => b.year - a.year);
        } else if (sortBy === "rating") {
            return sorted.sort((a, b) => b.vote - a.vote);
        }
        return sorted;
    }, [movies, sortBy]);

    return (
        <main className="min-h-screen w-full bg-black text-white flex flex-col items-center px-4 pt-32 relative overflow-y-auto overflow-x-hidden">
            <div className="mesh-gradient opacity-30 fixed inset-0 pointer-events-none" />
            
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="relative w-full max-w-4xl group z-50 mb-12"
            >
                <h1 className="font-['Arkhip'] text-5xl md:text-7xl text-center mb-8 text-white uppercase tracking-tighter leading-none"> 
                    THE PULSE <span className="text-[var(--primary)]">OF CINEMA</span>
                </h1>
                
                <div className='relative flex flex-col md:flex-row gap-4 items-stretch'>
                    <div className="relative flex-1">
                        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-[var(--primary)] transition-colors z-10">
                            <Search size={20} />
                        </div>
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder='What kind of story are you looking for? (Press "/" to focus)'
                            value={query}
                            onChange={(e) => SetQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            className="w-full bg-white/5 border border-white/10 backdrop-blur-2xl px-14 py-5 rounded-2xl outline-none focus:border-[var(--primary)]/50 focus:ring-4 ring-[var(--primary)]/10 transition-all text-lg placeholder:text-gray-500 shadow-2xl"
                        />
                    </div>
                    <div className="flex gap-4">
                        <button 
                            onClick={() => setShowFilters(!showFilters)}
                            className={`p-5 rounded-2xl border border-white/10 transition-all ${showFilters ? 'bg-[var(--primary)]/20 border-[var(--primary)]/50 text-[var(--primary)]' : 'bg-white/5 hover:bg-white/10'}`}
                        >
                            <Filter size={20} />
                        </button>
                        <button 
                            className={`bg-[var(--primary)] px-10 rounded-2xl font-black text-black uppercase tracking-widest text-xs transition-all shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ${loading ? 'opacity-50 cursor-not-allowed grayscale' : 'hover:brightness-110 active:scale-95'}`}
                            onClick={() => handleSearch()}
                            disabled={loading}
                        >
                            {loading ? "..." : "Search"}
                        </button>
                    </div>
                </div>

                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-4 flex items-start gap-3 px-6 py-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl max-w-2xl mx-auto"
                >
                    <AlertCircle size={16} className="text-[var(--primary)] mt-0.5 shrink-0" />
                    <p className="text-[11px] text-gray-400 leading-relaxed font-medium">
                        <span className="text-white font-black uppercase tracking-tighter mr-1">Pro Tip:</span>
                        Searching for a specific movie? Use the <span className="text-white">full, correct title</span> including punctuation (e.g., <span className="italic">"Singin' in the Rain"</span> instead of <span className="italic">"Singing in the rain"</span>) for the most accurate thematic siblings.
                    </p>
                </motion.div>

                <AnimatePresence>
                    {showFilters && (
                        <motion.div 
                            initial={{ height: 0, opacity: 0, y: -10 }}
                            animate={{ height: 'auto', opacity: 1, y: 0 }}
                            exit={{ height: 0, opacity: 0, y: -10 }}
                            className="overflow-hidden mt-4 grid grid-cols-2 md:grid-cols-5 gap-4 p-6 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl"
                        >
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Calendar size={12} /> Min Year
                                </label>
                                <input 
                                    type="number" 
                                    placeholder="1990"
                                    value={minYear}
                                    onChange={(e) => setMinYear(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Calendar size={12} /> Max Year
                                </label>
                                <input 
                                    type="number" 
                                    placeholder="2024"
                                    value={maxYear}
                                    onChange={(e) => setMaxYear(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Globe size={12} /> Language
                                </label>
                                <select 
                                    value={language}
                                    onChange={(e) => setLanguage(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none appearance-none cursor-pointer"
                                >
                                    {tmdbLanguages.map(lang => (
                                        <option key={lang.value} value={lang.value} className="bg-[#0a0a0a]">{lang.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Star size={12} /> Min Rating
                                </label>
                                <input 
                                    type="number" 
                                    step="0.1"
                                    placeholder="7.5"
                                    value={minVote}
                                    onChange={(e) => setMinVote(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Star size={12} /> Results
                                </label>
                                <select 
                                    value={resultCount}
                                    onChange={(e) => setResultCount(parseInt(e.target.value))}
                                    className="bg-black/20 border border-white/5 rounded-lg px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none appearance-none cursor-pointer"
                                >
                                    {resultOptions.map(opt => (
                                        <option key={opt} value={opt} className="bg-[#0a0a0a]">{opt}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex items-end pb-1">
                                <button 
                                    onClick={clearFilters}
                                    className="w-full py-2.5 rounded-lg border border-white/5 bg-white/5 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400 text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2"
                                >
                                    <X size={12} /> Clear All
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

            {isSearched && !loading && (
                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="w-full max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 mb-8 px-10"
                >
                    <div className="flex items-center gap-3 text-gray-500">
                        <AlertCircle size={14} className="text-[var(--primary)]" />
                        <p className="text-[10px] font-medium tracking-tight">
                            Showing top {sortedMovies.length} results. If the selection feels narrow, try broadening your filters or checking for typos.
                        </p>
                    </div>

                    {sortedMovies.length > 0 && (
                        <div className="flex items-center gap-4 bg-white/5 backdrop-blur-xl border border-white/10 px-6 py-3 rounded-2xl">
                            <ListOrdered size={16} className="text-[var(--primary)]" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-500">Sort By:</span>
                            <div className="flex gap-2">
                                {[
                                    { name: "Match", value: "match" },
                                    { name: "Year", value: "year" },
                                    { name: "Rating", value: "rating" }
                                ].map(option => (
                                    <button
                                        key={option.value}
                                        onClick={() => setSortBy(option.value)}
                                        className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-tighter transition-all ${sortBy === option.value ? 'bg-[var(--primary)] text-black shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]' : 'bg-white/5 text-gray-400 hover:text-white'}`}
                                    >
                                        {option.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </motion.div>
            )}

            {loading && (
                <div className="flex flex-col items-center gap-4 my-20">
                    <VibeSpinner />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--primary)] animate-pulse">Analyzing Cinematic Vibes...</p>
                </div>
            )}

            {!isSearched && !loading &&(
                <div
                    className="w-full max-w-4xl mx-auto overflow-hidden mt-8 relative"
                    style={{
                        maskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)',
                        WebkitMaskImage: 'linear-gradient(to right, transparent, black 15%, black 85%, transparent)'
                    }}
                >
                    <motion.div
                        className="flex gap-4 whitespace-nowrap px-10"
                        animate={{ x: ["0%", "-50%"] }}
                        transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
                    >
                        {[
                            "Dystopian synthwave city", "Heartfelt rural coming-of-age",
                            "Jazz-fueled heist banter", "Cosmic horror isolation",
                            "Lush atmospheric nostalgia", "Hyper-violent neon revenge",
                            "Quiet contemplative noir", "Post-apocalyptic hope"
                        ].map((vibe, index) => (
                            <button
                                key={index}
                                onClick={() => SetQuery(vibe)}
                                className="px-6 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm text-[10px] font-bold uppercase tracking-widest text-gray-400 hover:text-white hover:border-[var(--primary)]/50 hover:bg-[var(--primary)]/10 transition-all"
                            >
                                {vibe}
                            </button>
                        ))}
                    </motion.div>
                </div>
            )}

            {isSearched && !loading &&(
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8 }}
                    className="flex flex-wrap justify-center gap-10 w-full max-w-7xl mx-auto pb-40"
                >
                    {sortedMovies.map((movie, index) => (
                        <MovieCard key={movie.id} movie={movie} index={index} onGenreClick={handleGenreClick} />
                    ))}
                </motion.div>
            )}
        </main >
    );
}