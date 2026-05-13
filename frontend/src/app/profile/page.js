"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSync } from '@/components/SyncProvider';
import { Loader2, Film, Star, ChevronLeft, ChevronRight, Heart, Search, ChevronDown, RefreshCw, ExternalLink, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';

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
    const [searchQuery, setSearchQuery] = useState("");
    const [watchedPage, setWatchedPage] = useState(1);
    const [watchlistPage, setWatchlistPage] = useState(1);
    const [isSyncing, setIsSyncing] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/auth");
                return;
            }
            try {
                const userRes = await fetch("http://localhost:8000/auth/me", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const userData = await userRes.json();
                
                if (userData.letterboxd_username) {
                    const lbRes = await fetch(`http://localhost:8000/sync/profile?username=${userData.letterboxd_username}`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    const lbData = await lbRes.json();
                    setProfile(lbData);
                }

                const recentRes = await fetch("http://localhost:8000/sync/recent", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const recentData = await recentRes.json();
                setRecent(recentData);

            } catch (e) {
                console.error("Profile data fetch failed", e);
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
                // Fetch Watched
                const resWatched = await fetch(`http://localhost:8000/sync/library?type=watched&page=${watchedPage}&query=${searchQuery}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                setWatched(await resWatched.json());
                setLibLoading(false);

                // Fetch Watchlist
                const resWatchlist = await fetch(`http://localhost:8000/sync/library?type=watchlist&page=${watchlistPage}&query=${searchQuery}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                setWatchlist(await resWatchlist.json());
                setWatchLoading(false);
            } catch (e) {
                console.error("Library fetch failed", e);
                setLibLoading(false);
                setWatchLoading(false);
            }
        };

        const timer = setTimeout(fetchLibraries, 300);
        return () => clearTimeout(timer);
    }, [watchedPage, watchlistPage, searchQuery]);

    const triggerLiveSync = async () => {
        setIsSyncing(true);
        const token = localStorage.getItem("token");
        try {
            await fetch("http://localhost:8000/sync/live", {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` }
            });
            triggerSync(100);
        } catch (e) {
            console.error("Live sync trigger failed", e);
        } finally {
            setTimeout(() => setIsSyncing(false), 2000);
        }
    };

    const handleMovieClick = (tmdbId) => {
        if (tmdbId) {
            window.open(`https://www.themoviedb.org/movie/${tmdbId}`, '_blank');
        }
    };

    if (isLoading) return (
        <div className="h-screen w-full flex items-center justify-center bg-black">
            <Loader2 className="animate-spin text-[var(--primary)]" size={48} />
        </div>
    );

    return (
        <main className="w-full bg-black text-white">
            
            {/* DECK 1: IDENTITY */}
            <section className="h-screen w-full snap-start flex flex-col items-center justify-center pt-20 px-8 relative overflow-hidden bg-[#050505]">
                <div className="absolute inset-0 mesh-gradient opacity-10" />
                
                <div className="max-w-6xl mx-auto w-full h-full flex flex-row items-center justify-between gap-16 z-10 py-12">
                    
                    {/* LEFT SIDE: DP, Bio, Buttons */}
                    <div className="w-1/3 flex flex-col items-start text-left shrink-0">
                        <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="mb-8 relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-white/20 via-white/10 to-transparent rounded-none blur opacity-20 group-hover:opacity-60 transition-opacity" />
                            <img 
                                src={profile?.avatar || "https://a.ltrbxd.com/resized/avatar/twitter/4/8/9/4/6/7/shard/2126200257/avatar-80.jpg"} 
                                className="relative w-32 h-32 rounded-none border border-white/10 object-cover shadow-2xl"
                                alt="Avatar"
                            />
                        </motion.div>

                        <h1 
                            className="text-4xl font-black uppercase tracking-tighter mb-2 w-full truncate"
                            style={{ fontFamily: 'Arkhip' }}
                            title={profile?.name || profile?.username}
                        >
                            {profile?.name || profile?.username}
                        </h1>
                        <div className="flex items-center gap-3 mb-6">
                            <span className="text-white text-[10px] font-black uppercase tracking-widest px-4 py-2 bg-white/5 rounded-none border border-white/10">
                                {profile?.films_count || 0} Films
                            </span>
                        </div>
                        
                        <p className="w-full text-xs text-white/40 leading-relaxed mb-10 line-clamp-4">
                            {profile?.bio || "No bio available."}
                        </p>

                        <div className="flex flex-col w-full gap-3">
                            <button 
                                onClick={triggerLiveSync}
                                disabled={isSyncing}
                                className="w-full py-4 bg-[var(--primary)] text-black text-[10px] font-black uppercase tracking-widest rounded-none hover:bg-[var(--primary)]/90 active:scale-95 transition-all flex items-center justify-center gap-2 shadow-xl"
                            >
                                {isSyncing ? <Loader2 size={12} className="animate-spin text-black" /> : <RefreshCw size={12} />}
                                {isSyncing ? "Syncing..." : "Sync Latest"}
                            </button>
                            <div className="flex gap-3 w-full">
                                <a 
                                    href={`https://letterboxd.com/${profile?.username}`} 
                                    target="_blank"
                                    className="flex-1 py-4 bg-white/5 border border-white/10 text-white/60 text-[10px] font-black uppercase tracking-widest rounded-none hover:bg-white/10 hover:text-white transition-all flex items-center justify-center gap-2"
                                >
                                    <ExternalLink size={12} /> Letterboxd
                                </a>
                                <button 
                                    onClick={() => router.push('/settings')}
                                    className="flex-1 py-4 bg-white/5 border border-white/10 text-white/60 text-[10px] font-black uppercase tracking-widest rounded-none hover:bg-white/10 hover:text-white transition-all flex items-center justify-center gap-2"
                                >
                                    <Settings size={12} /> Settings
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* RIGHT SIDE: Favorites and Recent */}
                    <div className="w-2/3 flex flex-col gap-10 h-full justify-center">
                        {/* TOP 4 FAVORITES */}
                        <div className="w-full">
                            <div className="w-full mb-4 text-left">
                                <h3 className="text-[12px] font-black uppercase tracking-[0.3em] text-white/40 border-b border-white/10 pb-3">Top Favorites</h3>
                            </div>
                            <div className="w-full grid grid-cols-4 gap-4">
                                {(profile?.favorites || []).map((fav, i) => (
                                    <motion.div 
                                        key={i}
                                        whileHover={{ y: -6, scale: 1.05 }}
                                        className="group cursor-pointer"
                                        onClick={() => handleMovieClick(fav.tmdb_id)}
                                    >
                                        <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-white/5 transition-all duration-500 group-hover:shadow-[0_0_50px_rgba(255,255,255,0.2)] group-hover:border-white/40">
                                            <img 
                                                src={fav.poster_path ? `https://image.tmdb.org/t/p/w400${fav.poster_path}` : `https://via.placeholder.com/400x600?text=?`}
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                                alt="Fav"
                                            />
                                            <div className="absolute -inset-1 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                                <Heart size={16} className="fill-[#ff8000] text-[#ff8000]" />
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        {/* RECENT 4 */}
                        <div className="w-full">
                            <div className="w-full mb-4 text-left">
                                <h3 className="text-[12px] font-black uppercase tracking-[0.3em] text-white/40 border-b border-white/10 pb-3">Recently Watched</h3>
                            </div>
                            <div className="w-full grid grid-cols-4 gap-4">
                                {recent.slice(0, 4).map((movie, i) => (
                                    <motion.div 
                                        key={i} 
                                        whileHover={{ y: -6, scale: 1.05 }} 
                                        className="group cursor-pointer"
                                        onClick={() => handleMovieClick(movie.tmdb_id)}
                                    >
                                        <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-white/5 transition-all duration-500 group-hover:shadow-[0_0_50px_rgba(255,255,255,0.2)] group-hover:border-white/40">
                                            <img 
                                                src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} 
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                alt="Recent"
                                            />
                                            <div className="absolute -inset-1 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                                {movie.is_liked && <Heart size={16} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                                                {movie.rating && (
                                                    <div className="text-[10px] font-black text-white uppercase tracking-tighter">
                                                        ★ {movie.rating}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <h3 className="text-[8px] font-black mt-2 text-center truncate px-2 group-hover:text-white transition-colors uppercase tracking-tight">{movie.title}</h3>
                                        <p className="text-center text-[7px] text-white/40 font-bold mt-0.5">{movie.year}</p>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce opacity-20">
                    <ChevronDown size={24} className="text-white" />
                </div>
            </section>

            {/* DECK 2: FILMS */}
            <section className="h-screen w-full snap-start flex flex-col pt-24 px-8 pb-12 relative overflow-hidden bg-[#0a0a0a]">
                <div className="max-w-7xl mx-auto w-full flex flex-col h-full overflow-hidden relative">
                    
                    {/* Header Pinned */}
                    <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-6 shrink-0">
                        <div className="flex items-center gap-4">
                            <h2 className="font-['Arkhip'] text-3xl font-black uppercase tracking-tighter text-white">Films</h2>
                        </div>

                        <div className="relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/10" size={12} />
                            <input 
                                type="text"
                                placeholder="SEARCH..."
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); setWatchedPage(1); setWatchlistPage(1); }}
                                className="bg-black/20 border border-white/5 rounded-none pl-10 pr-6 py-2 text-[9px] uppercase font-black tracking-[0.2em] outline-none focus:border-white/30 transition-all w-56"
                            />
                        </div>
                    </div>

                    {/* Scrollable Grid Area */}
                    <div className="flex-1 overflow-y-auto pr-2 hide-scrollbar pb-8">
                        {libLoading ? (
                            <div className="h-full w-full flex items-center justify-center min-h-[300px]">
                                <Loader2 className="animate-spin text-[var(--primary)]" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-8 gap-x-4 gap-y-6 content-start">
                                {watched.movies.slice(0, 32).map((movie, i) => (
                                    <motion.div 
                                        key={i}
                                        whileHover={{ y: -4, scale: 1.05 }}
                                        className="group cursor-pointer"
                                        onClick={() => handleMovieClick(movie.tmdb_id)}
                                    >
                                        <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-black/40 transition-all duration-500 group-hover:shadow-[0_0_30px_rgba(255,255,255,0.15)] group-hover:border-white/30">
                                            <img 
                                                src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} 
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                alt="Poster"
                                            />
                                            <div className="absolute -inset-1 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                                {movie.is_liked && <Heart size={14} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                                                {movie.rating && (
                                                    <div className="text-[9px] font-black text-white uppercase tracking-tighter">
                                                        ★ {movie.rating}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <h3 className="text-[8px] font-black mt-2 text-center truncate px-1 group-hover:text-white transition-colors uppercase tracking-tight leading-none">{movie.title}</h3>
                                        <p className="text-center text-[7px] text-white/40 font-bold mt-0.5">{movie.year}</p>
                                    </motion.div>
                                ))}
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
            </section>

            {/* DECK 3: WATCHLIST */}
            <section className="h-screen w-full snap-start flex flex-col pt-24 px-8 pb-12 relative overflow-hidden bg-[#050505]">
                <div className="max-w-7xl mx-auto w-full flex flex-col h-full overflow-hidden relative">
                    
                    {/* Header Pinned */}
                    <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-6 shrink-0">
                        <div className="flex items-center gap-4">
                            <h2 className="font-['Arkhip'] text-3xl font-black uppercase tracking-tighter text-white">Watchlist</h2>
                        </div>
                    </div>

                    {/* Scrollable Grid Area */}
                    <div className="flex-1 overflow-y-auto pr-2 hide-scrollbar pb-8">
                        {watchLoading ? (
                            <div className="h-full w-full flex items-center justify-center min-h-[300px]">
                                <Loader2 className="animate-spin text-[var(--primary)]" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-8 gap-x-4 gap-y-6 content-start">
                                {watchlist.movies.slice(0, 32).map((movie, i) => (
                                    <motion.div 
                                        key={i}
                                        whileHover={{ y: -4, scale: 1.05 }}
                                        className="group cursor-pointer"
                                        onClick={() => handleMovieClick(movie.tmdb_id)}
                                    >
                                        <div className="relative aspect-[2/3] rounded-none overflow-hidden border border-white/10 bg-black/40 transition-all duration-500 group-hover:shadow-[0_0_30px_rgba(255,255,255,0.15)] group-hover:border-white/30">
                                            <img 
                                                src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} 
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                alt="Poster"
                                            />
                                            <div className="absolute -inset-1 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                                {movie.is_liked && <Heart size={14} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                                            </div>
                                        </div>
                                        <h3 className="text-[8px] font-black mt-2 text-center truncate px-1 group-hover:text-white transition-colors uppercase tracking-tight leading-none">{movie.title}</h3>
                                        <p className="text-center text-[7px] text-white/40 font-bold mt-0.5">{movie.year}</p>
                                    </motion.div>
                                ))}
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
