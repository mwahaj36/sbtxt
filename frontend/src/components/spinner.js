import { motion } from 'framer-motion';

export default function VibeSpinner({ message = "Curating the Cinematic Vibe..." }) {
    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center mt-20 gap-6"
        >
            <div className="relative w-16 h-16">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 border-t-2 border-r-2 border-[--primary] rounded-full"
                />
                <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-2 border-b-2 border-l-2 border-[--primary] rounded-full"
                />
            </div>
            <p className="text-[--foreground] animate-pulse font-medium tracking-[0.2em] text-[10px] uppercase">
                {message}
            </p>
        </motion.div>
    );
}
