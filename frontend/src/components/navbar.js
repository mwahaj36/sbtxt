"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar() {
    const pathname = usePathname();
    const [isLightMode, setIsLightMode] = useState(false);

    useEffect(() => {
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
                // We only care about the section that is currently crossing into the top zone
                if (entry.isIntersecting) {
                    setIsLightMode(entry.target.id === 'rant');
                }
            });
        };

        const observer = new IntersectionObserver(observerCallback, observerOptions);
        
        // Observe all major sections
        ['hero', 'rant', 'vibe', 'letterboxd', 'tmdb', 'galaxy', 'cta'].forEach(id => {
            const el = document.getElementById(id);
            if (el) observer.observe(el);
        });

        return () => observer.disconnect();
    }, [pathname]);

    const navItems = [
        { name: 'Search', href: '/search' },
        // { name: 'Discover', href: '/discover' },
        // { name: 'Moods', href: '/moods' }
    ];

    return (
        <motion.nav 
            animate={{ 
                backgroundColor: isLightMode ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)',
                borderColor: isLightMode ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.05)'
            }}
            className="sticky top-0 z-[100] w-full border-b backdrop-blur-2xl group transition-colors duration-500"
        >
            {/* Ambient Background Glow (Only in dark mode) */}
            {!isLightMode && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 pointer-events-none" />
            )}
            
            <div className="w-full px-8 h-20 flex items-center justify-between relative z-10">
                
                {/* Logo Section */}
                <Link href="/" className="flex items-center gap-3 group/logo">
                    <motion.div 
                        animate={{ backgroundColor: isLightMode ? '#000000' : '#ffffff' }}
                        className="w-28 h-8 group-hover/logo:bg-[var(--primary)] transition-all duration-500 transform group-hover/logo:scale-105 [mask-image:url(/file.svg)] [mask-size:contain] [mask-repeat:no-repeat] [mask-position:center]" 
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
                    
                    {/* Premium Action Button (Coming Soon) */}
                    {/* 
                    <button className={`relative group/btn overflow-hidden px-6 py-2 rounded-lg border transition-all duration-500 active:scale-95 ${
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
                    */}
                </div>
            </div>
        </motion.nav>
    );
}
