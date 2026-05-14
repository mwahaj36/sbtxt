"use client"
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Loader2, UploadCloud, FileArchive, X, CheckCircle2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useSync } from '@/components/SyncProvider';
import { API_URL } from '@/config';

export default function Onboard() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const[isOnboarding,setIsOnboarding]=useState(false);

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

    const startSync = async () => {
        if (!file) return;
        const token = localStorage.getItem("token");
        triggerSync(1); // Set to syncing state
        setToast("Sync started on our hardware! You can safely navigate away.");
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`${API_URL}/sbtxt-sync/letterboxd`, {
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

    const fetchProfile = async () => {
        if (!lbUsername) return;
        setIsFinding(true);
        const token = localStorage.getItem("token");
        try {
            const res = await fetch(`${API_URL}/sbtxt-sync/profile?username=${lbUsername}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
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
            await fetch(`${API_URL}/sbtxt-auth/preferences`, {
                method: 'POST',
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` 
                },
                body: JSON.stringify({ vibes: selectedVibes }),
            });
            router.push('/profile');
        } catch (e) {
            console.error("Failed to save preferences", e);
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
        <motion.div 
            initial={{ y: "100vh" }}
            animate={{ y: 0 }}
            transition={{ type: "spring", stiffness: 40, damping: 20 }}
            className=" fixed top-0 left-0 h-screen w-full overflow-y-auto snap-y snap-mandatory bg-white text-black"
        >
            <div className="h-screen w-full bg-[#000000] text-white flex flex-col relative items-center justify-center relative snap-start">
                <h1 className="font-['arkhip'] text-6xl text-center uppercase">
                    Welcome to SBTXT
                </h1>
                <h3 className=" text-2xl text-center uppercase pt-8">
                    Lets Get You Started
                </h3>
                <h2 className='text-xl text-white/50 absolute bottom-10 animate-bounce  duration-500 uppercase  '>
                    Scroll to Get Started
                </h2>
            </div>

            <div className="h-screen w-full bg-[#0a0a0a] text-white flex flex-col relative items-center justify-center snap-start px-20">
                <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    className="max-w-xl w-full text-center"
                >
                    <h1 className="font-['arkhip'] text-6xl mb-8">Who Are You?</h1>
                    <div className="relative group">
                        <input 
                            type="text" 
                            placeholder="Letterboxd Username" 
                            value={lbUsername}
                            onChange={(e) => setLbUsername(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && fetchProfile()}
                            className="w-full bg-transparent border-b-2 border-white/10 py-4 text-3xl font-bold text-center outline-none focus:border-[var(--primary)] transition-all placeholder:text-white/10"
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
                            className="mt-12 flex flex-col items-center gap-4"
                        >
                            <img src={profile.avatar} className="w-24 h-24 rounded-none border-2 border-[var(--primary)] p-1 shadow-2xl" alt="Avatar" />
                            <p className="text-xl font-bold">{profile.name}</p>
                            <p className="text-white/40 text-sm max-w-sm italic line-clamp-2">{profile.bio}</p>
                            <p className='text-xl text-white/50 animate-bounce mt-8 uppercase font-bold tracking-widest text-xs'>
                                Scroll to Continue
                            </p>
                        </motion.div>
                    ) : (
                        <button 
                            onClick={fetchProfile}
                            className="mt-12 px-10 py-4 bg-white text-black rounded-none font-black uppercase tracking-widest text-xs hover:bg-[var(--primary)] transition-all"
                        >
                            Confirm Identity
                        </button>
                    )}
                </motion.div>
            </div>

            <div className="h-screen w-full bg-[#14181c] text-white flex flex-row relative items-center justify-center snap-start px-20 gap-20">
                <div className="flex flex-col gap-8 max-w-2xl">
                    <h1 className="font-['arkhip'] text-6xl text-left">
                        Let's Load Your Letterboxd Data
                    </h1>
                    
                    <div className="space-y-4">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-[var(--primary)]">Export Protocol:</h4>
                        <ul className="space-y-3">
                            {[
                                "Login to Letterboxd on your browser.",
                                "Go to Settings > Import & Export.",
                                "Click 'Export Your Data'.",
                                "Drag that ZIP file into the box on the right!"
                            ].map((s, i) => (
                                <li key={i} className="flex gap-4 items-center text-sm font-medium text-white/40">
                                    <span className="text-[var(--primary)] font-black text-[10px]">{i + 1}.</span>
                                    {s}
                                </li>
                            ))}
                        </ul>
                        <p className="text-[10px] text-white/20 font-bold uppercase tracking-widest pt-4">
                            Note: Processing happens on our hardware. <br/>
                            It is safe to close this tab or leave the page.
                        </p>
                    </div>
                </div>
                <motion.div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={`relative group cursor-pointer w-full max-w-xl p-16 rounded-none border-2 border-dashed transition-all duration-500 flex flex-col items-center justify-center gap-6
                        ${isDragging ? 'border-white bg-white/20' : 'border-white/10 bg-white/5 hover:border-white/30 hover:bg-white/10'}
                        backdrop-blur-md shadow-2xl`}
                    onClick={() => document.getElementById('fileInput').click()}
                >
                    <input
                        id="fileInput"
                        type="file"
                        accept=".zip"
                        className="hidden"
                        onChange={handleFileSelect}
                    />

                    {file ? (
                        <motion.div 
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex flex-col items-center gap-4"
                        >
                            <div className="p-5 bg-white/10 rounded-none relative">
                                <FileArchive size={64} className="text-white" />
                                <div className="absolute -top-2 -right-2 bg-[var(--primary)] text-black rounded-none p-1 shadow-lg">
                                    <CheckCircle2 size={20} />
                                </div>
                            </div>
                            <div className="text-center">
                                <p className="text-xl font-bold max-w-xs truncate">{file.name}</p>
                                <p className="text-white/60 text-sm">
                                    {syncStatus.status === 'syncing' 
                                        ? `Syncing in background...` 
                                        : syncStatus.status === 'completed'
                                        ? "Data synchronized!"
                                        : "Ready to sync"}
                                </p>
                            </div>

                            {syncStatus.status === 'idle' && (
                                <div className="flex flex-col gap-2 w-full">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); startSync(); }}
                                        onKeyDown={(e) => e.key === 'Enter' && startSync()}
                                        className="mt-2 px-8 py-3 bg-[var(--primary)] text-black rounded-none text-lg font-bold hover:scale-105 transition-all shadow-lg shadow-[var(--primary)]/20"
                                    >
                                        Sync My Data
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    ) : (
                        <>
                            <div className={`p-8 rounded-none bg-white/10 transition-all duration-500 ${isDragging ? 'scale-110 rotate-12 bg-white/20' : 'group-hover:scale-110 group-hover:-rotate-6'}`}>
                                <UploadCloud size={64} className="text-white" />
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold tracking-tight">Drop your ZIP here</p>
                                <p className="text-white/50 font-medium">or click to browse files</p>
                            </div>
                            <div className="mt-4 px-4 py-2 bg-white/5 rounded-none border border-white/10">
                                <p className="text-xs font-bold uppercase tracking-widest text-white/40">Letterboxd Export Only</p>
                            </div>
                        </>
                    )}
                </motion.div>
                <AnimatePresence>
                    {(syncStatus.status === 'syncing' || syncStatus.status === 'completed') && (
                        <motion.h2 
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className='text-xl text-white/50 absolute bottom-10 animate-bounce duration-500 flex flex-col items-center gap-2'
                        >
                            <span className="font-bold text-[var(--primary)] uppercase tracking-widest text-sm">
                                {syncStatus.status === 'syncing' ? 'Syncing in background' : 'Success'}
                            </span>
                            Scroll to Continue
                        </motion.h2>
                    )}
                </AnimatePresence>
            </div>

            <div className="h-screen w-full bg-[#0a0a0a] text-white flex flex-col relative items-center justify-center snap-start px-20">
                <div className="max-w-4xl w-full flex flex-col items-center">
                    <motion.div 
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        className="text-center mb-16"
                    >
                        <h1 className="font-['arkhip'] text-6xl mb-4">Refine Your Signal</h1>
                        <p className="text-white/40 text-lg uppercase tracking-[0.3em] font-bold">Pick the vibes that define you</p>
                    </motion.div>

                    <div className="flex flex-wrap justify-center gap-4 max-w-3xl">
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
                                className={`px-8 py-4 rounded-none border-2 transition-all duration-500 font-bold uppercase tracking-widest text-xs
                                    ${selectedVibes.includes(vibe) 
                                        ? "bg-white text-black border-white shadow-[0_0_30px_rgba(255,255,255,0.3)]" 
                                        : "border-white/10 text-white/40 hover:border-white/40 hover:text-white hover:bg-white/5"}`}
                            >
                                {vibe}
                            </motion.button>
                        ))}
                    </div>

                    <motion.button
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        disabled={selectedVibes.length < 3}
                        className={`mt-20 px-12 py-5 font-black uppercase tracking-[0.3em] text-sm rounded-none transition-all shadow-2xl
                            ${selectedVibes.length >= 3 
                                ? "bg-white text-black hover:bg-[var(--primary)] cursor-pointer" 
                                : "bg-white/5 text-white/20 cursor-not-allowed border border-white/10"}`}
                        onClick={savePreferences}
                        onKeyDown={(e) => e.key === 'Enter' && selectedVibes.length >= 3 && savePreferences()}
                    >
                        {selectedVibes.length < 3 ? `Pick ${3 - selectedVibes.length} More` : "Enter the Galaxy"}
                    </motion.button>
                </div>
            </div>
        </motion.div>
    );
}
