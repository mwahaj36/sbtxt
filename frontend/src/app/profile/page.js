"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSync } from '@/components/SyncProvider';
import { Loader2, Film, Star, ChevronLeft, ChevronRight, Heart, Search, ChevronDown, RefreshCw, ExternalLink } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
    const router = useRouter();
    const { syncStatus, triggerSync } = useSync();
    const [profile, setProfile] = useState(null);
    const [recent, setRecent] = useState([]);
    const [library, setLibrary] = useState({ movies: [], total: 0, page: 1, pages: 1 });
    const [activeTab, setActiveTab] = useState('watched');
    const [isLoading, setIsLoading] = useState(true);
    const [libLoading, setLibLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [page, setPage] = useState(1);
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
        const fetchLibrary = async () => {
            setLibLoading(true);
            const token = localStorage.getItem("token");
            try {
                const res = await fetch(`http://localhost:8000/sync/library?type=${activeTab}&page=${page}&query=${searchQuery}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const data = await res.json();
                setLibrary(data);
            } catch (e) {
                console.error("Library fetch failed", e);
            } finally {
                setLibLoading(false);
            }
        };

        const timer = setTimeout(fetchLibrary, 300);
        return () => clearTimeout(timer);
    }, [activeTab, page, searchQuery]);

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
            <Loader2 className="animate-spin text-[#d946ef]" size={48} />
        </div>
    );

    return (
        <div className="h-screen bg-[#050505] text-white overflow-y-auto snap-y snap-mandatory scroll-smooth hide-scrollbar overflow-x-hidden pt-20">
            
            {/* DECK 1: IDENTITY */}
            <section className="h-[calc(100vh-80px)] w-full snap-start flex flex-col items-center justify-center px-8 relative overflow-hidden flex-shrink-0">
                <div className="absolute inset-0 mesh-gradient opacity-10" />
                
                <div className="max-w-4xl w-full flex flex-col items-center text-center z-10">
                    <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="mb-4 relative group">
                         <div className="absolute -inset-1 bg-gradient-to-r from-[#d946ef] via-[#7c3aed] to-[#00e054] rounded-full blur opacity-20 group-hover:opacity-60 transition-opacity" />
                        <img 
                            src={profile?.avatar} 
                            className="relative w-20 h-20 rounded-full border border-white/10 object-cover shadow-2xl"
                            alt="Avatar"
                        />
                    </motion.div>

                    <h1 
                        className="text-3xl font-black uppercase tracking-tighter mb-1"
                        style={{ fontFamily: 'Arkhip' }}
                    >
                        {profile?.name || profile?.username}
                    </h1>
                    <div className="flex items-center gap-3 mb-3">
                        <span className="text-[#00e054] text-[8px] font-black uppercase tracking-widest px-3 py-1 bg-[#00e054]/5 rounded-full border border-[#00e054]/10">
                            {profile?.films_count || 0} Films
                        </span>
                    </div>
                    
                    <p className="max-w-lg text-[10px] text-white/40 leading-relaxed mb-4 line-clamp-2">
                        {profile?.bio || "No bio available."}
                    </p>

                    <div className="flex items-center gap-3 mb-6">
                        <button 
                            onClick={triggerLiveSync}
                            disabled={isSyncing}
                            className="px-5 py-2 bg-white text-black text-[8px] font-black uppercase tracking-widest rounded-full hover:bg-white/90 active:scale-95 transition-all flex items-center gap-2 shadow-xl"
                        >
                            {isSyncing ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />}
                            {isSyncing ? "Syncing..." : "Sync Latest"}
                        </button>
                        <a 
                            href={`https://letterboxd.com/${profile?.username}`} 
                            target="_blank"
                            className="px-5 py-2 bg-white/5 border border-white/10 text-white/60 text-[8px] font-black uppercase tracking-widest rounded-full hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
                        >
                            <ExternalLink size={10} /> Letterboxd
                        </a>
                    </div>

                    {/* TOP 4 FAVORITES */}
                    <div className="w-full grid grid-cols-4 gap-5 max-w-lg mx-auto mb-6">
                        {(profile?.favorites || []).map((fav, i) => (
                            <motion.div 
                                key={i}
                                whileHover={{ y: -6, scale: 1.05 }}
                                className="group cursor-pointer"
                                onClick={() => handleMovieClick(fav.tmdb_id)}
                            >
                                <div className="relative aspect-[2/3] rounded-2xl overflow-hidden border border-white/10 bg-white/5 transition-all duration-500 group-hover:shadow-[0_0_50px_rgba(217,70,239,0.2)] group-hover:border-[#d946ef]/40">
                                    <img 
                                        src={fav.poster_path ? `https://image.tmdb.org/t/p/w400${fav.poster_path}` : `https://via.placeholder.com/400x600?text=?`}
                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                        alt="Fav"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                        <Heart size={16} className="fill-[#ff8000] text-[#ff8000]" />
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* RECENT 4 */}
                    <div className="w-full grid grid-cols-4 gap-5 max-w-lg mx-auto">
                        {recent.slice(0, 4).map((movie, i) => (
                            <motion.div 
                                key={i} 
                                whileHover={{ y: -6, scale: 1.05 }} 
                                className="group cursor-pointer"
                                onClick={() => handleMovieClick(movie.tmdb_id)}
                            >
                                <div className="relative aspect-[2/3] rounded-2xl overflow-hidden border border-white/10 bg-white/5 transition-all duration-500 group-hover:shadow-[0_0_50px_rgba(217,70,239,0.2)] group-hover:border-[#d946ef]/40">
                                    <img 
                                        src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} 
                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                        alt="Recent"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-4 text-center">
                                        {movie.is_liked && <Heart size={16} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                                        {movie.rating && (
                                            <div className="text-[10px] font-black text-[#d946ef] uppercase tracking-tighter">
                                                ★ {movie.rating}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <h3 className="text-[8px] font-black mt-2 text-center truncate px-2 group-hover:text-[#d946ef] transition-colors uppercase tracking-tight">{movie.title}</h3>
                                <p className="text-center text-[7px] text-white/40 font-bold mt-0.5">{movie.year}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>

                <div className="absolute bottom-6 animate-bounce opacity-20">
                    <ChevronDown size={24} className="text-[#d946ef]" />
                </div>
            </section>

            {/* DECK 2: TERMINAL - NAVBAR COMPENSATED */}
            <section className="h-[calc(100vh-80px)] w-full snap-start flex flex-col pt-8 px-8 pb-6 relative overflow-hidden flex-shrink-0">
                <div className="max-w-7xl mx-auto w-full flex flex-col h-full overflow-hidden">
                    
                    {/* Header Pinned */}
                    <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4 shrink-0">
                        <div className="flex gap-8">
                            {[
                                { id: 'watched', label: 'Watched' },
                                { id: 'watchlist', label: 'Wishlist' },
                            ].map(tab => (
                                <button 
                                    key={tab.id}
                                    onClick={() => { setActiveTab(tab.id); setPage(1); }}
                                    className={`text-[9px] font-black uppercase tracking-[0.3em] transition-all relative py-2
                                        ${activeTab === tab.id ? 'text-[#d946ef]' : 'text-white/20 hover:text-white'}`}
                                >
                                    {tab.label}
                                    {activeTab === tab.id && (
                                        <motion.div layoutId="tab-underline" className="absolute bottom-[-5px] left-0 right-0 h-[1px] bg-[#d946ef]" />
                                    )}
                                </button>
                            ))}
                        </div>

                        <div className="relative">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/10" size={12} />
                            <input 
                                type="text"
                                placeholder="SEARCH..."
                                value={searchQuery}
                                onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                                className="bg-white/5 border border-white/5 rounded-full pl-10 pr-6 py-2 text-[9px] uppercase font-black tracking-[0.2em] outline-none focus:border-[#d946ef]/30 transition-all w-56"
                            />
                        </div>
                    </div>

                    {/* Scrollable Grid Area */}
                    <div className="flex-1 min-h-0 overflow-y-auto pr-2 hide-scrollbar">
                        {libLoading ? (
                            <div className="h-full w-full flex items-center justify-center">
                                <Loader2 className="animate-spin text-[#d946ef]" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-8 gap-x-4 gap-y-6 content-start">
                                {library.movies.slice(0, 32).map((movie, i) => (
                                    <motion.div 
                                        key={i}
                                        whileHover={{ y: -4, scale: 1.05 }}
                                        className="group cursor-pointer"
                                        onClick={() => handleMovieClick(movie.tmdb_id)}
                                    >
                                        <div className="relative aspect-[2/3] rounded-xl overflow-hidden border border-white/10 bg-white/5 transition-all duration-500 group-hover:shadow-[0_0_30px_rgba(217,70,239,0.15)] group-hover:border-[#d946ef]/30">
                                            <img 
                                                src={movie.poster_path ? (movie.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w400${movie.poster_path}` : movie.poster_path) : `https://via.placeholder.com/400x600?text=?`} 
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                                alt="Poster"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end items-center p-3 text-center">
                                                {movie.is_liked && <Heart size={14} className="fill-[#ff8000] text-[#ff8000] mb-2" />}
                                                {movie.rating && (
                                                    <div className="text-[9px] font-black text-[#d946ef] uppercase tracking-tighter">
                                                        ★ {movie.rating}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <h3 className="text-[8px] font-black mt-2 text-center truncate px-1 group-hover:text-[#d946ef] transition-colors uppercase tracking-tight leading-none">{movie.title}</h3>
                                        <p className="text-center text-[7px] text-white/40 font-bold mt-0.5">{movie.year}</p>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer Pinned */}
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/5 shrink-0 bg-[#050505]">
                        <div className="flex items-center gap-6">
                            <button 
                                disabled={page === 1}
                                onClick={() => setPage(p => p - 1)}
                                className="p-2.5 bg-white/5 border border-white/5 rounded-xl disabled:opacity-20 hover:bg-white/10 text-[#d946ef] transition-all"
                            >
                                <ChevronLeft size={16} />
                            </button>
                            <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white/60">
                                <span className="text-[#d946ef]">{page}</span> / {library.pages}
                            </span>
                            <button 
                                disabled={page === library.pages}
                                onClick={() => setPage(p => p + 1)}
                                className="p-2.5 bg-white/5 border border-white/5 rounded-xl disabled:opacity-20 hover:bg-white/10 text-[#d946ef] transition-all"
                            >
                                <ChevronRight size={16} />
                            </button>
                        </div>

                        <div className="flex items-center gap-8 text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
                            <a href={`https://letterboxd.com/${profile?.username}`} target="_blank" className="hover:text-white transition-colors flex items-center gap-2">
                                <ExternalLink size={12} /> SOURCE
                            </a>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}
