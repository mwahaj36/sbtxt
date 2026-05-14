"use client"
import { useState, useEffect, createContext, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle2, Loader2, RefreshCw } from 'lucide-react';
import { API_URL } from '@/config';

const SyncContext = createContext();

export function SyncProvider({ children }) {
    const [syncStatus, setSyncStatus] = useState({ status: 'idle', processed: 0, total: 0, message: '' });

    useEffect(() => {
        let interval;
        if (syncStatus.status === 'syncing') {
            interval = setInterval(async () => {
                const token = localStorage.getItem("token");
                if (!token) return;

                try {
                    const res = await fetch(`${API_URL}/sbtxt-sync/status`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    const data = await res.json();
                    
                    if (data.status === 'completed') {
                        clearInterval(interval);
                        setSyncStatus(prev => ({ ...prev, ...data, status: 'completed_recently' }));
                        // Reset to idle after 5 seconds
                        setTimeout(() => setSyncStatus(prev => ({ status: 'idle', processed: 0, total: 0 })), 5000);
                    } else if (data.status === 'error') {
                        clearInterval(interval);
                        setSyncStatus(prev => ({ ...prev, ...data }));
                    } else {
                        setSyncStatus(prev => ({ ...prev, ...data }));
                    }
                } catch (e) {
                    console.error("Sync polling failed", e);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [syncStatus.status]);

    const triggerSync = (total) => {
        setSyncStatus({ status: 'syncing', processed: 0, total: total || 1, message: '' });
    };

    const isVisible = syncStatus.status === 'syncing' || 
                      syncStatus.status === 'completed_recently' || 
                      syncStatus.status === 'error';

    return (
        <SyncContext.Provider value={{ syncStatus, triggerSync }}>
            {children}
            
            {/* Global Sync Toast */}
            <AnimatePresence>
                {isVisible && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 50, scale: 0.9 }}
                        className={`fixed bottom-8 right-8 z-[999] backdrop-blur-2xl border p-4 rounded-none flex items-center gap-4 shadow-2xl min-w-[280px]
                            ${syncStatus.status === 'error' ? 'bg-red-950/40 border-red-500/30' : 'bg-black/80 border-[var(--primary)]/30'}`}
                    >
                        <div className="relative w-12 h-12 flex-shrink-0">
                            {syncStatus.status === 'error' ? (
                                <div className="w-full h-full flex items-center justify-center text-red-500">
                                    <AlertCircle size={32} />
                                </div>
                            ) : syncStatus.status === 'completed_recently' ? (
                                <div className="w-full h-full flex items-center justify-center text-[#00e054]">
                                    <CheckCircle2 size={32} />
                                </div>
                            ) : (
                                <div className="w-full h-full">
                                    <svg className="w-full h-full -rotate-90">
                                        <circle 
                                            cx="24" cy="24" r="20" 
                                            className="stroke-white/10 fill-none" 
                                            strokeWidth="4"
                                        />
                                        <motion.circle 
                                            cx="24" cy="24" r="20" 
                                            className={`fill-none ${syncStatus.status === 'error' ? 'stroke-red-500' : 'stroke-[#d946ef]'}`}
                                            strokeWidth="4"
                                            strokeDasharray="125.6"
                                            initial={{ strokeDashoffset: 125.6 }}
                                            animate={{ 
                                                strokeDashoffset: 125.6 - (125.6 * (syncStatus.processed / (syncStatus.total || 1))) 
                                            }}
                                            transition={{ type: "spring", stiffness: 50, damping: 20 }}
                                        />
                                    </svg>
                                    <div className="absolute inset-0 flex items-center justify-center text-[9px] font-black uppercase">
                                        {syncStatus.total > 0 ? Math.round((syncStatus.processed / syncStatus.total) * 100) : 0}%
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex flex-col pr-4">
                            <p className={`text-[10px] font-black uppercase tracking-widest
                                ${syncStatus.status === 'error' ? 'text-red-400' : 'text-white'}`}>
                                {syncStatus.status === 'syncing' ? (syncStatus.message || 'Syncing Vault') : 
                                 syncStatus.status === 'completed_recently' ? 'DNA Mapped' : 'Sync Failed'}
                            </p>
                            <p className="text-[9px] text-white/40 font-bold leading-tight mt-1 max-w-[180px]">
                                {syncStatus.status === 'error' ? (syncStatus.message || "Unknown Error") :
                                 syncStatus.status === 'completed_recently' ? 'Vault fully synchronized' : 
                                 syncStatus.message ? `${syncStatus.processed} / ${syncStatus.total || 0} items — ${syncStatus.message}` :
                                 `${syncStatus.processed} / ${syncStatus.total || 0} items resolved`}
                            </p>
                        </div>
                        
                        {syncStatus.status === 'error' && (
                            <button 
                                onClick={() => setSyncStatus({ status: 'idle', processed: 0, total: 0 })}
                                className="ml-2 p-1.5 hover:bg-white/5 rounded-none text-white/40 hover:text-white transition-all"
                            >
                                <RefreshCw size={14} />
                            </button>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </SyncContext.Provider>
    );
}

export const useSync = () => useContext(SyncContext);
