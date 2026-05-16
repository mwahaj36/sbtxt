"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Search, Dna, User, LogOut, Settings as SettingsIcon } from 'lucide-react';

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [isLightMode, setIsLightMode] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleLogout = () => {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        setIsDropdownOpen(false);
        router.push("/"); // Send them back to landing page
    };

    useEffect(() => {
        // Check if the user has a VIP wristband in their browser!
        if (typeof window !== "undefined") {
            const token = localStorage.getItem("token");
            setIsLoggedIn(!!token);
        }

        // Only run this logic on the landing page
        if (pathname !== '/') {
            setIsLightMode(false);
            return;
        }

        const scrollContainer = document.querySelector('.main-scroll-container');
        const observerOptions = {
            root: scrollContainer,
            rootMargin: '0px 0px -90% 0px',
            threshold: 0
        };

        const observerCallback = (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setIsLightMode(entry.target.id === 'rant');
                }
            });
        };

        const observer = new IntersectionObserver(observerCallback, observerOptions);
        
        ['hero', 'rant', 'vibe', 'letterboxd', 'tmdb', 'galaxy', 'cta'].forEach(id => {
            const el = document.getElementById(id);
            if (el) observer.observe(el);
        });

        return () => observer.disconnect();
    }, [pathname]);

    useEffect(() => {
        setIsMenuOpen(false); // Close menu on route change
    }, [pathname]);

    const navItems = [
        { name: 'Search', href: '/search' },
        { name: 'Galaxy', href: '/galaxy' },
    ];

    // Hide the navbar entirely on the auth page
    if (pathname === '/auth') {
        return null;
    }

    return (
        <motion.nav 
            animate={{ 
                backgroundColor: isLightMode ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)',
                borderColor: isLightMode ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.05)'
            }}
            className="sticky top-0 z-[1500] w-full border-b backdrop-blur-2xl group transition-colors duration-500"
        >
            {/* Ambient Background Glow (Only in dark mode) */}
            {!isLightMode && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
            )}
            
            <div className="w-full px-6 md:px-8 h-16 md:h-20 flex items-center justify-between relative z-10">
                
                {/* Logo Section */}
                <Link href="/" className="flex items-center gap-3 group/logo">
                    <motion.div 
                        animate={{ backgroundColor: isLightMode ? '#000000' : '#ffffff' }}
                        className="w-20 md:w-28 h-6 md:h-8 group-hover/logo:bg-[var(--primary)] transition-all duration-500 transform group-hover/logo:scale-105 [mask-image:url(/file.svg)] [mask-size:contain] [mask-repeat:no-repeat] [mask-position:center]" 
                    />
                </Link>

                {/* Navigation Links */}
                <div className="hidden md:flex items-center gap-12">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link 
                                key={item.name} 
                                href={item.href}
                                className={`text-[10px] font-black uppercase tracking-[0.3em] transition-all duration-300 relative group/link ${
                                    isActive 
                                        ? 'text-[var(--primary)]' 
                                        : isLightMode ? 'text-black/60 hover:text-black' : 'text-gray-400 hover:text-white'
                                }`}
                            >
                                {item.name}
                                {/* Active/Hover Underline */}
                                <span className={`absolute -bottom-1 left-0 h-[1px] bg-[var(--primary)] transition-all duration-500 shadow-[0_0_8px_var(--primary)] ${
                                    isActive ? 'w-full opacity-100' : 'w-0 opacity-0 group-hover/link:w-full group-hover/link:opacity-100'
                                }`} />
                            </Link>
                        );
                    })}
                    
                    {/* The Sign In / Profile Button */}
                    {!isLoggedIn ? (
                        <Link href="/auth">
                            <button className={`relative group/btn overflow-hidden px-6 py-2 rounded-none border transition-all duration-500 active:scale-95 ${
                                isLightMode ? 'border-black/20 hover:border-black/50' : 'border-white/10 hover:border-[var(--primary)]/50'
                            }`}>
                                <div className={`absolute inset-0 transition-colors duration-500 ${
                                    isLightMode ? 'bg-black/5 group-hover/btn:bg-black/10' : 'bg-white/5 group-hover/btn:bg-[var(--primary)]/10'
                                }`} />
                                <span className={`relative z-10 text-[10px] font-black uppercase tracking-[0.2em] transition-colors duration-500 ${
                                    isLightMode ? 'text-black' : 'text-white'
                                }`}>
                                    Sign In
                                </span>
                            </button>
                        </Link>
                    ) : (
                        <div className="relative">
                            <button 
                                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                className={`relative group/btn overflow-hidden px-6 py-2 rounded-none border transition-all duration-500 active:scale-95 ${
                                    isLightMode ? 'border-black/20 hover:border-black/50' : 'border-white/10 hover:border-[var(--primary)]/50'
                                }`}
                            >
                                <div className={`absolute inset-0 transition-colors duration-500 ${
                                    isLightMode ? 'bg-black/5 group-hover/btn:bg-black/10' : 'bg-white/5 group-hover/btn:bg-[var(--primary)]/10'
                                }`} />
                                <span className={`relative z-10 text-[10px] font-black uppercase tracking-[0.2em] transition-colors duration-500 ${
                                    isLightMode ? 'text-black' : 'text-white'
                                }`}>
                                    My Profile
                                </span>
                            </button>

                            {/* Dropdown Menu */}
                            {isDropdownOpen && (
                                <div className={`absolute right-0 mt-4 w-48 rounded-none border backdrop-blur-3xl overflow-hidden flex flex-col shadow-2xl ${
                                    isLightMode ? 'bg-white/80 border-black/10' : 'bg-[#0a0a0a]/90 border-white/10'
                                }`}>
                                    <Link 
                                        href="/profile" 
                                        onClick={() => setIsDropdownOpen(false)} 
                                        className={`px-6 py-4 text-[10px] font-black uppercase tracking-widest transition-colors border-b ${
                                            isLightMode ? 'text-black hover:bg-black/5 border-black/5' : 'text-white hover:bg-white/5 border-white/5'
                                        }`}
                                    >
                                        My Profile
                                    </Link>
                                    <Link 
                                        href="/settings" 
                                        onClick={() => setIsDropdownOpen(false)} 
                                        className={`px-6 py-4 text-[10px] font-black uppercase tracking-widest transition-colors ${
                                            isLightMode ? 'text-black hover:bg-black/5' : 'text-white hover:bg-white/5'
                                        }`}
                                    >
                                        Settings
                                    </Link>
                                    <button 
                                        onClick={handleLogout} 
                                        className="px-6 py-4 text-[10px] text-left font-black uppercase tracking-widest text-red-500 hover:bg-red-500/10 transition-colors"
                                    >
                                        Log Out
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                </div>

                {/* Mobile Menu Toggle */}
                <button 
                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    className="flex md:hidden p-2 text-white/60 hover:text-[var(--primary)] transition-colors"
                >
                    {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
                </button>
            </div>

            {/* Mobile Drawer */}
            <AnimatePresence>
                {isMenuOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className={`md:hidden overflow-hidden border-t border-white/5 backdrop-blur-3xl ${
                            isLightMode ? 'bg-white/95' : 'bg-black/95'
                        }`}
                    >
                        <div className="flex flex-col p-6 gap-6">
                            {navItems.map((item) => (
                                <Link 
                                    key={item.name} 
                                    href={item.href}
                                    className="text-xs font-black uppercase tracking-[0.4em] text-white/60 hover:text-[var(--primary)]"
                                >
                                    {item.name}
                                </Link>
                            ))}
                            <div className="h-px w-full bg-white/5" />
                            {isLoggedIn ? (
                                <>
                                    <Link href="/profile" className="flex items-center gap-3 text-xs font-black uppercase tracking-[0.4em] text-white/60">
                                        <User size={14} className="text-[var(--primary)]" /> Profile
                                    </Link>
                                    <Link href="/settings" className="flex items-center gap-3 text-xs font-black uppercase tracking-[0.4em] text-white/60">
                                        <SettingsIcon size={14} className="text-[var(--primary)]" /> Settings
                                    </Link>
                                    <button onClick={handleLogout} className="flex items-center gap-3 text-xs font-black uppercase tracking-[0.4em] text-red-500">
                                        <LogOut size={14} /> Log Out
                                    </button>
                                </>
                            ) : (
                                <Link href="/auth" className="flex items-center gap-3 text-xs font-black uppercase tracking-[0.4em] text-[var(--primary)]">
                                    Sign In
                                </Link>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.nav>
    );
}
