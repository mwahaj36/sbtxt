"use client"
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, User, Database, Shield, LogOut, Loader2, CheckCircle2, RefreshCw, UploadCloud, ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useSync } from '@/components/SyncProvider';
import { API_URL } from '@/config';
import ConfirmationModal from '@/components/ConfirmationModal';

export default function SettingsPage() {
    const router = useRouter();
    const { syncStatus, triggerSync } = useSync();
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('profile');
    const [toast, setToast] = useState("");
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    
    // Modal States
    const [modalConfig, setModalConfig] = useState({ 
        isOpen: false, 
        title: "", 
        message: "", 
        confirmText: "", 
        onConfirm: () => {}, 
        type: "danger" 
    });

    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [toast]);

    useEffect(() => {
        const fetchUserData = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/auth");
                return;
            }
            try {
                const res = await fetch(`${API_URL}/api/v1/sbtxt-auth/me`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const data = await res.json();
                if (!data.letterboxd_username) {
                    router.push("/onboarding");
                    return;
                }
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
            const res = await fetch(`${API_URL}/api/v1/sbtxt-sync/profile?username=${user.letterboxd_username}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await res.json();
            setUser(prev => ({ ...prev, letterboxd_dp: data.avatar }));
            setToast("Profile updated!");
        } catch (e) {
            setToast("Sync failed.");
        }
    };

    const triggerForgotPassword = async () => {
        if (!user?.email) return;
        setToast("Sending reset link...");
        try {
            const res = await fetch(`${API_URL}/api/v1/sbtxt-auth/forgot-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: user.email })
            });
            if (res.ok) {
                setToast("Password reset link sent to your email!");
            } else {
                setToast("Failed to send reset link.");
            }
        } catch (e) {
            setToast("Error sending reset link.");
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

    const startSync = async (wipe = false) => {
        if (!file) return;
        
        if (wipe) {
            setModalConfig({
                isOpen: true,
                title: "DANGER: SYSTEM WIPE",
                message: "This will PERMANENTLY WIPE your entire Subtext library before importing from the ZIP. Are you absolutely sure?",
                confirmText: "WIPE & START FRESH",
                type: "danger",
                onConfirm: () => executeSync(true)
            });
            return;
        }

        executeSync(false);
    };

    const triggerQuickSync = async () => {
        const token = localStorage.getItem("token");
        triggerSync(1, { silent: true });
        setToast("Quick sync started in background!");
        try {
            await fetch(`${API_URL}/api/v1/sbtxt-sync/live`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` }
            });
        } catch (e) {
            setToast("Quick sync failed.");
        }
    };

    const executeSync = async (wipe) => {
        const token = localStorage.getItem("token");
        triggerSync(1);
        setToast(wipe ? "Wipe & Sync started!" : "Sync started in background!");
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('wipe', wipe ? 'true' : 'false');
        
        try {
            const res = await fetch(`${API_URL}/api/v1/sbtxt-sync/letterboxd`, {
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

    const handleDeleteAccount = async () => {
        setModalConfig({
            isOpen: true,
            title: "TERMINATE IDENTITY",
            message: "FINAL WARNING: This will PERMANENTLY DELETE your account and all your movie data. This cannot be undone. All your Taste DNA, constellations, and library history will be gone forever.",
            confirmText: "DELETE EVERYTHING",
            type: "danger",
            onConfirm: async () => {
                const token = localStorage.getItem("token");
                try {
                    const res = await fetch(`${API_URL}/api/v1/sbtxt-auth/delete`, {
                        method: 'DELETE',
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    if (res.ok) {
                        localStorage.removeItem("token");
                        router.push("/");
                    } else {
                        setToast("Failed to delete account.");
                    }
                } catch (e) {
                    setToast("An error occurred during deletion.");
                }
            }
        });
    };

    if (isLoading) return (
        <div className="h-screen w-full flex items-center justify-center bg-black">
            <Loader2 className="animate-spin text-[var(--primary)]" size={48} />
        </div>
    );

    return (
        <main className="w-full bg-black text-white flex flex-col">
            
            <ConfirmationModal 
                isOpen={modalConfig.isOpen}
                onClose={() => setModalConfig({...modalConfig, isOpen: false})}
                onConfirm={modalConfig.onConfirm}
                title={modalConfig.title}
                message={modalConfig.message}
                isDanger={modalConfig.type === "danger"}
            />

            <AnimatePresence>
                {toast && (
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="fixed bottom-10 left-1/2 -translate-x-1/2 bg-[var(--primary)] text-black px-8 py-4 rounded-none font-black uppercase tracking-widest text-xs z-[200] shadow-[0_0_40px_rgba(var(--primary-rgb),0.5)]"
                    >
                        {toast}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* DECK 1: PROFILE & ACCOUNT */}
            <section className="h-[calc(100vh-64px)] md:h-[calc(100vh-80px)] scroll-mt-16 md:scroll-mt-20 w-full snap-start flex flex-col pt-16 md:pt-32 px-8 relative overflow-hidden bg-[#050505]">
                <div className="max-w-6xl mx-auto w-full h-full flex flex-col items-center justify-center pb-20 text-center">
                    <h2 className="font-['Arkhip'] text-4xl md:text-6xl uppercase tracking-tighter text-white mb-12">Account Details</h2>
                    
                    <div className="flex flex-col md:flex-row gap-8 md:gap-16 w-full max-w-5xl justify-center items-center md:items-stretch">
                        
                        {/* LEFT COLUMN: Avatar & Actions */}
                        <div className="flex flex-col items-center justify-between w-full md:w-1/2 py-2">
                            <div className="flex flex-col items-center gap-4">
                                <div className="relative group">
                                    <img 
                                        src={user.letterboxd_dp || "https://a.ltrbxd.com/resized/avatar/twitter/4/8/9/4/6/7/shard/2126200257/avatar-80.jpg"} 
                                        className="w-32 h-32 md:w-40 md:h-40 rounded-none border-4 border-white/10 group-hover:border-[var(--primary)] transition-all duration-500 object-cover"
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
                                    <h2 className="text-2xl md:text-3xl font-black uppercase tracking-tight">{user.username}</h2>
                                </div>
                            </div>

                            <div className="flex flex-col gap-3 w-full max-w-xs mt-8 md:mt-0">
                                <button 
                                    type="button"
                                    onClick={triggerForgotPassword}
                                    className="px-6 py-4 rounded-none text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-all font-black uppercase tracking-widest text-[10px] w-full"
                                >
                                    Send Password Reset
                                </button>
                                <button 
                                    onClick={() => { localStorage.removeItem("token"); router.push("/"); }}
                                    className="flex items-center justify-center gap-3 px-6 py-4 rounded-none text-red-500 bg-red-500/10 hover:bg-red-500 hover:text-white transition-all font-black uppercase tracking-widest text-[10px] w-full"
                                >
                                    <LogOut size={16} />
                                    Log Out
                                </button>
                                <button 
                                    onClick={handleDeleteAccount}
                                    className="px-6 py-4 rounded-none border border-red-500/20 text-red-500/60 hover:text-red-500 hover:border-red-500 transition-all font-black uppercase tracking-widest text-[10px] w-full mt-2"
                                >
                                    Delete Account
                                </button>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: Edit Form */}
                        <div className="flex flex-col w-full md:w-1/2 border border-white/10 bg-white/5 p-8 relative h-full min-h-[400px]">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 mb-8 absolute -top-3 left-8 bg-[#050505] px-2">Edit Profile</h3>
                            <form className="flex flex-col h-full w-full flex-1" onSubmit={async (e) => {
                                e.preventDefault();
                                const formData = new FormData(e.target);
                                const token = localStorage.getItem("token");
                                setToast("Updating profile...");
                                const lbUsername = formData.get('letterboxd_username');
                                try {
                                    const res = await fetch(`${API_URL}/api/v1/sbtxt-auth/update`, {
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
                                        const updatedRes = await fetch(`${API_URL}/api/v1/sbtxt-auth/me`, {
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
                                <div className="flex flex-col flex-1 justify-center gap-8 w-full pb-8">
                                    <div className="flex flex-col gap-2 w-full text-left">
                                        <label className="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--primary)] pl-1">Email Address</label>
                                        <input name="email" defaultValue={user?.email} type="email" className="bg-black/40 border border-white/10 p-4 rounded-none outline-none focus:border-[var(--primary)] transition-all text-white w-full" />
                                    </div>
                                    <div className="flex flex-col gap-2 w-full text-left">
                                        <label className="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--primary)] pl-1">Letterboxd Username</label>
                                        <input name="letterboxd_username" defaultValue={user?.letterboxd_username} type="text" className="bg-black/40 border border-white/10 p-4 rounded-none outline-none focus:border-[var(--primary)] transition-all text-white w-full" />
                                        <p className="text-[9px] text-white/30 font-bold uppercase tracking-widest mt-1 leading-relaxed">Changing this updates your App Username. Only change this if your Letterboxd username changed.</p>
                                    </div>
                                </div>
                                <div className="mt-auto pt-4">
                                    <button type="submit" className="px-12 py-5 bg-[var(--primary)] text-black rounded-none font-black uppercase tracking-widest text-[10px] hover:brightness-110 transition-all shadow-lg w-full">
                                        Save Changes
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce opacity-20">
                    <ChevronDown size={24} className="text-white" />
                </div>
            </section>

            {/* DECK 2: DATA & SYNC */}
            <section className="h-[calc(100vh-64px)] md:h-[calc(100vh-80px)] scroll-mt-16 md:scroll-mt-20 w-full snap-start flex flex-col pt-16 md:pt-32 px-8 relative overflow-hidden bg-[#14181c]">
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
                                    <div className="flex flex-col gap-3">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); startSync(false); }}
                                            className="px-8 py-4 bg-[var(--primary)] text-black rounded-none font-black uppercase tracking-widest text-[10px] hover:scale-105 transition-all shadow-lg"
                                        >
                                            Start Letterboxd Sync
                                        </button>
                                        <p className="text-[8px] uppercase font-black text-white/30 tracking-widest">Safe, additive sync (Recommended)</p>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <UploadCloud size={48} className="text-white/40 mb-2" />
                                    <p className="text-lg font-bold tracking-tight text-white">Drop your Letterboxd ZIP here</p>
                                    <p className="text-white/40 text-sm">or click to browse files</p>
                                </>
                            )}
                        </div>

                        <div className="p-8 bg-black/20 border border-white/10 rounded-none flex flex-col items-center justify-center gap-6">
                            <div className="flex flex-col items-center gap-2">
                                <h4 className="font-bold uppercase tracking-widest text-[10px] text-[var(--primary)]">Sync Intelligence</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-center md:text-left mt-2">
                                    <div className="flex flex-col gap-3 items-center md:items-start">
                                        <div className="flex flex-col gap-1">
                                            <p className="text-[11px] font-black text-white uppercase tracking-widest">Live Sync (Daily)</p>
                                            <p className="text-[10px] text-white/40 leading-relaxed">The "Fast Lane." Instantly pulls new ratings and reviews. <span className="text-white/20 italic">(Note: Cannot detect deletions)</span></p>
                                        </div>
                                        <button 
                                            onClick={triggerQuickSync}
                                            className="px-6 py-2.5 bg-white/5 hover:bg-[var(--primary)] hover:text-black border border-white/10 text-white/60 font-black uppercase tracking-widest text-[9px] transition-all"
                                        >
                                            Sync Activity
                                        </button>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <p className="text-[11px] font-black text-white uppercase tracking-widest">ZIP Sync (Additive)</p>
                                        <p className="text-[10px] text-white/40 leading-relaxed">The "Deep Clean." Reconciles your entire library. Now strictly additive to keep your data safe. <span className="text-white/20 italic">(For deletions, use the Danger Zone below)</span></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce opacity-20">
                    <ChevronDown size={24} className="text-white" />
                </div>
            </section>

            {/* DECK 3: DANGER ZONE */}
            <section className="h-[calc(100vh-64px)] md:h-[calc(100vh-80px)] scroll-mt-16 md:scroll-mt-20 w-full snap-start flex flex-col pt-16 md:pt-32 px-8 relative overflow-hidden bg-black">
                <div className="max-w-4xl mx-auto w-full h-full flex flex-col items-center justify-center text-center pb-20">
                    <div className="p-12 border-2 border-red-500/30 bg-red-500/5 flex flex-col items-center gap-8 max-w-2xl w-full">
                        <div className="p-4 bg-red-500/20 rounded-none text-red-500">
                            <Shield size={48} strokeWidth={3} />
                        </div>
                        
                        <div className="space-y-4">
                            <h2 className="font-['Arkhip'] text-3xl uppercase tracking-tight text-red-500">Danger Zone</h2>
                            <p className="text-sm text-white/60 leading-relaxed">
                                Use this only if you want to perform a <span className="text-white font-bold">Full Database Reset</span>. 
                                This will wipe all existing movie data in Subtext and re-import everything from your ZIP file. 
                                <br/><br/>
                                This is the only way to synchronize deletions (movies you removed from Letterboxd).
                            </p>
                        </div>

                        {file ? (
                            <button 
                                onClick={() => startSync(true)}
                                className="px-12 py-5 bg-red-600 text-white font-black uppercase tracking-[0.2em] text-xs hover:bg-red-500 transition-all shadow-[0_0_30px_rgba(220,38,38,0.3)] w-full md:w-auto"
                            >
                                WIPE DATABASE & START FRESH
                            </button>
                        ) : (
                            <p className="text-red-500/40 text-[10px] font-black uppercase tracking-widest">
                                Upload a ZIP file in the Sync section to enable this button
                            </p>
                        )}
                    </div>
                </div>
            </section>
        </main>
    );
}
