"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSync } from '@/components/SyncProvider';
import { Loader2, Film, Star, ChevronLeft, ChevronRight, Heart, Search, ChevronDown, RefreshCw, ExternalLink, Settings, Dna } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { API_URL } from '@/config';

export default function ProfilePage() {
    const router = useRouter();
    const { syncStatus, triggerSync } = useSync();
    const [profile, setProfile] = useState(null);
    const [recent, setRecent] = useState([]);
    const [watched, setWatched] = useState({ movies: [], total: 0, page: 1, pages: 1 });
    const [watchlist, setWatchlist] = useState({ movies: [], total: 0, page: 1, pages: 1 });
    const [isLoading, setIsLoading] = useState(true);
    const [libLoading, setLibLoading] = useState(false);
    const [watchLoading, setWatchLoading] = useState(false);
    const [watchedSearch, setWatchedSearch] = useState("");
    const [watchlistSearch, setWatchlistSearch] = useState("");
    const [localWatchedSearch, setLocalWatchedSearch] = useState("");
    const [localWatchlistSearch, setLocalWatchlistSearch] = useState("");
    const [watchedPage, setWatchedPage] = useState(1);
    const [watchlistPage, setWatchlistPage] = useState(1);
    const [isSyncing, setIsSyncing] = useState(false);
    const [tasteData, setTasteData] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/auth");
                return;
            }
            setIsLoading(true);
            try {
                // Profile Turbo: Fetch Bundle (Profile + DNA + Recent 4) in one go
                const bundleRes = await fetch(`${API_URL}/api/v1/sbtxt-auth/bundle`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (bundleRes.status === 401) {
                    localStorage.removeItem("token");
                    router.push("/auth");
                    return;
                }

                const bundle = await bundleRes.json();
                
                // Guard: Redirect incomplete accounts to onboarding
                if (!bundle.profile?.letterboxd_username) {
                    router.push("/onboarding");
                    return;
                }

                if (bundle.profile) {
                    setProfile(bundle.profile);
                }
                if (bundle.taste) {
                    setTasteData(bundle.taste);
                }
                if (bundle.recent) {
                    setRecent(bundle.recent);
                }

            } catch (e) {
                if (process.env.NODE_ENV === 'development') console.error("Profile bundle fetch failed", e);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [syncStatus.status]);

    useEffect(() => {
        const fetchLibraries = async () => {
            setLibLoading(true);
            setWatchLoading(true);
            const token = localStorage.getItem("token");
            try {
                const [resWatched, resWatchlist] = await Promise.all([
                    fetch(`${API_URL}/api/v1/sbtxt-sync/library?type=watched&page=${watchedPage}&query=${watchedSearch}`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    }),
                    fetch(`${API_URL}/api/v1/sbtxt-sync/library?type=watchlist&page=${watchlistPage}&query=${watchlistSearch}`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    })
                ]);

                const [dataWatched, dataWatchlist] = await Promise.all([
                    resWatched.json(),
                    resWatchlist.json()
                ]);

                setWatched(dataWatched);
                setWatchlist(dataWatchlist);
            } catch (e) {
                if (process.env.NODE_ENV === 'development') console.error("Library fetch failed", e);
            } finally {
                setLibLoading(false);
                setWatchLoading(false);
            }
        };

        const timeoutId = setTimeout(() => {
            fetchLibraries();
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [watchedPage, watchlistPage, watchedSearch, watchlistSearch, syncStatus.status]);

    const triggerLiveSync = async () => {
        setIsSyncing(true);
        const token = localStorage.getItem("token");
        try {
            await fetch(`${API_URL}/api/v1/sbtxt-sync/live`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` }
            });
            triggerSync(100);
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error("Live sync trigger failed", e);
        } finally {
            setTimeout(() => setIsSyncing(false), 2000);
        }
    };

    const handleMovieClick = (tmdbId) => {
        if (tmdbId) {
            window.open(`https://www.themoviedb.org/movie/${tmdbId}`, '_blank');
        }
    };

    const handleSearch = (type) => {
        if (type === 'watched') {
            setWatchedSearch(localWatchedSearch);
            setWatchedPage(1);
        } else {
            setWatchlistSearch(localWatchlistSearch);
            setWatchlistPage(1);
        }
    };

    const handleKeyDown = (e, type) => {
        if (e.key === 'Enter') {
            handleSearch(type);
        }
    };

    const [isDevEmpty, setIsDevEmpty] = useState(false);

    useEffect(() => {
        const handleDevForce = (e) => setIsDevEmpty(e.detail);
        document.addEventListener('dev:forceEmpty', handleDevForce);
        return () => document.removeEventListener('dev:forceEmpty', handleDevForce);
    }, []);

    // Logic updated to respect dev mode
    const isActuallyEmpty = (watched.movies.length === 0 && !watchLoading) || isDevEmpty;

    if (isLoading) return (
        <div className="h-screen w-full flex items-center justify-center bg-black">
            <Loader2 className="animate-spin text-[var(--primary)]" size={48} />
        </div>
    );

    // Profile Lock: If currently syncing, show full-page status instead of profile
    if (syncStatus.status === 'syncing') {
        return (
            <div className="h-screen w-full flex flex-col items-center justify-center bg-[#050505] p-8 text-center">
                <div className="w-64 h-[1px] bg-white/10 relative overflow-hidden mb-12">
                    <motion.div 
                        initial={{ x: "-100%" }}
                        animate={{ x: "100%" }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 bg-[var(--primary)]"
                    />
                </div>
                <h2 className="text-3xl font-black uppercase tracking-tighter text-white mb-6" style={{ fontFamily: 'Arkhip' }}>
                    Vault <span className="text-[#d946ef]">Syncing</span>
                </h2>
                <p className="text-[10px] text-white/30 font-bold uppercase tracking-[0.4em] leading-relaxed max-w-sm">
                    {syncStatus.message || "Calibrating neural discovery engine..."}
                </p>
                <div className="mt-12 text-[9px] font-black uppercase tracking-widest text-[var(--primary)] opacity-40">
                    {syncStatus.processed} / {syncStatus.total || 0} Films Resolved
                </div>
            </div>
        );
    }

    return (
        <main className="w-full bg-black text-white">
            
            {/* DECK 1: IDENTITY */}
            <section className="min-h-screen w-full snap-start flex flex-col items-center justify-center pt-24 pb-12 px-8 md:px-20 relative bg-[#050505] overflow-hidden">
                <div className="absolute inset-0 mesh-gradient opacity-10" />
                
                <div className="max-w-7xl mx-auto w-full h-full md:max-h-[80vh] flex flex-col md:flex-row gap-12 md:gap-20 z-10 items-center">
                    
                    {/* LEFT COLUMN: Identity Info */}
                    <div className="w-full md:w-[400px] flex flex-col items-center justify-center gap-8 md:gap-12 shrink-0">
                        <div className="flex flex-col items-center text-center">
                            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="relative group shrink-0 mb-8">
                                <div className="absolute -inset-2 bg-gradient-to-r from-[var(--primary)]/20 via-white/10 to-transparent rounded-none blur opacity-20 group-hover:opacity-40 transition-opacity" />
                                <img 
                                    src={profile?.avatar || "https://a.ltrbxd.com/resized/avatar/twitter/4/8/9/4/6/7/shard/2126200257/avatar-80.jpg"} 
                                    className="relative w-32 h-32 rounded-none border border-white/10 object-cover shadow-2xl"
                                    alt="Avatar"
                                />
                            </motion.div>

                            <h1 className="text-3xl md:text-5xl font-black uppercase tracking-tighter mb-2" style={{ fontFamily: 'Arkhip' }}>
                                {profile?.name || profile?.username}
                            </h1>
                            <div className="flex items-center justify-center gap-4 mb-6">
                                <span className="text-white text-[10px] font-black uppercase tracking-widest px-4 py-1.5 bg-white/5 rounded-none border border-white/10">
                                    {profile?.films_count || 0} Films
                                </span>
                            </div>
                            <p className="text-xs text-white/40 leading-relaxed max-w-sm mb-8">
                                {profile?.bio || "No bio available."}
                            </p>
                            <div className="flex gap-3">
                                <div className="relative group">
                                    <button onClick={triggerLiveSync} disabled={isSyncing} className="px-6 py-3 bg-[var(--primary)] text-black text-[9px] font-black uppercase tracking-widest hover:bg-[var(--primary)]/90 transition-all flex items-center gap-2">
                                        {isSyncing ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />}
                                        {isSyncing ? "Syncing..." : "Sync Latest"}
                                    </button>
                                    <div className="hidden group-hover:block absolute top-full mt-2 p-3 bg-black/90 border border-white/10 text-[8px] lowercase font-medium tracking-normal text-gray-400 w-48 text-left backdrop-blur-xl z-[100] shadow-2xl">
                                        quick-sync for recent watches. for full library cleanup or syncing deletions, use <span className="text-white">zip sync</span> in settings.
                                    </div>
                                </div>
                                <button 
                                    onClick={() => window.open(`https://letterboxd.com/${profile?.username}`, '_blank')}
                                    className="px-6 py-3 bg-white/5 border border-white/10 text-white/60 text-[9px] font-black uppercase tracking-widest hover:bg-[#ff8000]/10 hover:text-[#ff8000] hover:border-[#ff8000]/30 transition-all flex items-center gap-2"
                                >
                                    <ExternalLink size={10} /> Letterboxd
                                </button>
                                <button onClick={() => router.push('/settings')} className="px-6 py-3 bg-white/5 border border-white/10 text-white/60 text-[9px] font-black uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all flex items-center gap-2">
                                    <Settings size={10} /> Settings
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN: Movie Sections Highlights */}
                    <div className="flex-1 flex flex-col justify-between h-full py-4 overflow-hidden">
                        {/* TOP FAVORITES */}
                        <div className="w-full flex flex-col">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-white/20 border-b border-white/5 pb-2 mb-4 flex items-center gap-2">
                                 Favorites
                            </h3>
                            <div className="grid grid-cols-4 gap-2 md:gap-4">
                                {(profile?.favorites || []).slice(0, 4).map((fav, i) => (
                                    <motion.div key={i} whileHover={{ y: -4, scale: 1.05 }} className="group cursor-pointer relative" onClick={() => handleMovieClick(fav.tmdb_id)}>
                                        <div className="aspect-[2/3] overflow-hidden border border-white/10 bg-white/5 group-hover:border-white/40 transition-all shadow-2xl">
                                            <img src={fav.poster_path ? (fav.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${fav.poster_path}` : fav.poster_path) : `https://via.placeholder.com/400x600?text=?`} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt="Fav" />
                                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                <Heart size={16} className="fill-[#ff8000] text-[#ff8000]" />
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        {/* RECENTLY WATCHED */}
                        <div className="w-full flex flex-col">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-white/20 border-b border-white/5 pb-2 mb-4 flex items-center gap-2">
                                 Recently Watched
                            </h3>
                            <div className="grid grid-cols-4 gap-2 md:gap-4">
                                {recent.slice(0, 4).map((movie, i) => (
                                    <motion.div key={i} whileHover={{ y: -4, scale: 1.05 }} className="group cursor-pointer" onClick={() => handleMovieClick(movie.tmdb_id)}>
                                        <div className="relative aspect-[2/3] overflow-hidden border border-white/10 bg-white/5 group-hover:border-white/40 transition-all shadow-2xl">
                                            <img src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" alt="Recent" />
                                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2 text-center">
                                                {movie.is_liked && <Heart size={14} className="fill-[#ff8000] text-[#ff8000] mb-1" />}
                                                <span className="text-[10px] font-black text-white uppercase tracking-tighter">★ {movie.rating || 'N/A'}</span>
                                            </div>
                                        </div>
                                        <h4 className="text-[7px] font-black mt-2 truncate uppercase text-white/40 group-hover:text-white transition-colors tracking-widest">{movie.title}</h4>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>                <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-30">
                    <span className="text-[7px] font-black uppercase tracking-[0.4em] text-white/40">Scroll to see your DNA</span>
                    <ChevronDown size={24} className="text-white animate-bounce" />
                </div>
            </section>

            {/* DECK 2: TASTE DNA */}
            <section className="min-h-screen w-full snap-start flex flex-col items-center justify-center py-24 px-8 md:px-20 relative bg-black overflow-hidden border-t border-white/5">
                <div className="absolute inset-0 bg-gradient-to-b from-[#d946ef]/5 to-transparent opacity-20" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#d946ef]/10 rounded-full blur-[120px] opacity-20 animate-pulse" />
                
                <div className="max-w-6xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-24 z-10 items-center">
                    {/* LEFT: Explanation */}
                    <div className="flex flex-col items-start text-left">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-12 h-[1px] bg-[#d946ef]" />
                            <span className="text-[#d946ef] text-[10px] font-black uppercase tracking-[0.4em]">Cinematic Signature</span>
                        </div>
                        <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tighter text-white mb-8 leading-tight md:leading-none" style={{ fontFamily: 'Arkhip' }}>
                            Your<br/><span className="text-[#d946ef]">Taste DNA</span>
                        </h2>
                        <div className="space-y-6 text-sm text-white/50 leading-relaxed max-w-md font-medium mb-12">
                            <p>
                                Every movie you've ever watched, rated, or liked has been processed through our 
                                <span className="text-white"> Neural Embedding Engine</span>. We translate cinema into a high-dimensional mathematical space.
                            </p>
                            <p>
                                By calculating the <span className="text-white">Centroid of your Cinematic Universe</span>, we've distilled your identity into these core genetic markers. This is your unique signature.
                            </p>
                        </div>

                        {/* DNA FACTORS GRID */}
                        <div className="grid grid-cols-2 gap-px bg-white/5 border border-white/5">
                            <div className="p-4 bg-black group hover:bg-white/5 transition-colors">
                                <h4 className="text-[8px] font-black uppercase tracking-widest text-[#d946ef] mb-1">Quadratic Rating</h4>
                                <p className="text-[7px] text-white/40 leading-tight uppercase font-bold tracking-tight">5-star films carry 3x more influence than average watches.</p>
                            </div>
                            <div className="p-4 bg-black group hover:bg-white/5 transition-colors">
                                <h4 className="text-[8px] font-black uppercase tracking-widest text-[#d946ef] mb-1">Affinity Bonus</h4>
                                <p className="text-[7px] text-white/40 leading-tight uppercase font-bold tracking-tight">Liked films are prioritized during vectorization.</p>
                            </div>
                            <div className="p-4 bg-black group hover:bg-white/5 transition-colors">
                                <h4 className="text-[8px] font-black uppercase tracking-widest text-[#d946ef] mb-1">Temporal Drift</h4>
                                <p className="text-[7px] text-white/40 leading-tight uppercase font-bold tracking-tight">Recent watches (6mo) are weighted 20% higher.</p>
                            </div>
                            <div className="p-4 bg-black group hover:bg-white/5 transition-colors">
                                <h4 className="text-[8px] font-black uppercase tracking-widest text-[#d946ef] mb-1">Noise Filtering</h4>
                                <p className="text-[7px] text-white/40 leading-tight uppercase font-bold tracking-tight">Generic tropes are filtered to find your unique subtext.</p>
                            </div>
                        </div>
                        
                        <p className="text-[10px] uppercase tracking-widest font-black text-white/20 pt-8">
                            Analyzed {tasteData?.movie_count || profile?.films_count || 0} unique data points
                        </p>
                    </div>

                    {/* RIGHT: Visualization */}
                    {tasteData && (
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            className="p-10 bg-white/5 border border-white/10 relative group w-full"
                        >
                            <div className="space-y-8 relative z-10">
                                {tasteData.top_genres.map((g, idx) => (
                                    <div key={idx} className="flex flex-col gap-3">
                                        <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-[0.3em]">
                                            <span className="text-white/60">{g.genre}</span>
                                            <span className="text-[#d946ef]">{g.affinity}% Affinity</span>
                                        </div>
                                        <div className="h-2 w-full bg-white/5 rounded-none overflow-hidden">
                                            <motion.div 
                                                initial={{ width: 0 }}
                                                whileInView={{ width: `${g.affinity}%` }}
                                                transition={{ duration: 1.5, delay: idx * 0.1, ease: "circOut" }}
                                                className="h-full bg-[#d946ef]"
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>

                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-30">
                    <span className="text-[7px] font-black uppercase tracking-[0.4em] text-white/40">Scroll to see your films</span>
                    <ChevronDown size={24} className="text-white animate-bounce" />
                </div>
            </section>

            {/* DECK 3: FILMS */}
            <section className="h-screen w-full snap-start flex flex-col pt-24 px-8 pb-12 relative overflow-hidden bg-[#0a0a0a]">
                <div className="max-w-7xl mx-auto w-full flex flex-col h-full overflow-hidden relative">
                    
                    {/* Header Pinned */}
                    <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-6 shrink-0">
                        <div className="flex items-center gap-4">
                            <h2 className="font-['Arkhip'] text-2xl md:text-3xl font-black uppercase tracking-tighter text-white">Films</h2>
                        </div>

                        <div className="flex flex-col md:flex-row items-center gap-2 w-full md:w-auto mt-4 md:mt-0">
                            <div className="relative group w-full md:w-auto">
                                <Search 
                                    className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-white transition-colors cursor-pointer" 
                                    size={12} 
                                    onClick={() => handleSearch('watched')}
                                />
                                <input 
                                    type="text"
                                    placeholder="SEARCH FILMS..."
                                    value={localWatchedSearch}
                                    onChange={(e) => setLocalWatchedSearch(e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(e, 'watched')}
                                    className="bg-black/20 border border-white/5 rounded-none pl-10 pr-6 py-2 text-[9px] uppercase font-black tracking-[0.2em] outline-none focus:border-white/30 transition-all w-56"
                                />
                            </div>
                            <button 
                                onClick={() => handleSearch('watched')}
                                className="px-4 py-2 bg-white/5 border border-white/10 text-white/40 text-[8px] font-black uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all"
                            >
                                Search
                            </button>
                        </div>
                    </div>

                    {/* Scrollable Grid Area */}
                    <div className="flex-1 overflow-y-auto pr-2 hide-scrollbar pb-8">
                        {libLoading ? (
                            <div className="h-full w-full flex items-center justify-center min-h-[300px]">
                                <Loader2 className="animate-spin text-[var(--primary)]" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-8 xl:grid-cols-10 gap-x-3 gap-y-5 content-start">
                                {isActuallyEmpty ? (
                                    <div className="h-full w-full flex flex-col items-center justify-center min-h-[500px] gap-8 col-span-10">
                                        <div className="p-16 bg-white/[0.01] border border-white/5 rounded-none flex flex-col items-center text-center max-w-sm">
                                            <h3 className="text-2xl font-black uppercase tracking-tighter text-white/40 mb-6" style={{ fontFamily: 'Arkhip' }}>
                                                Vault <span className="text-white/10">Offline</span>
                                            </h3>
                                            <p className="text-[9px] text-white/20 font-bold uppercase tracking-[0.3em] leading-loose mb-12 max-w-[220px]">
                                                Synchronize your history to calibrate the neural discovery engine.
                                            </p>
                                            <button 
                                                onClick={() => {
                                                    const syncInput = document.getElementById('letterboxd-sync-input');
                                                    if (syncInput) syncInput.click();
                                                }}
                                                className="w-full py-5 bg-white text-black font-black uppercase tracking-[0.5em] text-[9px] hover:bg-[#d946ef] hover:text-white transition-all"
                                            >
                                                Activate Sync
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    watched.movies.slice(0, 30).map((movie, i) => (
                                        <motion.div 
                                            key={i}
                                            whileHover={{ y: -4, scale: 1.05 }}
                                            className="group cursor-pointer"
                                            onClick={() => handleMovieClick(movie.tmdb_id)}
                                        >
                                            <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-black/40 transition-all duration-500 group-hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] group-hover:border-white/30">
                                                <img 
                                                    src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w200${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/200x300?text=?`} 
                                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                    alt="Poster"
                                                />
                                                <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col justify-center items-center p-3 text-center">
                                                    {movie.is_liked && <Heart size={12} className="fill-[#ff8000] text-[#ff8000] mb-1.5" />}
                                                    <h3 className="text-[9px] font-black text-white uppercase tracking-tighter leading-tight mb-1.5 line-clamp-3">{movie.title}</h3>
                                                    {movie.rating && (
                                                        <div className="text-[10px] font-black text-[var(--primary)] uppercase tracking-tighter">
                                                            ★ {movie.rating}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer Pinned */}
                    <div className="w-full flex items-center justify-between pt-6 mt-4 border-t border-white/5 shrink-0">
                        <div className="flex items-center gap-6">
                            <button 
                                disabled={watchedPage === 1}
                                onClick={() => setWatchedPage(p => p - 1)}
                                className="p-4 bg-[var(--primary)] text-black rounded-none disabled:opacity-20 disabled:bg-[var(--primary)]/10 disabled:text-black hover:bg-[var(--primary)]/80 transition-all shadow-xl"
                            >
                                <ChevronLeft size={16} strokeWidth={3} />
                            </button>
                            <span className="text-xs font-black uppercase tracking-[0.4em] text-white/60">
                                <span className="text-white text-sm">{watchedPage}</span> <span className="mx-2">/</span> {watched.pages}
                            </span>
                            <button 
                                disabled={watchedPage === watched.pages}
                                onClick={() => setWatchedPage(p => p + 1)}
                                className="p-4 bg-[var(--primary)] text-black rounded-none disabled:opacity-20 disabled:bg-[var(--primary)]/10 disabled:text-black hover:bg-[var(--primary)]/80 transition-all shadow-xl"
                            >
                                <ChevronRight size={16} strokeWidth={3} />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-30">
                    <span className="text-[7px] font-black uppercase tracking-[0.4em] text-white/40">Scroll to see watchlist</span>
                    <ChevronDown size={24} className="text-white animate-bounce" />
                </div>
            </section>

            {/* DECK 4: WATCHLIST */}
            <section className="h-screen w-full snap-start flex flex-col pt-24 px-8 pb-12 relative overflow-hidden bg-[#050505]">
                <div className="max-w-7xl mx-auto w-full flex flex-col h-full overflow-hidden relative">
                    
                    {/* Header Pinned */}
                    <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-6 shrink-0">
                        <div className="flex items-center gap-4">
                            <h2 className="font-['Arkhip'] text-3xl font-black uppercase tracking-tighter text-white">Watchlist</h2>
                        </div>

                        <div className="flex items-center gap-2">
                            <div className="relative group">
                                <Search 
                                    className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-white transition-colors cursor-pointer" 
                                    size={12} 
                                    onClick={() => handleSearch('watchlist')}
                                />
                                <input 
                                    type="text"
                                    placeholder="SEARCH WATCHLIST..."
                                    value={localWatchlistSearch}
                                    onChange={(e) => setLocalWatchlistSearch(e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(e, 'watchlist')}
                                    className="bg-black/20 border border-white/5 rounded-none pl-10 pr-6 py-2 text-[9px] uppercase font-black tracking-[0.2em] outline-none focus:border-white/30 transition-all w-56"
                                />
                            </div>
                            <button 
                                onClick={() => handleSearch('watchlist')}
                                className="px-4 py-2 bg-white/5 border border-white/10 text-white/40 text-[8px] font-black uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all"
                            >
                                Search
                            </button>
                        </div>
                    </div>

                    {/* Scrollable Grid Area */}
                    <div className="flex-1 overflow-y-auto pr-2 hide-scrollbar pb-8">
                        {watchLoading ? (
                            <div className="h-full w-full flex items-center justify-center min-h-[300px]">
                                <Loader2 className="animate-spin text-[var(--primary)]" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-8 xl:grid-cols-10 gap-x-3 gap-y-5 content-start">
                                {watchlist.movies.length === 0 ? (
                                    <div className="col-span-10 py-20 text-center">
                                        <p className="text-white/20 font-black uppercase tracking-[0.3em] text-xs">No matching films found</p>
                                    </div>
                                ) : (
                                    watchlist.movies.slice(0, 30).map((movie, i) => (
                                        <motion.div 
                                            key={i}
                                            whileHover={{ y: -4, scale: 1.05 }}
                                            className="group cursor-pointer"
                                            onClick={() => handleMovieClick(movie.tmdb_id)}
                                        >
                                            <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-black/40 transition-all duration-500 group-hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] group-hover:border-white/30">
                                                <img 
                                                    src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w200${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/200x300?text=?`} 
                                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                    alt="Poster"
                                                />
                                                <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col justify-center items-center p-3 text-center">
                                                    {movie.is_liked && <Heart size={12} className="fill-[#ff8000] text-[#ff8000] mb-1.5" />}
                                                    <h3 className="text-[9px] font-black text-white uppercase tracking-tighter leading-tight mb-1 line-clamp-3">{movie.title}</h3>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer Pinned */}
                    <div className="w-full flex items-center justify-between pt-6 mt-4 border-t border-white/5 shrink-0">
                        <div className="flex items-center gap-6">
                            <button 
                                disabled={watchlistPage === 1}
                                onClick={() => setWatchlistPage(p => p - 1)}
                                className="p-4 bg-[var(--primary)] text-black rounded-none disabled:opacity-20 disabled:bg-[var(--primary)]/10 disabled:text-black hover:bg-[var(--primary)]/80 transition-all shadow-xl"
                            >
                                <ChevronLeft size={16} strokeWidth={3} />
                            </button>
                            <span className="text-xs font-black uppercase tracking-[0.4em] text-white/60">
                                <span className="text-white text-sm">{watchlistPage}</span> <span className="mx-2">/</span> {watchlist.pages}
                            </span>
                            <button 
                                disabled={watchlistPage === watchlist.pages}
                                onClick={() => setWatchlistPage(p => p + 1)}
                                className="p-4 bg-[var(--primary)] text-black rounded-none disabled:opacity-20 disabled:bg-[var(--primary)]/10 disabled:text-black hover:bg-[var(--primary)]/80 transition-all shadow-xl"
                            >
                                <ChevronRight size={16} strokeWidth={3} />
                            </button>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
