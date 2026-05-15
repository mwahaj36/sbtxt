"use client"
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, ShieldAlert, Info, X } from 'lucide-react';

export default function ConfirmationModal({ 
    isOpen, 
    onClose, 
    onConfirm, 
    title = "Are you sure?", 
    message = "This action cannot be undone.", 
    confirmText = "Confirm", 
    type = "danger" 
}) {
    const colors = {
        danger: {
            text: "text-red-500",
            bg: "bg-red-500/10",
            border: "border-red-500/30",
            button: "bg-red-600 hover:bg-red-500",
            icon: <ShieldAlert size={48} className="text-red-500" />
        },
        warning: {
            text: "text-yellow-500",
            bg: "bg-yellow-500/10",
            border: "border-yellow-500/30",
            button: "bg-yellow-600 hover:bg-yellow-500",
            icon: <AlertTriangle size={48} className="text-yellow-500" />
        },
        info: {
            text: "text-[var(--primary)]",
            bg: "bg-[var(--primary)]/10",
            border: "border-[var(--primary)]/30",
            button: "bg-[var(--primary)] text-black hover:brightness-110",
            icon: <Info size={48} className="text-[var(--primary)]" />
        }
    };

    const style = colors[type] || colors.danger;

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[2000] flex items-center justify-center px-4">
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/90 backdrop-blur-xl"
                        onClick={onClose}
                    />
                    
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className={`relative w-full max-w-lg bg-black border ${style.border} p-12 md:p-16 shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col items-center text-center`}
                    >
                        <button 
                            onClick={onClose}
                            className="absolute top-6 right-6 text-white/20 hover:text-white transition-colors"
                        >
                            <X size={20} />
                        </button>

                        <div className={`mb-8 p-6 ${style.bg} rounded-none`}>
                            {style.icon}
                        </div>

                        <h2 className={`text-2xl md:text-3xl font-black uppercase tracking-tighter mb-4 ${style.text}`} style={{ fontFamily: 'Arkhip' }}>
                            {title}
                        </h2>
                        
                        <p className="text-[10px] text-white/40 uppercase font-bold tracking-[0.2em] leading-relaxed mb-12 max-w-xs">
                            {message}
                        </p>

                        <div className="flex flex-col w-full gap-4">
                            <button 
                                onClick={() => {
                                    onConfirm();
                                    onClose();
                                }}
                                className={`w-full py-5 ${style.button} text-white font-black uppercase tracking-[0.4em] text-[9px] transition-all shadow-xl`}
                                style={type === 'info' ? { color: 'black' } : {}}
                            >
                                {confirmText}
                            </button>
                            <button 
                                onClick={onClose}
                                className="w-full py-5 bg-white/5 text-white/40 border border-white/10 font-black uppercase tracking-[0.4em] text-[9px] hover:bg-white/10 hover:text-white transition-all"
                            >
                                Cancel
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
