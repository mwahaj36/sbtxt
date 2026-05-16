"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Search, Filter, Calendar, Star, Globe, ListOrdered, AlertCircle, Loader2, X, Share2, Check, Heart, BookMarked, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSync } from '@/components/SyncProvider';
import { useRouter } from 'next/navigation';
import { API_URL } from '@/config';

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
            whileHover={{ y: -4, scale: 1.05 }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={() => setIsHovered(false)}
            onClick={() => window.open(`https://www.themoviedb.org/movie/${movie.id}`, '_blank')}
            className="group cursor-pointer"
        >
            <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-black/40 transition-all duration-500 group-hover:shadow-[0_0_30px_rgba(255,255,255,0.15)] group-hover:border-white/30">
                <AnimatePresence mode='wait'>
                    <motion.img
                        key={currentPoster}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.8 }}
                        src={currentPoster}
                        alt={movie.title}
                        className='w-full h-full object-cover transition-transform duration-700 group-hover:scale-110'
                    />
                </AnimatePresence>
                
                {loadingVariants && isHovered && (
                    <div className="absolute top-2 right-2 p-1.5 bg-black/50 backdrop-blur-md rounded-none">
                        <Loader2 size={12} className="animate-spin text-[var(--primary)]" />
                    </div>
                )}

                <div className="absolute -inset-1 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-3 text-center">
                    {movie.is_liked && <Heart size={14} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                    {movie.taste_match && movie.taste_match > 70 && (
                        <div className="text-[9px] font-black text-[#d946ef] uppercase tracking-tighter mb-1 bg-[#d946ef]/10 px-2 py-0.5 rounded-none border border-[#d946ef]/20 flex items-center gap-1">
                            <span className="text-[6px] font-black uppercase">Taste Match</span> {movie.taste_match}%
                        </div>
                    )}
                    <div className="text-[9px] font-black text-[var(--primary)] uppercase tracking-tighter mb-2 bg-[var(--primary)]/10 px-2 py-0.5 rounded-none border border-[var(--primary)]/20">
                        {Math.round(movie.score * 100)}% MATCH
                    </div>
                    {movie.reason && (
                        <p className="text-white/80 text-[7px] leading-tight font-bold italic tracking-tight line-clamp-3">
                            "{movie.reason}"
                        </p>
                    )}
                </div>
            </div>

            <h3 className='text-[8px] font-black mt-2 text-center group-hover:text-white transition-colors uppercase tracking-tight px-1 truncate leading-none'>{movie.title}</h3>
            <p className="text-center text-[7px] text-white/40 font-bold mt-0.5 mb-1">{movie.year}</p>
            {movie.genres && movie.genres.length > 0 && (
                <div className="flex gap-1 justify-center items-center flex-wrap">
                    {movie.genres.slice(0, 2).map((g, i) => (
                        <button 
                            key={i} 
                            onClick={(e) => {
                                e.stopPropagation();
                                onGenreClick(g);
                            }}
                            className="text-[6px] uppercase tracking-widest text-white/60 font-bold hover:text-white transition-colors"
                        >
                            {g}
                        </button>
                    ))}
                </div>
            )}
        </motion.div>
    );
};

export default function SearchPage() {
    const inputRef = React.useRef(null);
    const { syncStatus } = useSync();
    const router = useRouter();
    const [query, SetQuery] = useState("");
    const [movies, setMovies] = useState([]);
    const [loading, setLoading] = useState(false);
    const [isSearched, setIsSearched] = useState(false);
    const [isDNASearch, setIsDNASearch] = useState(false);
    const [sortBy, setSortBy] = useState("match"); // match, year, rating
    const [tmdbLanguages, setTmdbLanguages] = useState([{ name: "All Languages", value: "" }]);
    const abortControllerRef = useRef(null);
    
    // Advanced Filters
    const [showFilters, setShowFilters] = useState(false);
    const [minYear, setMinYear] = useState("");
    const [maxYear, setMaxYear] = useState("");
    const [language, setLanguage] = useState("");
    const [minVote, setMinVote] = useState("");
    const [resultCount, setResultCount] = useState(25);

    // Taste Vector State
    const [hasTasteVector, setHasTasteVector] = useState(false);
    const [tasteBlend, setTasteBlend] = useState(0.5);
    const [watchlistOnly, setWatchlistOnly] = useState(false);
    const [showSeen, setShowSeen] = useState(false);
    const [tasteEnabled, setTasteEnabled] = useState(false);

    const resultOptions = [10, 25, 50, 100];
    const [placeholderIndex, setPlaceholderIndex] = useState(0);
    const placeholders = [
        "What kind of story are you looking for?",
        "Search by vibe: 'Rainy neon city noir'...",
        "Search by similarity: 'Like Inception but grounded'...",
        "Search by emotion: 'Something to make me cry'...",
        "Search by trope: 'Gritty 70s heist'...",
        "Search by setting: 'Isolated arctic horror'..."
    ];

    useEffect(() => {
        const interval = setInterval(() => {
            setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
        }, 4000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const fetchLanguages = async () => {
            try {
                const res = await fetch(`${API_URL}/api/v1/sbtxt-sync/languages`);
                const data = await res.json();
                if (data && data.length > 0) {
                    setTmdbLanguages([
                        { name: "All Languages", value: "" },
                        ...data
                    ]);
                }
            } catch (e) {
                console.error("Failed to fetch languages", e);
                setTmdbLanguages([
                    { name: "All Languages", value: "" },
                    { name: "English", value: "en" },
                    { name: "Korean", value: "ko" },
                    { name: "Japanese", value: "ja" },
                    { name: "French", value: "fr" },
                    { name: "Spanish", value: "es" }
                ]);
            }
        };
        fetchLanguages();

        // Check taste vector status
        const token = localStorage.getItem("token");
        if (token) {
            fetch(`${API_URL}/api/v1/sbtxt-auth/taste`, {
                headers: { "Authorization": `Bearer ${token}` }
            })
            .then(res => {
                if (res.status === 401) {
                    localStorage.removeItem("token");
                    window.location.reload();
                    return null;
                }
                return res.json();
            })
            .then(data => {
                if (data) setHasTasteVector(data.has_taste_vector);
            })
            .catch(() => {});
        }

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
    }, [syncStatus.status]);

    const clearFilters = () => {
        setMinYear("");
        setMaxYear("");
        setLanguage("");
        setMinVote("");
        setResultCount(25);
    };

    const handleBack = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        setIsSearched(false);
        setIsDNASearch(false);
        setMovies([]);
        setLoading(false);
        SetQuery("");
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

    const handleForYou = () => {
        SetQuery("");
        setLoading(true);
        setIsSearched(true);
        setIsDNASearch(true);
        handleSearch("", true);
    };

    const handleSearch = async (overrideQuery = null, forYou = false) => {
        const searchQuery = overrideQuery !== null ? overrideQuery : query;
        if (!searchQuery.trim() && !forYou) return;

        // Abort previous request
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        abortControllerRef.current = new AbortController();

        setLoading(true);
        setIsSearched(true);
        try {
            let url = `/api/search?q=${encodeURIComponent(searchQuery)}`;
            
            // Filters only apply to regular searches, "For You" (Lucky) is unconstrained
            if (!forYou) {
                if (minYear) url += `&min_year=${minYear}`;
                if (maxYear) url += `&max_year=${maxYear}`;
                if (language) url += `&language=${language}`;
                if (minVote) url += `&min_vote=${minVote}`;
            }
            
            if (resultCount) url += `&k=${resultCount}`;

            // Taste personalization params
            const token = localStorage.getItem("token");
            if (token && hasTasteVector) {
                if (tasteEnabled || forYou) {
                    url += `&taste_blend=${forYou ? 1.0 : tasteBlend}`;
                }
                if (watchlistOnly) {
                    url += `&watchlist_only=true`;
                }
                if (showSeen) {
                    url += `&show_seen=true`;
                }
            }

            console.log("🚀 [Search] Fetching from proxy:", url);

            const headers = {};
            if (token) {
                headers['x-user-token'] = token;
            }

            const response = await fetch(url, { 
                headers,
                signal: abortControllerRef.current.signal 
            });

            if (response.status === 401) {
                localStorage.removeItem("token");
                router.push("/auth");
                return;
            }

            if (!response.ok) {
                const errorText = await response.text();
                console.error("❌ [Search] Backend Error:", errorText);
                setMovies([]);
                return;
            }

            const data = await response.json();
            console.log("✅ [Search] Results received:", data?.length || 0);
            
            if (token && data && data.length > 0) {
                try {
                    const tmdbIds = data.map(m => m.id);
                    const likedRes = await fetch(`${API_URL}/api/v1/sbtxt-sync/check_liked`, {
                        method: "POST",
                        headers: { 
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${token}`
                        },
                        body: JSON.stringify({ tmdb_ids: tmdbIds })
                    });
                    
                    if (likedRes.ok) {
                        const likedData = await likedRes.json();
                        data.forEach(m => {
                            if (likedData[m.id]) {
                                m.is_liked = true;
                            }
                        });
                    }
                } catch (e) {
                    console.error("Failed to check liked status", e);
                }
            }
            
            setMovies(data);
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log("🛑 [Search] Request aborted by user.");
                return;
            }
            console.error("🚨 [Search] Critical Connection Failure:", error);
            setMovies([]);
        } finally {
            setLoading(false);
        }
    };

    const sortedMovies = useMemo(() => {
        if (!movies) return [];
        const sorted = [...movies];
        if (sortBy === "year") {
            return sorted.sort((a, b) => b.year - a.year);
        } else if (sortBy === "rating") {
            return sorted.sort((a, b) => b.vote - a.vote);
        } else if (sortBy === "taste") {
            return sorted.sort((a, b) => (b.taste_match || 0) - (a.taste_match || 0));
        }
        return sorted;
    }, [movies, sortBy]);



    return (
        <main className={`min-h-screen w-full bg-black text-white flex flex-col items-center px-4 relative overflow-y-auto overflow-x-hidden transition-all duration-700 ${isSearched ? 'pt-20 md:pt-24' : 'pt-32'}`}>
            <div className="mesh-gradient opacity-30 fixed inset-0 pointer-events-none" />
            
            <motion.div
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`relative w-full transition-all duration-700 z-50 ${isSearched ? 'max-w-7xl mb-8 flex flex-col md:flex-row items-center gap-4' : 'max-w-4xl mb-12'}`}
            >
                {!isSearched && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="mb-12 text-center"
                    >
                        <h1 className="font-['Arkhip'] text-3xl md:text-7xl mb-8 text-white uppercase tracking-tighter leading-none px-4"> 
                            CINEMA, <span className="text-[var(--primary)]">BEYOND THE TAGS</span>
                        </h1>
                    </motion.div>
                )}

                {isDNASearch && isSearched && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex-1 flex flex-col md:flex-row items-center justify-between gap-6 p-5 bg-[#d946ef]/5 border border-[#d946ef]/20 backdrop-blur-2xl"
                    >
                        <div className="flex items-center gap-6">
                            <div className="flex flex-col gap-1">
                                <h2 className="text-xs font-black uppercase tracking-[0.4em] text-[#d946ef]">Neural Discovery Active</h2>
                                <p className="text-[10px] text-gray-500 font-medium uppercase tracking-widest">
                                    Personalized results based on your ratings
                                </p>
                            </div>
                        </div>
                        <button 
                            onClick={handleBack}
                            className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-all group"
                        >
                            <span>Exit Discovery</span>
                        </button>
                    </motion.div>
                )}

                {isSearched && !isDNASearch && (
                    <motion.button
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        onClick={handleBack}
                        className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-all mr-4 group"
                    >
                        <span>Back</span>
                    </motion.button>
                )}
                
                {(!isSearched || (isSearched && !isDNASearch)) && (
                    <form 
                        onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
                        className={`relative flex flex-col md:flex-row gap-4 items-stretch transition-all duration-700 ${isSearched ? 'flex-1' : 'w-full'}`}
                    >
                        <div className="relative flex-1">
                            <input
                                ref={inputRef}
                                type="text"
                                placeholder={placeholders[placeholderIndex]}
                                autoComplete="off"
                                value={query}
                                onChange={(e) => SetQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                className={`w-full bg-white/5 border border-white/10 backdrop-blur-2xl px-10 md:px-14 rounded-none outline-none focus:border-[var(--primary)]/50 focus:ring-4 ring-[var(--primary)]/10 transition-all placeholder:text-gray-400/30 shadow-2xl ${isSearched ? 'py-3 text-sm md:text-base' : 'py-4 md:py-5 text-base md:text-lg'}`}
                            />
                        </div>
                        <div className="flex gap-2 w-full md:w-auto">
                            <button 
                                type="button"
                                onClick={() => setShowFilters(!showFilters)}
                                className={`flex-1 md:flex-none p-4 md:p-5 rounded-none border border-white/10 transition-all ${showFilters ? 'bg-[var(--primary)]/20 border-[var(--primary)]/50 text-[var(--primary)]' : 'bg-white/5 hover:bg-white/10'} ${isSearched ? 'py-3' : ''}`}
                            >
                                <Filter size={18} className="mx-auto" />
                            </button>
                            <button 
                                type="submit"
                                className={`flex-[3] md:flex-none bg-[var(--primary)] px-8 md:px-10 rounded-none font-black text-black uppercase tracking-widest text-[10px] md:text-xs transition-all shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] ${loading ? 'opacity-50 cursor-not-allowed grayscale' : 'hover:brightness-110 active:scale-95'} ${isSearched ? 'py-3' : ''}`}
                                disabled={loading}
                            >
                                {loading ? "..." : "Search"}
                            </button>
                        </div>
                    </form>
                )}

                {!isSearched && (
                    <>
                        <div className="px-10 mt-3 flex flex-col gap-1 opacity-60">
                            <div className="flex items-center justify-between">
                                <p className="text-[11px] text-gray-300 font-medium tracking-wide flex items-center gap-3">
                                    <span className="text-gray-100 font-black uppercase tracking-widest text-[9px]">Pro Tip</span>
                                    Use full movie titles for accurate thematic siblings.
                                </p>
                            </div>
                        </div>

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
                                    "Quiet contemplative noir", "Post-apocalyptic hope",
                                    "Dystopian synthwave city", "Heartfelt rural coming-of-age",
                                    "Jazz-fueled heist banter", "Cosmic horror isolation"
                                ].map((vibe, index) => (
                                    <button
                                        key={index}
                                        onClick={() => SetQuery(vibe)}
                                        className="px-6 py-2 rounded-none border border-white/10 bg-white/5 backdrop-blur-sm text-[10px] font-bold uppercase tracking-widest text-gray-400 hover:text-white hover:border-[var(--primary)]/50 hover:bg-[var(--primary)]/10 transition-all"
                                    >
                                        {vibe}
                                    </button>
                                ))}
                            </motion.div>
                        </div>

                        {hasTasteVector && (
                            <motion.div 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mt-8 px-10"
                            >
                                <button 
                                    onClick={handleForYou}
                                    className="group w-full p-6 bg-[#d946ef]/5 border border-[#d946ef]/20 rounded-none flex items-center justify-between cursor-pointer hover:bg-[#d946ef]/10 hover:border-[#d946ef]/40 transition-all shadow-[0_0_50px_rgba(217,70,239,0.05)]"
                                >
                                    <div className="flex items-center gap-6">
                                        <div className="flex flex-col gap-1 text-left">
                                            <span className="text-xs font-black uppercase tracking-[0.3em] text-[#d946ef]">Neural Discovery Active</span>
                                            <p className="text-[10px] text-gray-500 font-medium uppercase tracking-widest leading-relaxed">
                                                Discover films semantically matched to your taste profile.
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4 text-[#d946ef]">
                                        <span className="text-[10px] font-black uppercase tracking-widest opacity-40 group-hover:opacity-100 transition-opacity">Launch</span>
                                        <ChevronRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </button>
                            </motion.div>
                        )}
                    </>
                )}

                <AnimatePresence>
                    {showFilters && (
                        <motion.div 
                            initial={{ height: 0, opacity: 0, y: -10 }}
                            animate={{ height: 'auto', opacity: 1, y: 0 }}
                            exit={{ height: 0, opacity: 0, y: -10 }}
                            className="overflow-hidden mt-4 grid grid-cols-2 md:grid-cols-5 gap-4 p-6 bg-white/5 border border-white/10 rounded-none backdrop-blur-xl"
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
                                    className="bg-black/20 border border-white/5 rounded-none px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
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
                                    className="bg-black/20 border border-white/5 rounded-none px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Globe size={12} /> Language
                                </label>
                                <select 
                                    value={language}
                                    onChange={(e) => setLanguage(e.target.value)}
                                    className="bg-black/20 border border-white/5 rounded-none px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none appearance-none cursor-pointer"
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
                                    className="bg-black/20 border border-white/5 rounded-none px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none"
                                />
                            </div>
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                    <Star size={12} /> Results
                                </label>
                                <select 
                                    value={resultCount}
                                    onChange={(e) => setResultCount(parseInt(e.target.value))}
                                    className="bg-black/20 border border-white/5 rounded-none px-3 py-2 text-sm focus:border-[var(--primary)]/50 outline-none appearance-none cursor-pointer"
                                >
                                    {resultOptions.map(opt => (
                                        <option key={opt} value={opt} className="bg-[#0a0a0a]">{opt}</option>
                                    ))}
                                </select>
                            </div>

                            {hasTasteVector && (
                                <>
                                    <div className="md:col-span-5 h-[1px] bg-white/5 my-2" />
                                    
                                    <div className="flex flex-col gap-3 md:col-span-3 justify-end pb-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="text-[10px] font-black uppercase tracking-widest text-[#d946ef] flex items-center gap-2">
                                                Taste Influence
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <button 
                                                    onClick={() => setTasteEnabled(!tasteEnabled)}
                                                    className={`px-3 py-1 text-[8px] font-black uppercase tracking-widest transition-all ${tasteEnabled ? 'bg-[#d946ef] text-black' : 'bg-white/5 text-white/40'}`}
                                                >
                                                    {tasteEnabled ? 'Enabled' : 'Disabled'}
                                                </button>
                                                <span className="text-[10px] font-black text-white/60">{Math.round(tasteBlend * 100)}%</span>
                                            </div>
                                        </div>
                                        <div className="h-10 flex items-center">
                                            <input 
                                                type="range" 
                                                min="0" 
                                                max="1" 
                                                step="0.05"
                                                value={tasteBlend}
                                                onChange={(e) => {
                                                    setTasteBlend(parseFloat(e.target.value));
                                                    if (parseFloat(e.target.value) > 0) setTasteEnabled(true);
                                                }}
                                                className="w-full accent-[#d946ef] bg-white/5 h-1 rounded-none appearance-none cursor-pointer"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex flex-col gap-3 md:col-span-2">
                                        <label className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em] flex items-center gap-2">
                                            <BookMarked size={12} /> Search Area
                                        </label>
                                        <div className="flex gap-2">
                                            <button 
                                                onClick={() => setWatchlistOnly(!watchlistOnly)}
                                                className={`flex-1 h-10 px-4 border text-[9px] font-black uppercase tracking-[0.2em] transition-all flex items-center justify-between ${watchlistOnly ? 'border-[#d946ef]/50 bg-[#d946ef]/5 text-[#d946ef]' : 'border-white/10 bg-black/20 text-white/40'}`}
                                            >
                                                <span>Watchlist</span>
                                                <div className={`w-3 h-3 rounded-none border ${watchlistOnly ? 'bg-[#d946ef] border-[#d946ef]' : 'border-white/20'}`} />
                                            </button>
                                            <button 
                                                onClick={() => setShowSeen(!showSeen)}
                                                className={`flex-1 h-10 px-4 border text-[9px] font-black uppercase tracking-[0.2em] transition-all flex items-center justify-between ${showSeen ? 'border-white/50 bg-white/5 text-white' : 'border-white/10 bg-black/20 text-white/40'}`}
                                            >
                                                <span>Include Seen</span>
                                                <div className={`w-3 h-3 rounded-none border ${showSeen ? 'bg-white border-white' : 'border-white/20'}`} />
                                            </button>
                                        </div>
                                    </div>
                                </>
                            )}

                            <div className="md:col-span-5 flex justify-center mt-6 pt-4 border-t border-white/5">
                                <button 
                                    onClick={clearFilters}
                                    className="px-8 py-2.5 rounded-none border border-white/5 bg-white/5 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-400 text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2"
                                >
                                    <X size={12} /> Reset All Filters
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
                    className="w-full max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 md:gap-6 mb-8 px-6 md:px-10"
                >
                    <div className="flex items-start md:items-center gap-3 text-gray-500">
                        <AlertCircle size={14} className="text-[var(--primary)] shrink-0 mt-0.5 md:mt-0" />
                        <p className="text-[9px] md:text-[10px] font-medium tracking-tight">
                            Showing top {sortedMovies.length} results. If the selection feels narrow, try broadening your filters.
                        </p>
                    </div>

                    {sortedMovies.length > 0 && (
                        <div className="w-full md:w-auto flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 px-4 md:px-6 py-2.5 md:py-3 rounded-none overflow-x-auto whitespace-nowrap">
                            <ListOrdered size={14} className="text-[var(--primary)] shrink-0" />
                            <span className="text-[9px] font-black uppercase tracking-widest text-gray-500">Sort:</span>
                            <div className="flex gap-2">
                                {[
                                    { name: "Match", value: "match" },
                                    ...(hasTasteVector ? [{ name: "My Taste", value: "taste" }] : []),
                                    { name: "Year", value: "year" },
                                    { name: "Rating", value: "rating" }
                                ].map(option => (
                                    <button
                                        key={option.value}
                                        onClick={() => setSortBy(option.value)}
                                        className={`px-4 py-1.5 rounded-none text-[10px] font-black uppercase tracking-tighter transition-all ${sortBy === option.value ? 'bg-[var(--primary)] text-black shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]' : 'bg-white/5 text-gray-400 hover:text-white'}`}
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
                    <Loader2 className="animate-spin text-[var(--primary)]" size={32} />
                    <p className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--primary)] animate-pulse">Analyzing Cinematic Vibes...</p>
                </div>
            )}

            {/* Vibe Chips removed from here as they are now integrated above */}

            {isSearched && !loading &&(
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.8 }}
                    className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-x-4 gap-y-6 w-full max-w-7xl mx-auto pb-40 px-8"
                >
                    {sortedMovies.map((movie, index) => (
                        <MovieCard key={movie.id} movie={movie} index={index} onGenreClick={handleGenreClick} />
                    ))}
                </motion.div>
            )}
        </main >
    );
}