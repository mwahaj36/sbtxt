"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, User, Database, Shield, LogOut, Loader2, CheckCircle2, RefreshCw, UploadCloud, ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useSync } from '@/components/SyncProvider';

export default function SettingsPage() {
    const router = useRouter();
    const { syncStatus, triggerSync } = useSync();
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('profile');
    const [toast, setToast] = useState("");
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);

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

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && (droppedFile.type === "application/zip" || droppedFile.name.endsWith(".zip"))) {
            setFile(droppedFile);
        } else {
            setToast("Please upload a ZIP file.");
        }
    };

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && (selectedFile.type === "application/zip" || selectedFile.name.endsWith(".zip"))) {
            setFile(selectedFile);
        }
    };

    const startSync = async () => {
        if (!file) return;
        const token = localStorage.getItem("token");
        triggerSync(1);
        setToast("Sync started in background!");
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`http://localhost:8000/sync/letterboxd`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` },
                body: formData,
            });
            const data = await res.json();
            triggerSync(data.total_movies);
        } catch (e) {
            setToast("Sync failed to start.");
        }
    };

    if (isLoading) return (
        <div className="h-screen w-full flex items-center justify-center bg-black">
            <Loader2 className="animate-spin text-[var(--primary)]" size={48} />
        </div>
    );

    return (
        <main className="w-full bg-black text-white">
            
            {/* Custom Toast */}
            <AnimatePresence>
                {toast && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="fixed bottom-10 left-1/2 -translate-x-1/2 bg-[var(--primary)] text-black px-8 py-4 rounded-none font-black uppercase tracking-widest text-[10px] z-[1000] border border-black shadow-[0_0_20px_rgba(var(--primary-rgb),0.5)]"
                    >
                        {toast}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* DECK 1: PROFILE & ACCOUNT */}
            <section className="h-screen w-full snap-start flex flex-col pt-32 px-8 relative overflow-hidden bg-[#050505]">
                <div className="max-w-5xl mx-auto w-full h-full flex flex-col items-center justify-center pb-20 text-center">
                    <h2 className="font-['Arkhip'] text-4xl md:text-6xl uppercase tracking-tighter text-white mb-10">Account Details</h2>
                    
                    <div className="flex flex-col items-center gap-10 w-full max-w-lg">
                        <div className="flex flex-col items-center gap-6">
                            <div className="relative group">
                                <img 
                                    src={user.letterboxd_dp || "https://a.ltrbxd.com/resized/avatar/twitter/4/8/9/4/6/7/shard/2126200257/avatar-80.jpg"} 
                                    className="w-32 h-32 rounded-none border-4 border-white/10 group-hover:border-white transition-all duration-500 object-cover"
                                    alt="Avatar"
                                />
                                <button 
                                    onClick={handleUsernameSync}
                                    className="absolute -bottom-3 -right-3 bg-[var(--primary)] text-black p-3 rounded-none hover:brightness-110 transition-colors shadow-xl"
                                >
                                    <RefreshCw size={16} />
                                </button>
                            </div>
                            <div>
                                <h2 className="text-3xl font-black uppercase tracking-tight">{user.username}</h2>
                            </div>
                        </div>

                        <form className="flex flex-col gap-6 w-full items-center" onSubmit={async (e) => {
                            e.preventDefault();
                            const formData = new FormData(e.target);
                            const token = localStorage.getItem("token");
                            setToast("Updating profile...");
                            const lbUsername = formData.get('letterboxd_username');
                            try {
                                const res = await fetch(`http://localhost:8000/auth/update`, {
                                    method: 'PUT',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'Authorization': `Bearer ${token}`
                                    },
                                    body: JSON.stringify({
                                        username: lbUsername || undefined,
                                        email: formData.get('email') || undefined,
                                        letterboxd_username: lbUsername || undefined
                                    })
                                });
                                if (res.ok) {
                                    setToast("Profile updated successfully!");
                                    const updatedRes = await fetch("http://localhost:8000/auth/me", {
                                        headers: { "Authorization": `Bearer ${token}` }
                                    });
                                    setUser(await updatedRes.json());
                                } else {
                                    setToast("Failed to update profile.");
                                }
                            } catch(e) {
                                setToast("Error updating profile.");
                            }
                        }}>
                            <div className="flex flex-col gap-2 w-full">
                                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 text-center">Email Address</label>
                                <input name="email" defaultValue={user?.email} type="email" className="bg-white/5 border border-white/10 p-4 rounded-none outline-none focus:border-white transition-all text-white text-center w-full" />
                            </div>
                            <div className="flex flex-col gap-2 w-full">
                                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 text-center">Letterboxd Username</label>
                                <input name="letterboxd_username" defaultValue={user?.letterboxd_username} type="text" className="bg-white/5 border border-white/10 p-4 rounded-none outline-none focus:border-white transition-all text-white text-center w-full" />
                                <p className="text-[10px] text-white/40 font-bold uppercase tracking-widest mt-1">Changing this updates your App Username. Only do this incase ur letterboxd username is changed else it will break ur account</p>
                            </div>
                            <button type="submit" className="mt-4 px-12 py-5 bg-[var(--primary)] text-black rounded-none font-black uppercase tracking-widest text-xs hover:brightness-110 transition-all shadow-lg">
                                Save Changes
                            </button>
                        </form>

                        <div className="pt-8 border-t border-white/10 w-full flex justify-center">
                            <button 
                                onClick={() => { localStorage.removeItem("token"); router.push("/"); }}
                                className="flex items-center gap-4 px-8 py-5 rounded-none text-red-500 bg-red-500/10 hover:bg-red-500 hover:text-white transition-all font-black uppercase tracking-widest text-xs w-fit shadow-lg"
                            >
                                <LogOut size={20} />
                                Log Out
                            </button>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce opacity-20">
                    <ChevronDown size={24} className="text-white" />
                </div>
            </section>

            {/* DECK 2: DATA & SYNC */}
            <section className="h-screen w-full snap-start flex flex-col pt-32 px-8 relative overflow-hidden bg-[#14181c]">
                <div className="max-w-5xl mx-auto w-full h-full flex flex-col items-center justify-center pb-20 text-center">
                    <h2 className="font-['Arkhip'] text-4xl md:text-6xl uppercase tracking-tighter text-white mb-12">Data & Sync</h2>
                    
                    <div className="flex flex-col gap-8 w-full max-w-2xl">
                        <div className="p-8 bg-white/5 border border-white/10 rounded-none flex flex-col items-center justify-center shrink-0 gap-4">
                            <div className="p-4 bg-white/10 rounded-none">
                                <CheckCircle2 className="text-white" size={32} />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Data Synchronization</h3>
                                <p className="text-white/40 text-sm mt-1">Your cinematic history is up to date.</p>
                            </div>
                        </div>

                        <div 
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => document.getElementById('fileInput').click()}
                            className={`relative shrink-0 cursor-pointer w-full p-8 rounded-none border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center gap-4 min-h-[200px]
                                ${isDragging ? 'border-white bg-white/10' : 'border-white/20 bg-black/20 hover:border-white/40 hover:bg-white/5'}`}
                        >
                            <input
                                id="fileInput"
                                type="file"
                                accept=".zip"
                                className="hidden"
                                onChange={handleFileSelect}
                            />
                            {file ? (
                                <div className="flex flex-col items-center gap-4">
                                    <div className="p-4 bg-white/10 rounded-none">
                                        <Database size={32} className="text-white" />
                                    </div>
                                    <p className="text-lg font-bold text-white">{file.name}</p>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); startSync(); }}
                                        className="px-8 py-4 bg-[var(--primary)] text-black rounded-none font-black uppercase tracking-widest text-[10px] hover:scale-105 transition-all shadow-lg"
                                    >
                                        Start Letterboxd Sync
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <UploadCloud size={48} className="text-white/40 mb-2" />
                                    <p className="text-lg font-bold tracking-tight text-white">Drop your Letterboxd ZIP here</p>
                                    <p className="text-white/40 text-sm">or click to browse files</p>
                                </>
                            )}
                        </div>

                        <div className="p-8 bg-black/20 border border-white/10 rounded-none flex flex-col items-center justify-center gap-4">
                            <h4 className="font-bold uppercase tracking-widest text-xs text-white">Live Username Sync</h4>
                            <p className="text-white/40 text-xs leading-relaxed max-w-sm">Scrape your latest ratings and profile details directly from your public Letterboxd page.</p>
                            <button 
                                onClick={handleUsernameSync}
                                className="mt-4 px-8 py-4 bg-[var(--primary)] text-black rounded-none hover:brightness-110 transition-all font-black uppercase tracking-widest text-[10px] w-fit shadow-lg"
                            >
                                Trigger Sync
                            </button>
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
