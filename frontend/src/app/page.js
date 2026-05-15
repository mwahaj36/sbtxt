"use client";
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Search, Library, Compass, ChevronRight, Share2, Sparkles, Database, Loader2 } from 'lucide-react';
import Footer from '@/components/footer';

export default function Home() {
    const pathname = usePathname();
    const [trendingMovies, setTrendingMovies] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [stars, setStars] = useState([]);

    const fadeIn = {
        initial: { opacity: 0, y: 20 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: true },
        transition: { duration: 0.8 }
    };
    const fallbackPosters = [
        { id: 313369, title: "La La Land", path: "/xjH9jy4EhNG81B2tzpDWz9yeLfF.jpg" },
        { id: 385383, title: "Manchester by the Sea", path: "/o9VXYOuaJxCEKOxbA86xqtwmqYn.jpg" },
        { id: 11104, title: "Chungking Express", path: "/43I9DcNoCzpyzK8JCkJYpHqHqGG.jpg" },
        { id: 872, title: "Singin' in the Rain", path: "/w03EiJVHP8Un77boQeE7hg9DVdU.jpg" },
        { id: 603, title: "The Matrix", path: "/aOIuZAjPaRIE6CMzbazvcHuHXDc.jpg" },
        { id: 238, title: "The Godfather", path: "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg" },
        { id: 680, title: "Pulp Fiction", path: "/yDCNcS5pz8CZiL4fbMmtBrf1Ggz.jpg" },
        { id: 155, title: "The Dark Knight", path: "/qJ2tW6WMUDux911r6m7haRef0WH.jpg" },
        { id: 27205, title: "Inception", path: "/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg" }
    ];

    useEffect(() => {
        // Generate stars only on the client to avoid hydration errors
        const newStars = [...Array(40)].map((_, i) => ({
            id: i,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            duration: Math.random() * 4 + 3
        }));
        setStars(newStars);
        setTrendingMovies(fallbackPosters);
    }, []);

    return (
        <main className="w-full bg-black text-white selection:bg-[var(--primary)]/30 pt-20 md:pt-24">
            <div className="mesh-gradient opacity-40" />

            {/* SECTION 1: HERO (BLACK) */}
            <section id="hero" className="h-screen w-full flex flex-col items-center justify-center text-center px-4 bg-black snap-start relative overflow-hidden">
                <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="absolute inset-0 pointer-events-none"
                >
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[var(--primary)]/10 rounded-none blur-[120px]" />
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className="relative z-10"
                >
                    <h1 className="font-['Arkhip'] text-4xl md:text-9xl tracking-tighter leading-tight md:leading-none mb-6 uppercase px-4">
                        MOVIES,<br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-[var(--primary)] to-white/40">SEMANTICALLY.</span>
                    </h1>
                    <p className="max-w-2xl mx-auto text-gray-400 text-sm md:text-xl font-light tracking-wide mb-10 px-6">
                        Escape the algorithm. Discover cinema through vibes, story, and soul—not just metadata.
                    </p>
                    <div className="flex flex-col md:flex-row gap-4 justify-center items-center">
                        <Link href="/search" className="group relative px-8 py-4 bg-[var(--primary)] text-black font-black uppercase tracking-widest text-xs rounded-none overflow-hidden transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]">
                            <span className="relative z-10">Start Searching</span>
                            <div className="absolute inset-0 bg-white translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                        </Link>
                    </div>
                </motion.div>

                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.5, duration: 1 }}
                    className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
                >
                    <span className="text-[10px] uppercase tracking-[0.4em] text-gray-500">Scroll to explore</span>
                    <div className="w-px h-12 bg-gradient-to-b from-white/20 to-transparent" />
                </motion.div>
            </section>

            {/* SECTION 2: THE RANT (WHITE) */}
            <section id="rant" className="h-screen w-full flex items-center justify-center bg-white text-black snap-start relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-8 relative z-10">
                    <motion.div 
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8 }}
                        className="max-w-4xl"
                    >
                        <h2 className="text-4xl md:text-8xl font-black tracking-tighter mb-8 md:12 leading-[1] md:leading-[0.9]">
                            KEYWORDS ARE <br />
                            <span className="line-through decoration-[var(--primary)] decoration-4 md:decoration-8 text-black/20">A LIE.</span>
                        </h2>
                        <p className="text-lg md:text-4xl font-bold tracking-tight leading-snug md:leading-tight mb-8 md:12">
                            Traditional search is a graveyard of metadata. It doesn't care about the <span className="italic">soul</span> of the story—it only cares if the title matches your typo.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-3 gap-12 mt-20">
                        {[
                            { title: "The Popularity Trap", desc: "Old search engines only show you what's trending, burying the hidden gems you actually need." },
                            { title: "The Keyword Curse", desc: "Tags are limited. Feelings aren't. Why can't you search for 'movies that feel like a cold morning'?" },
                            { title: "The Scroll Fatigue", desc: "Spent 45 minutes looking and 0 minutes watching? That's an algorithm failure, not a you problem." }
                        ].map((item, i) => (
                            <motion.div 
                                key={item.title}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.2 }}
                                className="border-l-4 border-black pl-6 py-2"
                            >
                                <h4 className="text-xl font-black uppercase mb-3">{item.title}</h4>
                                <p className="text-gray-600 font-medium text-sm">{item.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
                <div className="absolute top-1/2 right-0 -translate-y-1/2 text-[20rem] font-black opacity-[0.03] select-none pointer-events-none whitespace-nowrap">
                    TRADITIONAL SEARCH SUCKS
                </div>
            </section>

            {/* SECTION 3: VIBE SEARCH (DEEP PURPLE) */}
            <section id="vibe" className="h-screen w-full flex items-center justify-center bg-[#0d041a] snap-start relative px-4">
                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-20 items-center">
                    <motion.div {...fadeIn}>
                        <div className="w-12 h-12 bg-[var(--secondary)]/10 rounded-none flex items-center justify-center text-[var(--secondary)] mb-6">
                            <Search size={24} />
                        </div>
                        <h2 className="text-3xl md:text-6xl font-black mb-6 tracking-tight text-white">Vibe-First Search</h2>
                        <p className="text-gray-400 text-base md:text-lg leading-relaxed mb-8">
                            Stop typing titles. Start typing feelings. Search for "Lush atmospheric nostalgia," "Neon-soaked revenge," or "Heartfelt rural coming-of-age." Our semantic engine understands the DNA of story.
                        </p>
                        <ul className="space-y-4">
                            {['Vector-based thematic retrieval', 'Natural language understanding', 'Mood-aware results'].map((item) => (
                                <li key={item} className="flex items-center gap-3 text-sm font-bold text-gray-300">
                                    <div className="w-1.5 h-1.5 rounded-none bg-[var(--secondary)]" />
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        className="relative aspect-square bg-white/5 rounded-none border border-white/10 overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-[var(--secondary)]/20 to-transparent" />
                        <div className="absolute inset-8 flex flex-col gap-4">
                            <div className="h-12 w-full bg-white/10 rounded-none animate-pulse" />
                            <div className="h-32 w-full bg-white/5 rounded-none" />
                            <div className="grid grid-cols-2 gap-4">
                                <div className="h-40 bg-white/10 rounded-none" />
                                <div className="h-40 bg-white/10 rounded-none" />
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* SECTION 4: LETTERBOXD (BLUE) */}
            <section id="letterboxd" className="h-screen w-full flex items-center justify-center bg-[#0a1128] snap-start relative px-4">
                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-20 items-center">
                    <motion.div 
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 1 }}
                        className="order-2 md:order-1 relative aspect-video bg-black/40 backdrop-blur-3xl rounded-none border border-white/10 overflow-hidden p-8"
                    >
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex gap-2">
                                <div className="w-3 h-3 rounded-none bg-orange-500" />
                                <div className="w-3 h-3 rounded-none bg-green-500" />
                                <div className="w-3 h-3 rounded-none bg-blue-500" />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-blue-400">Syncing with Letterboxd...</span>
                        </div>
                        <div className="space-y-4">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="flex items-center gap-4 p-4 bg-white/5 rounded-none border border-white/5">
                                    <div className="w-12 h-16 bg-white/10 rounded-lg" />
                                    <div className="flex-1 space-y-2">
                                        <div className="h-3 w-1/2 bg-white/10 rounded" />
                                        <div className="h-2 w-1/4 bg-white/5 rounded" />
                                    </div>
                                    <div className="text-blue-400"><Sparkles size={16} /></div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                    <motion.div {...fadeIn} className="order-1 md:order-2">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-12 h-12 bg-blue-500/10 rounded-none flex items-center justify-center text-blue-400">
                                <Library size={24} />
                            </div>
                        </div>
                        <h2 className="text-3xl md:text-6xl font-black mb-6 tracking-tight text-white leading-tight md:leading-none">Your Cinematic <br/>Signature</h2>
                        <p className="text-gray-300 text-base md:text-lg leading-relaxed mb-8">
                            Connect your Letterboxd diary to unlock <strong>Neural Search</strong>. SBTXT analyzes your 5-star ratings to map your unique Taste DNA.
                        </p>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-none bg-white/5 border border-white/5">
                                <h4 className="text-blue-200 font-bold mb-1 italic text-xs uppercase tracking-widest">Taste DNA</h4>
                                <p className="text-[10px] text-blue-400/60 leading-tight">Search using your personalized neural signature.</p>
                            </div>
                            <div className="p-4 rounded-none bg-white/5 border border-white/5">
                                <h4 className="text-blue-200 font-bold mb-1 italic text-xs uppercase tracking-widest">Watchlist Scan</h4>
                                <p className="text-[10px] text-blue-400/60 leading-tight">Find exactly what to watch next in your own list.</p>
                            </div>
                            <div className="p-4 rounded-none bg-white/5 border border-white/5">
                                <h4 className="text-blue-200 font-bold mb-1 italic text-xs uppercase tracking-widest">Auto-Filter</h4>
                                <p className="text-[10px] text-blue-400/60 leading-tight">Automatically hide every movie you've already seen.</p>
                            </div>
                            <div className="p-4 rounded-none bg-white/5 border border-white/5">
                                <h4 className="text-blue-200 font-bold mb-1 italic text-xs uppercase tracking-widest">Affinity Bonus</h4>
                                <p className="text-[10px] text-blue-400/60 leading-tight">Your highest ratings carry the most weight.</p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* SECTION 5: TMDB DATA (OFFICIAL COLORS) */}
            <section id="tmdb" className="h-screen w-full flex items-center justify-center bg-[#0d253f] snap-start relative px-4">
                <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-20 items-center">
                    <motion.div {...fadeIn}>
                        <div className="w-12 h-12 bg-[#90cea1]/10 rounded-none flex items-center justify-center text-[#90cea1] mb-6">
                            <Database size={24} />
                        </div>
                        <h2 className="text-4xl md:text-6xl font-black mb-6 tracking-tight text-white leading-none">Powered by the World's Movie Database</h2>
                        <p className="text-blue-100/60 text-lg leading-relaxed mb-8">
                            SBTXT is built upon the robust infrastructure of TMDB. We ingest millions of data points—from classic filmography to upcoming blockbusters—to ensure your discovery journey is always backed by the most comprehensive movie library on Earth.
                        </p>
                        <div className="flex items-center gap-6">
                            <a href="https://www.themoviedb.org/" target="_blank" rel="noopener noreferrer" className="hover:scale-110 transition-transform">
                                <img src="/tmdb.svg" alt="TMDB" className="h-8" />
                            </a>
                            <div className="h-8 w-px bg-white/10" />
                            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#01b4e4]">Data Provided by TMDB</span>
                        </div>
                    </motion.div>
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        className="relative hidden md:block w-full max-w-md mx-auto"
                    >
                        <div className="absolute inset-0 bg-[#01b4e4]/10 blur-[100px] rounded-none" />
                        

                            <div className="relative z-10 grid grid-cols-3 gap-3">
                                {trendingMovies.map((movie, i) => (
                                    <motion.a
                                        key={movie.id}
                                        href={`https://www.themoviedb.org/movie/${movie.id}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        initial={{ opacity: 0, y: 20 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.1 }}
                                        whileHover={{ scale: 1.05, zIndex: 50 }}
                                        className="aspect-[2/3] relative rounded-none border border-white/10 overflow-hidden shadow-2xl group/poster bg-black/20"
                                    >
                                        <img 
                                            src={`https://image.tmdb.org/t/p/w500${movie.path}`} 
                                            alt={movie.title} 
                                            className="w-full h-full object-cover transition-all duration-500 hover:brightness-110"
                                            onError={(e) => {
                                                e.currentTarget.src = `https://via.placeholder.com/500x750/0d253f/01b4e4?text=${encodeURIComponent(movie.title)}`;
                                            }}
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-[#0d253f] via-transparent to-transparent opacity-60 pointer-events-none" />
                                        <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-full group-hover/poster:translate-y-0 transition-transform duration-300 bg-black/80 backdrop-blur-md">
                                            <p className="text-[8px] font-black uppercase tracking-widest text-white truncate">{movie.title}</p>
                                        </div>
                                    </motion.a>
                                ))}
                            </div>
                    </motion.div>
                </div>
            </section>

            {/* SECTION 6: GALAXY (MAGENTA) */}
            <section id="galaxy" className="min-h-screen w-full flex items-center justify-center bg-black snap-start relative px-8 md:px-24 py-24 md:py-0 overflow-hidden">
                <div className="max-w-7xl mx-auto w-full grid md:grid-cols-2 gap-20 items-center">
                    
                    {/* LEFT: Galaxy Visualization Preview */}
                    <Link href="/galaxy" className="group relative order-2 md:order-1">
                        <motion.div 
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            transition={{ duration: 1 }}
                            className="relative h-[400px] md:h-[650px] w-full bg-white/[0.02] backdrop-blur-3xl rounded-none border border-white/10 overflow-hidden group hover:border-[var(--primary)]/50 transition-all cursor-pointer shadow-[0_0_50px_rgba(var(--primary-rgb),0.05)]"
                        >
                             {stars.map((star) => (
                                <motion.div 
                                    key={star.id}
                                    animate={{ opacity: [0.1, 0.4, 0.1], scale: [1, 1.2, 1] }}
                                    transition={{ duration: star.duration, repeat: Infinity }}
                                    className="absolute w-1 h-1 bg-white rounded-none"
                                    style={{ top: star.top, left: star.left }}
                                />
                             ))}
                             <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)]/10 to-transparent" />
                             <div className="absolute inset-0 flex items-center justify-center">
                                <div className="flex flex-col items-center gap-6">
                                    <div className="flex flex-col items-center">
                                        <span className="text-[16px] font-black uppercase tracking-[0.6em] text-white px-4 text-center mb-2" style={{ fontFamily: 'Arkhip' }}>Enter the Galaxy</span>
                                        <div className="h-1 w-12 bg-[var(--primary)]" />
                                    </div>
                                    <div className="px-8 py-4 border border-[var(--primary)] text-[var(--primary)] text-[11px] font-black uppercase tracking-[0.4em] group-hover:bg-[var(--primary)] group-hover:text-black transition-all">Launch Engine</div>
                                </div>
                             </div>
                        </motion.div>
                    </Link>

                    {/* RIGHT: Detailed Intelligence */}
                    <motion.div {...fadeIn} className="flex flex-col items-start text-left order-1 md:order-2">
                        <div className="flex items-center gap-3 mb-8">
                            <div className="w-12 h-12 bg-[var(--primary)]/10 rounded-none flex items-center justify-center text-[var(--primary)]">
                                <Compass size={24} />
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--primary)]">Neural Cartography</span>
                        </div>
                        
                        <h2 className="text-4xl md:text-8xl font-black mb-6 md:8 tracking-tighter text-white uppercase leading-none" style={{ fontFamily: 'Arkhip' }}>
                            The <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--primary)] to-white/40">Galaxy</span>
                        </h2>
                        
                        <p className="text-gray-400 text-base md:text-lg leading-relaxed mb-10 md:12 font-medium max-w-lg">
                            Escape the grid. We've mapped over 100,000 films into a high-dimensional neural matrix. By measuring <strong>Raw Vector Similarity</strong>, we've created a universe where proximity is meaning. 
                        </p>
                        
                        <div className="grid gap-6 w-full">
                            <div className="flex gap-8 items-start p-8 bg-white/[0.02] border border-white/5 hover:border-[var(--primary)]/30 transition-all group">
                                <div className="text-[var(--primary)] font-black text-2xl italic shrink-0 opacity-40 group-hover:opacity-100 transition-opacity">01</div>
                                <div>
                                    <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white mb-3">Neural Embeddings</h4>
                                    <p className="text-[10px] text-white/30 uppercase leading-relaxed font-bold tracking-tight">Every film distilled into a 768-dimensional mathematical signature representing its cinematic soul.</p>
                                </div>
                            </div>
                            <div className="flex gap-8 items-start p-8 bg-white/[0.02] border border-white/5 hover:border-[var(--primary)]/30 transition-all group">
                                <div className="text-[var(--primary)] font-black text-2xl italic shrink-0 opacity-40 group-hover:opacity-100 transition-opacity">02</div>
                                <div>
                                    <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white mb-3">Spatial Projection</h4>
                                    <p className="text-[10px] text-white/30 uppercase leading-relaxed font-bold tracking-tight">Advanced UMAP algorithms compress infinite variables into a navigable 3D star-field where math meets intuition.</p>
                                </div>
                            </div>
                            <div className="flex gap-8 items-start p-8 bg-white/[0.02] border border-white/5 hover:border-[var(--primary)]/30 transition-all group">
                                <div className="text-[var(--primary)] font-black text-2xl italic shrink-0 opacity-40 group-hover:opacity-100 transition-opacity">03</div>
                                <div>
                                    <h4 className="text-[11px] font-black uppercase tracking-[0.2em] text-white mb-3">Raw Similarity</h4>
                                    <p className="text-[10px] text-white/30 uppercase leading-relaxed font-bold tracking-tight">Distance is data. If two stars are close, they share the same emotional, stylistic, and thematic DNA.</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* SECTION 7: CTA & FOOTER (BLACK) */}
            <section id="cta" className="h-screen w-full flex flex-col justify-between bg-black snap-start relative">
                <div className="flex-1 flex items-center justify-center px-4">
                    <motion.div {...fadeIn} className="max-w-4xl w-full p-8 md:12 rounded-none bg-gradient-to-br from-white/5 to-transparent border border-white/10 text-center relative overflow-hidden">
                        <h2 className="text-3xl md:text-7xl font-black mb-8 md:10 text-white leading-tight">Ready to find<br />something real?</h2>
                        <Link href="/search" className="inline-flex items-center gap-4 px-10 md:12 py-5 md:6 bg-[var(--primary)] text-black font-black uppercase tracking-widest text-[10px] md:text-xs rounded-none hover:scale-110 transition-all shadow-[0_0_50px_rgba(217,70,239,0.3)]">
                            Launch Search <ChevronRight size={18} />
                        </Link>
                    </motion.div>
                </div>
                <Footer />
            </section>
        </main>
    );
}
