"use client"
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { API_URL } from '@/config';

export default function AuthPage() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const[isOnboarding,setIsOnboarding]=useState(false);
    
    // Form States
    const [email, setEmail] = useState("");
    const [username, setUsername] = useState("");
    const [identifier, setIdentifier] = useState(""); // For login (email OR username)
    const [password, setPassword] = useState("");
    const [letterboxd, setLetterboxd] = useState("");
    
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [toast, setToast] = useState(""); // Custom popup state

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            // BEST PRACTICE: Sanitize inputs (remove accidental whitespace, lowercase emails)
            const cleanEmail = email.trim().toLowerCase();
            const cleanUsername = username.trim(); // This is now the Letterboxd username
            const cleanIdentifier = identifier.trim().toLowerCase();

            // BEST PRACTICE: Frontend Validation
            if (!isLogin) {
                if (!cleanEmail.includes("@") || !cleanEmail.includes(".")) {
                    throw new Error("Please enter a valid email address.");
                }
                if (cleanUsername.length < 3) {
                    throw new Error("Username must be at least 3 characters.");
                }
                if (password.length < 8) {
                    throw new Error("Password must be at least 8 characters long.");
                }
            }

            const endpoint = isLogin ? "/auth/login" : "/auth/signup";
            const payload = isLogin 
                ? { identifier: cleanIdentifier, password } 
                : { email: cleanEmail, username: cleanUsername, password, letterboxd_username: cleanUsername };

            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                // FastAPI returns an Array of errors if validation fails (which caused the [object Object] glitch!)
                const errorMessage = Array.isArray(data.detail) 
                    ? `Invalid Input: ${data.detail[0].loc[data.detail[0].loc.length - 1]} ${data.detail[0].msg}`
                    : (data.detail || "Authentication failed");
                throw new Error(errorMessage);
            }

            // Success! Save the JWT wristband to localStorage (works for both login and signup now)
            localStorage.setItem("token", data.access_token);

            if (isLogin) {
                // Redirect the user to the search page
                router.push("/search");
            } else {
                // Signup successful! Show a welcome message and then redirect
                setToast("Welcome to Subtext! Redirecting...");
                setTimeout(() => {
                    router.push("/onboarding");
                }, 2000); // Brief delay so they see the success message
            }

        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="h-screen w-screen overflow-hidden bg-white text-black flex relative">
            
            {/* Custom Reusable Toast Popup */}
            <AnimatePresence>
                {toast && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="absolute bottom-10 left-1/2 -translate-x-1/2 bg-[var(--primary)] text-black px-8 py-4 rounded-none font-black uppercase tracking-widest text-[10px] z-[100] shadow-[0_0_40px_rgba(217,70,239,0.5)] border border-black/10"
                    >
                        {toast}
                    </motion.div>
                )}
            </AnimatePresence>

             <Link 
                href="/" 
                className="absolute top-10 left-10 z-50 flex items-center gap-3 text-white mix-blend-difference hover:opacity-60 transition-opacity"
            >
                <ArrowLeft size={20} />
                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Return</span>
            </Link>
            
            {/* LEFT SIDE: The Signup Form (White Background) */}
            <div className="w-1/2 h-full flex flex-col items-center justify-center p-12 relative">
                <h1 className="font-['Arkhip'] text-6xl mb-12 uppercase tracking-tighter">Join Sbtxt</h1>
                <form onSubmit={handleSubmit} className="w-full max-w-sm flex flex-col">
                    {!isLogin && error && <p className="text-red-500 text-xs font-bold mb-4 uppercase text-center">{error}</p>}
                    
                    <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required={!isLogin} 
                        className="w-full border-b-2 border-black/10 focus:border-black bg-transparent py-3 mb-6 outline-none transition-colors placeholder:text-gray-400" />
                    
                    <div className="w-full mb-6">
                        <input type="text" placeholder="Letterboxd Username" value={username} onChange={e => setUsername(e.target.value)} required={!isLogin} 
                            className="w-full border-b-2 border-black/10 focus:border-black bg-transparent py-3 outline-none transition-colors placeholder:text-gray-400" />
                        <p className="text-[9px] text-gray-400 font-bold uppercase mt-2 text-left tracking-widest w-full">This acts as your app username.</p>
                    </div>
                    
                    <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required={!isLogin} 
                        className="w-full border-b-2 border-black/10 focus:border-black bg-transparent py-3 mb-6 outline-none transition-colors placeholder:text-gray-400" />
                    
                    <button type="submit" disabled={isLoading} className="w-full bg-[var(--primary)] text-black py-4 font-black uppercase tracking-widest text-xs hover:brightness-110 transition-colors flex justify-center items-center h-12">
                        {isLoading && !isLogin ? <Loader2 className="animate-spin text-black" size={16} /> : "Create Account"}
                    </button>
                </form>
            </div>

            {/* RIGHT SIDE: The Login Form (White Background) */}
            <div className="w-1/2 h-full flex flex-col items-center justify-center p-12 relative">
                <h1 className="font-['Arkhip'] text-6xl mb-12 uppercase tracking-tighter">Welcome Back</h1>
                <form onSubmit={handleSubmit} className="w-full max-w-sm flex flex-col">
                    {isLogin && error && <p className="text-red-500 text-xs font-bold mb-4 uppercase text-center">{error}</p>}

                    <input type="text" placeholder="Email or Username" value={identifier} onChange={e => setIdentifier(e.target.value)} required={isLogin} 
                        className="w-full border-b-2 border-black/10 focus:border-black bg-transparent py-3 mb-6 outline-none transition-colors placeholder:text-gray-400" />
                    
                    <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required={isLogin} 
                        className="w-full border-b-2 border-black/10 focus:border-black bg-transparent py-3 mb-10 outline-none transition-colors placeholder:text-gray-400" />
                    
                    <button type="submit" disabled={isLoading} className="w-full bg-[var(--primary)] text-black py-4 font-black uppercase tracking-widest text-xs hover:brightness-110 transition-colors flex justify-center items-center h-12">
                        {isLoading && isLogin ? <Loader2 className="animate-spin text-black" size={16} /> : "Log In"}
                    </button>
                </form>
            </div>

            {/* THE FULL-SCREEN SLIDING COVER (Black Background) */}
            <motion.div 
                animate={{ x: isLogin ? "0%" : "100%" }}
                transition={{ type: "spring", stiffness: 50, damping: 15 }}
                className="absolute top-0 left-0 w-1/2 h-full bg-[#050505] text-white flex flex-col items-center justify-center p-16 text-center z-20 shadow-[0_0_100px_rgba(0,0,0,0.5)]"
            >

                <div className="relative z-10 flex flex-col items-center">
                    <h2 className="font-['Arkhip'] text-5xl mb-6 uppercase tracking-tighter">
                        {isLogin ? "New Here?" : "Already a Member?"}
                    </h2>
                    <p className="text-gray-400 mb-12 text-lg font-light leading-relaxed max-w-sm">
                        {isLogin 
                            ? "Escape the algorithm. Discover cinema through vibes, story, and soul." 
                            : "Welcome back to your personalized cinematic galaxy. We saved your seat."}
                    </p>
                    <button 
                        type="button"
                        onClick={() => {
                            setIsLogin(!isLogin);
                            setError(""); // Clear errors when switching sides
                        }}
                        className="px-10 py-4 bg-[var(--primary)] text-black hover:brightness-110 uppercase tracking-[0.2em] text-xs font-black rounded-none transition-colors"
                    >
                        {isLogin ? "Create Account" : "Go to Login"}
                    </button>
                </div>
            </motion.div>

        </div>
    );
}
