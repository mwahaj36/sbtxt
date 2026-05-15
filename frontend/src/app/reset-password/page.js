"use client"
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { API_URL } from '@/config';

function ResetPasswordForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [toast, setToast] = useState("");
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setError("Invalid or missing password reset token.");
        }
    }, [token]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        
        if (password.length < 8) {
            setError("Password must be at least 8 characters long.");
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${API_URL}/api/v1/sbtxt-auth/reset-password`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token, new_password: password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Failed to reset password.");
            }

            setToast("Password reset successfully! Redirecting to login...");
            setSuccess(true);
            
            setTimeout(() => {
                router.push('/auth');
            }, 3000);

        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full max-w-sm flex flex-col relative z-10">
            <h1 className="font-['Arkhip'] text-4xl md:text-5xl mb-6 uppercase tracking-tighter text-white text-center">
                Set New Password
            </h1>
            
            {!token ? (
                <div className="text-center text-red-500 font-bold uppercase text-xs mt-8">
                    Invalid or missing token. Please request a new link.
                </div>
            ) : success ? (
                <div className="text-center text-[var(--primary)] font-bold uppercase text-xs mt-8">
                    {toast}
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="flex flex-col mt-8">
                    {error && <p className="text-red-500 text-xs font-bold mb-4 uppercase text-center">{error}</p>}
                    
                    <input 
                        type="password" 
                        placeholder="New Password" 
                        value={password} 
                        onChange={e => setPassword(e.target.value)} 
                        required 
                        className="w-full border-b-2 border-white/20 focus:border-[var(--primary)] text-white bg-transparent py-3 mb-6 outline-none transition-colors placeholder:text-gray-500" 
                    />
                    
                    <input 
                        type="password" 
                        placeholder="Confirm New Password" 
                        value={confirmPassword} 
                        onChange={e => setConfirmPassword(e.target.value)} 
                        required 
                        className="w-full border-b-2 border-white/20 focus:border-[var(--primary)] text-white bg-transparent py-3 mb-10 outline-none transition-colors placeholder:text-gray-500" 
                    />
                    
                    <button 
                        type="submit" 
                        disabled={isLoading} 
                        className="w-full bg-[var(--primary)] text-black py-4 font-black uppercase tracking-widest text-xs hover:brightness-110 transition-colors flex justify-center items-center h-12"
                    >
                        {isLoading ? <Loader2 className="animate-spin text-black" size={16} /> : "Reset Password"}
                    </button>
                </form>
            )}
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <div className="min-h-screen w-screen overflow-x-hidden bg-black text-white flex items-center justify-center relative">
            <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.05)_0%,rgba(0,0,0,1)_70%)]" />
            <Suspense fallback={<Loader2 className="animate-spin text-[var(--primary)]" size={32} />}>
                <ResetPasswordForm />
            </Suspense>
        </div>
    );
}
