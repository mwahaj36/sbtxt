"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, User, Database, Shield, LogOut, Loader2, CheckCircle2, RefreshCw, UploadCloud } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useSync } from '@/components/SyncProvider';

export default function SettingsPage() {
    const router = useRouter();
    const { syncStatus, triggerSync } = useSync();
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('profile');
    const [toast, setToast] = useState("");

    useEffect(() => {
        const fetchUserData = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/auth");
                return;
            }
            try {
                const res = await fetch("http://localhost:8000/auth/me", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const data = await res.json();
                setUser(data);
            } catch (e) {
                console.error("Failed to fetch user", e);
            } finally {
                setIsLoading(false);
            }
        };
        fetchUserData();
    }, []);

    const handleUsernameSync = async () => {
        const token = localStorage.getItem("token");
        setToast("Starting live sync...");
        try {
            const res = await fetch(`http://localhost:8000/sync/profile?username=${user.letterboxd_username}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await res.json();
            setUser(prev => ({ ...prev, letterboxd_dp: data.avatar }));
            setToast("Profile updated!");
        } catch (e) {
            setToast("Sync failed.");
        }
    };

    if (isLoading) return (
        <div className="h-screen w-full flex items-center justify-center bg-black">
            <Loader2 className="animate-spin text-[var(--primary)]" size={48} />
        </div>
    );

    const tabs = [
        { id: 'profile', icon: User, label: 'Profile' },
        { id: 'sync', icon: Database, label: 'Data & Sync' },
        { id: 'account', icon: Shield, label: 'Account' },
    ];

    return (
        <div className="min-h-screen bg-[#050505] text-white pt-24 px-8 pb-12">
            
            {/* Custom Toast */}
            <AnimatePresence>
                {toast && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="fixed bottom-10 left-1/2 -translate-x-1/2 bg-[#00e054] text-black px-8 py-4 rounded-full font-black uppercase tracking-widest text-[10px] z-[1000]"
                    >
                        {toast}
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="max-w-6xl mx-auto flex gap-12">
                
                {/* Sidebar */}
                <div className="w-64 flex flex-col gap-2">
                    <h1 className="font-['arkhip'] text-4xl mb-8 uppercase tracking-tighter">Settings</h1>
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-4 px-6 py-4 rounded-2xl transition-all duration-300 font-bold uppercase tracking-widest text-[10px]
                                ${activeTab === tab.id ? 'bg-white/10 text-white' : 'text-white/40 hover:bg-white/5 hover:text-white/60'}`}
                        >
                            <tab.icon size={16} />
                            {tab.label}
                        </button>
                    ))}
                    <button 
                        onClick={() => { localStorage.removeItem("token"); router.push("/"); }}
                        className="flex items-center gap-4 px-6 py-4 rounded-2xl text-red-500 hover:bg-red-500/10 transition-all font-bold uppercase tracking-widest text-[10px] mt-8"
                    >
                        <LogOut size={16} />
                        Log Out
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 bg-white/5 border border-white/10 rounded-[3rem] p-12 backdrop-blur-2xl">
                    <AnimatePresence mode="wait">
                        {activeTab === 'profile' && (
                            <motion.div 
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="flex flex-col gap-10"
                            >
                                <div className="flex items-center gap-8">
                                    <div className="relative group">
                                        <img 
                                            src={user.letterboxd_dp || "https://a.ltrbxd.com/resized/avatar/twitter/4/8/9/4/6/7/shard/2126200257/avatar-80.jpg"} 
                                            className="w-32 h-32 rounded-full border-4 border-white/10 group-hover:border-[#00e054] transition-all duration-500"
                                            alt="Avatar"
                                        />
                                        <button 
                                            onClick={handleUsernameSync}
                                            className="absolute -bottom-2 -right-2 bg-white text-black p-2 rounded-full hover:bg-[#00e054] transition-colors shadow-xl"
                                        >
                                            <RefreshCw size={16} />
                                        </button>
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-black uppercase tracking-tight">{user.username}</h2>
                                        <p className="text-white/40 font-bold uppercase tracking-widest text-[10px] mt-1">Letterboxd: {user.letterboxd_username || 'Not Linked'}</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-6 mt-4">
                                    <div className="flex flex-col gap-2">
                                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Display Name</label>
                                        <input type="text" value={user.username} readOnly className="bg-white/5 border border-white/10 p-4 rounded-2xl outline-none focus:border-[#00e054] transition-all" />
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Email Address</label>
                                        <input type="email" value={user.email} readOnly className="bg-white/5 border border-white/10 p-4 rounded-2xl outline-none focus:border-[#00e054] transition-all" />
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {activeTab === 'sync' && (
                            <motion.div 
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="flex flex-col gap-8"
                            >
                                <div className="p-8 bg-[#00e054]/10 border border-[#00e054]/20 rounded-[2rem] flex items-center justify-between">
                                    <div className="flex items-center gap-6">
                                        <div className="p-4 bg-[#00e054]/20 rounded-2xl">
                                            <CheckCircle2 className="text-[#00e054]" size={32} />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold">Data Synchronization</h3>
                                            <p className="text-white/40 text-sm">Your cinematic history is up to date.</p>
                                        </div>
                                    </div>
                                    <button 
                                        onClick={() => router.push('/onboarding')}
                                        className="px-8 py-3 bg-[#00e054] text-black rounded-full font-black uppercase tracking-widest text-[10px] hover:scale-105 transition-all shadow-lg shadow-[#00e054]/20"
                                    >
                                        Re-Sync ZIP
                                    </button>
                                </div>

                                <div className="grid grid-cols-2 gap-6">
                                    <div className="p-8 bg-white/5 border border-white/10 rounded-[2rem] flex flex-col gap-4">
                                        <h4 className="font-bold uppercase tracking-widest text-xs">Live Username Sync</h4>
                                        <p className="text-white/40 text-xs leading-relaxed">Scrape your latest ratings and profile details directly from your public Letterboxd page.</p>
                                        <button 
                                            onClick={handleUsernameSync}
                                            className="mt-2 w-full py-4 border border-white/10 rounded-2xl hover:bg-white hover:text-black transition-all font-black uppercase tracking-widest text-[10px]"
                                        >
                                            Trigger Sync
                                        </button>
                                    </div>
                                    <div className="p-8 bg-white/5 border border-white/10 rounded-[2rem] flex flex-col gap-4 opacity-50 cursor-not-allowed">
                                        <h4 className="font-bold uppercase tracking-widest text-xs">Automated Polling</h4>
                                        <p className="text-white/40 text-xs leading-relaxed">Automatically check for new Letterboxd activity every 24 hours. (Coming Soon)</p>
                                        <div className="mt-2 w-full py-4 border border-white/10 rounded-2xl text-center font-black uppercase tracking-widest text-[10px]">
                                            Locked
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
