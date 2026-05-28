"use client"
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, Loader2, UploadCloud, FileArchive, X, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useSync } from '@/components/SyncProvider';
import { API_URL } from '@/config';

export default function Onboard() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const[isOnboarding,setIsOnboarding]=useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const welcomeRef = useRef(null);
    const identityRef = useRef(null);
    const dataRef = useRef(null);
    const vibesRef = useRef(null);

    const steps = [welcomeRef, identityRef, dataRef, vibesRef];

    const scrollToStep = (index) => {
        setCurrentStep(index);
        steps[index].current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/auth");
        }
    }, [router]);
    
    // Form States
    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [identifier, setIdentifier] = useState(""); // For login (email OR username)
    const [password, setPassword] = useState("");
    const [letterboxd, setLetterboxd] = useState("");
    
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [toast, setToast] = useState(""); // Custom popup state
    const [file, setFile] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const { syncStatus, triggerSync } = useSync();
    const [selectedVibes, setSelectedVibes] = useState([]);
    const [lbUsername, setLbUsername] = useState("");
    const [profile, setProfile] = useState(null);
    const [isFinding, setIsFinding] = useState(false);

    // Progression Guards
    const canProgressToData = !!profile;
    const canProgressToVibes = syncStatus.status === 'syncing' || syncStatus.status === 'completed' || syncStatus.status === 'completed_recently';
    const canFinish = selectedVibes.length >= 3;

    const startSync = async () => {
        if (!file) return;
        const token = localStorage.getItem("token");
        triggerSync(1); // Set to syncing state
        setToast("Sync started on our hardware! You can safely navigate away.");
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`${API_URL}/api/v1/sbtxt-sync/letterboxd`, {
                method: 'POST',
                headers: { "Authorization": `Bearer ${token}` },
                body: formData,
            });
            
            if (res.status === 401) {
                localStorage.removeItem("token");
                router.push("/auth");
                return;
            }

            const data = await res.json();
            triggerSync(data.total_movies);
        } catch (e) {
            setToast("Sync failed to start.");
        }
    };

    const fetchProfile = async () => {
        if (!lbUsername) return;
        setIsFinding(true);
        const token = localStorage.getItem("token");
        try {
            const res = await fetch(`${API_URL}/api/v1/sbtxt-sync/profile?username=${lbUsername}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (res.status === 401) {
                localStorage.removeItem("token");
                router.push("/auth");
                return;
            }

            const data = await res.json();
            setProfile(data);
            setToast(`Found you, ${lbUsername}!`);
        } catch (e) {
            setToast("User not found on Letterboxd.");
        } finally {
            setIsFinding(false);
        }
    };

    const toggleVibe = (vibe) => {
        setSelectedVibes(prev => 
            prev.includes(vibe) ? prev.filter(v => v !== vibe) : [...prev, vibe]
        );
    };

    const savePreferences = async () => {
        const token = localStorage.getItem("token");
        try {
            await fetch(`${API_URL}/api/v1/sbtxt-auth/preferences`, {
                method: 'POST',
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` 
                },
                body: JSON.stringify({ vibes: selectedVibes }),
            });
            router.push('/profile');
        } catch (e) {
            if (process.env.NODE_ENV === 'development') console.error("Failed to save preferences", e);
            router.push('/profile'); // Proceed anyway
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
            // Ideally use your toast system here
            alert("Please upload a ZIP file.");
        }
    };

    const handleFileSelect = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && (selectedFile.type === "application/zip" || selectedFile.name.endsWith(".zip"))) {
            setFile(selectedFile);
        }
    };


    return (
        <div 
            className="fixed top-0 left-0 h-screen w-full overflow-hidden bg-black text-white"
        >
            {/* PROGRESS BAR */}
            <div className="fixed top-0 left-0 w-full h-1 bg-white/5 z-[100]">
                <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
                    className="h-full bg-[var(--primary)] shadow-[0_0_10px_var(--primary-glow)]"
                />
            </div>

            <div className="h-full w-full overflow-hidden">
                {/* SECTION 1: WELCOME */}
                <div ref={welcomeRef} className="h-screen w-full flex flex-col relative items-center justify-center shrink-0 snap-start px-6 py-20">
                    <h1 className="font-['arkhip'] text-3xl md:text-6xl text-center uppercase px-6">
                        Welcome to SBTXT
                    </h1>
                    <h3 className="text-lg md:text-2xl text-center uppercase pt-8 opacity-50">
                        Let's Get You Started
                    </h3>
                    
                    <button 
                        onClick={() => scrollToStep(1)}
                        className="mt-20 px-10 py-4 bg-white text-black font-black uppercase tracking-[0.4em] text-[10px] hover:bg-[var(--primary)] hover:text-white transition-all group flex items-center gap-3"
                    >
                        Initialize Onboarding
                        <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>

                {/* SECTION 2: IDENTITY */}
                <div ref={identityRef} className="h-screen w-full bg-[#0a0a0a] flex flex-col relative items-center justify-center shrink-0 snap-start px-6 md:px-20 py-20 md:py-0">
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        className="max-w-xl w-full text-center"
                    >
                        <h1 className="font-['arkhip'] text-3xl md:text-6xl mb-8">Who Are You?</h1>
                        <div className="relative group">
                            <input 
                                type="text" 
                                placeholder="Letterboxd Username" 
                                value={lbUsername}
                                onChange={(e) => setLbUsername(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && fetchProfile()}
                                autoComplete="off"
                                autoCorrect="off"
                                autoCapitalize="off"
                                spellCheck="false"
                                className="w-full bg-transparent border-b-2 border-white/10 py-4 text-xl md:text-3xl font-bold text-center outline-none focus:border-[var(--primary)] transition-all placeholder:text-white/10"
                            />
                            {isFinding && <Loader2 className="absolute right-4 top-5 animate-spin text-[var(--primary)]" />}
                            <p className="mt-4 text-[10px] text-white/20 font-black uppercase tracking-[0.2em]">
                                Note: Your Letterboxd username will also be your username on Sbtxt.
                            </p>
                        </div>
                        
                        {profile ? (
                            <motion.div 
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="mt-12 flex flex-col items-center gap-6"
                            >
                                <div className="flex flex-col items-center gap-4">
                                    <img src={profile.avatar} className="w-24 h-24 rounded-none border-2 border-[var(--primary)] p-1 shadow-2xl" alt="Avatar" />
                                    <p className="text-xl font-bold">{profile.name}</p>
                                    <p className="text-white/40 text-sm max-w-sm italic line-clamp-2">{profile.bio}</p>
                                </div>

                                <button 
                                    onClick={() => scrollToStep(2)}
                                    className="mt-8 px-10 py-4 bg-[var(--primary)] text-black font-black uppercase tracking-[0.4em] text-[10px] hover:scale-105 transition-all shadow-xl shadow-[var(--primary)]/20"
                                >
                                    Verify & Continue
                                </button>
                            </motion.div>
                        ) : (
                            <button 
                                onClick={fetchProfile}
                                className="mt-12 px-10 py-4 bg-white text-black rounded-none font-black uppercase tracking-widest text-[10px] hover:bg-[var(--primary)] transition-all"
                            >
                                Confirm Identity
                            </button>
                        )}
                    </motion.div>
                </div>

                {/* SECTION 3: DATA */}
                <div ref={dataRef} className="h-screen w-full bg-[#14181c] flex flex-col md:flex-row relative items-center justify-center shrink-0 snap-start px-6 md:px-20 py-20 md:py-0 gap-12 md:gap-20">
                    <div className="flex flex-col gap-8 max-w-2xl">
                        <h1 className="font-['arkhip'] text-3xl md:text-5xl text-left">
                            Load Your <span className="text-[var(--primary)]">Library</span>
                        </h1>
                        
                        <div className="space-y-4">
                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-[var(--primary)] opacity-50">Export Protocol:</h4>
                            <ul className="space-y-3">
                                {[
                                    "Go to Letterboxd Settings > Import & Export.",
                                    "Click 'Export Your Data' to get your ZIP.",
                                    "Drag that file into the vault to the right."
                                ].map((s, i) => (
                                    <li key={i} className="flex gap-4 items-center text-xs font-bold text-white/40 uppercase tracking-widest">
                                        <span className="text-[var(--primary)] font-black text-[10px]">{i + 1}.</span>
                                        {s}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    <div className="w-full max-w-xl flex flex-col gap-6">
                        <motion.div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            whileHover={{ scale: 1.01 }}
                            className={`relative group cursor-pointer w-full p-10 md:p-16 rounded-none border-2 border-dashed transition-all duration-500 flex flex-col items-center justify-center gap-6
                                ${isDragging ? 'border-white bg-white/20' : 'border-white/10 bg-white/5 hover:border-white/30 hover:bg-white/10'}
                                backdrop-blur-md shadow-2xl`}
                            onClick={() => document.getElementById('fileInput').click()}
                        >
                            <input id="fileInput" type="file" accept=".zip" className="hidden" onChange={handleFileSelect} />

                            {file ? (
                                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center gap-4">
                                    <div className="p-5 bg-white/10 rounded-none relative">
                                        <FileArchive size={64} className="text-white" />
                                        {(syncStatus.status === 'completed' || syncStatus.status === 'completed_recently') && (
                                            <div className="absolute -top-2 -right-2 bg-[var(--primary)] text-black rounded-none p-1 shadow-lg">
                                                <CheckCircle2 size={20} />
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-center">
                                        <p className="text-xl font-bold max-w-xs truncate uppercase tracking-tighter">{file.name}</p>
                                        <p className="text-white/40 text-[10px] font-black uppercase tracking-[0.2em] mt-2">
                                            {syncStatus.status === 'syncing' ? `Calibrating: ${syncStatus.processed} resolved` : 
                                             (syncStatus.status === 'completed' || syncStatus.status === 'completed_recently') ? "Vault Synced" : "Ready for Transmission"}
                                        </p>
                                    </div>

                                    {syncStatus.status === 'idle' && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); startSync(); }}
                                            className="mt-2 px-8 py-3 bg-white text-black rounded-none text-[10px] font-black uppercase tracking-[0.4em] hover:bg-[var(--primary)] hover:text-white transition-all shadow-lg"
                                        >
                                            Initiate Sync
                                        </button>
                                    )}
                                </motion.div>
                            ) : (
                                <>
                                    <div className={`p-8 rounded-none bg-white/10 transition-all duration-500 ${isDragging ? 'scale-110 rotate-12' : 'group-hover:scale-110 group-hover:-rotate-6'}`}>
                                        <UploadCloud size={64} className="text-white" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-2xl font-black uppercase tracking-tighter">Drop Library ZIP</p>
                                        <p className="text-white/30 text-[10px] font-black uppercase tracking-widest mt-2">or click to browse files</p>
                                    </div>
                                </>
                            )}
                        </motion.div>

                        {/* NEXT BUTTON FOR DATA STEP */}
                        <AnimatePresence>
                            {canProgressToVibes && (
                                <motion.button
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    onClick={() => scrollToStep(3)}
                                    className="w-full py-4 bg-white/5 border border-white/10 text-white font-black uppercase tracking-[0.4em] text-[10px] hover:bg-[var(--primary)] hover:text-white transition-all flex items-center justify-center gap-3"
                                >
                                    Proceed to Vibes
                                    <ArrowRight size={14} />
                                </motion.button>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* SECTION 4: VIBES */}
                <div ref={vibesRef} className="h-screen w-full bg-[#050505] flex flex-col relative items-center justify-center shrink-0 snap-start px-6 md:px-20 py-20 md:py-0">
                    <div className="max-w-4xl w-full flex flex-col items-center">
                        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} className="text-center mb-16">
                            <h1 className="font-['arkhip'] text-3xl md:text-6xl mb-4">Refine Your Signal</h1>
                            <p className="text-white/30 text-[10px] md:text-lg uppercase tracking-[0.3em] font-black">Select 3+ core cinematic markers</p>
                        </motion.div>

                        <div className="flex flex-wrap justify-center gap-3 max-w-3xl">
                            {[
                                "Mind-Bending", "Neon-Drenched", "Ghibli-esque", "Gritty Realism",
                                "Nostalgic", "Existential", "Visually Stunning", "Cozy",
                                "Dark & Moody", "High-Octane", "Philosophical", "Melancholic"
                            ].map((vibe) => (
                                <motion.button
                                    key={vibe}
                                    onClick={() => toggleVibe(vibe)}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    className={`px-6 py-3 rounded-none border-2 transition-all duration-300 font-black uppercase tracking-widest text-[9px]
                                        ${selectedVibes.includes(vibe) 
                                            ? "bg-[var(--primary)] text-black border-[var(--primary)] shadow-[0_0_20px_var(--primary-glow)]" 
                                            : "border-white/5 text-white/20 hover:border-white/20 hover:text-white hover:bg-white/5"}`}
                                >
                                    {vibe}
                                </motion.button>
                            ))}
                        </div>

                        <motion.button
                            initial={{ opacity: 0 }}
                            whileInView={{ opacity: 1 }}
                            disabled={!canFinish}
                            className={`mt-20 px-12 py-5 font-black uppercase tracking-[0.4em] text-[10px] rounded-none transition-all shadow-2xl
                                ${canFinish 
                                    ? "bg-white text-black hover:bg-[var(--primary)] hover:text-white cursor-pointer" 
                                    : "bg-white/5 text-white/10 cursor-not-allowed border border-white/5"}`}
                            onClick={savePreferences}
                        >
                            {selectedVibes.length < 3 ? `Identify ${3 - selectedVibes.length} more` : "Enter the Galaxy"}
                        </motion.button>
                    </div>
                </div>
            </div>

            {/* CUSTOM TOAST */}
            <AnimatePresence>
                {toast && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="fixed bottom-10 left-1/2 -translate-x-1/2 px-6 py-3 bg-white text-black text-[10px] font-black uppercase tracking-widest z-[200] shadow-2xl"
                    >
                        {toast}
                        <button onClick={() => setToast("")} className="ml-4 opacity-30 hover:opacity-100"><X size={12} /></button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
