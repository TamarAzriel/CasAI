import { motion } from "framer-motion";
import { Armchair, MessageCircle, Heart } from "lucide-react"; 
import { Link } from "react-router-dom";
import heroImage from "@/assets/hero-interior.jpg";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface HomeScreenProps {
  onStartProject: () => void;
  onOpenChat: () => void;
}

const HomeScreen = ({ onStartProject, onOpenChat }: HomeScreenProps) => {
  const [hasSavedItems, setHasSavedItems] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("casai_wishlist");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) {
        setHasSavedItems(true);
      }
    }
  }, []);

  return (
    <div className="relative h-screen w-full flex items-center justify-center overflow-hidden">
      {/* 1. Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat z-0"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      <div className="absolute inset-0 bg-black/60 z-10" />

      {/* Top Right - Collection Link (Saved Pieces) */}
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.5 }}
        className="absolute top-10 right-10 z-30"
      >
        <Link 
          to="/saved" 
          className="group flex items-center gap-4 py-2 px-6 bg-black/40 backdrop-blur-md rounded-xl hover:bg-white/10 transition-all border border-white/20 shadow-xl"
        >
          <Heart className={cn("w-3.5 h-3.5", hasSavedItems ? "text-accent fill-accent" : "text-white/40")} />
          <span className="font-body text-[9px] uppercase tracking-[0.3em] text-white/60 group-hover:text-white transition-colors">
            {hasSavedItems ? "Collection" : "Saved"}
          </span>
          {hasSavedItems && (
            <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          )}
        </Link>
      </motion.div>

      {/* 2. Main Content - Better hierarchy and spacing */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, ease: [0.19, 1, 0.22, 1] }}
        className="relative z-20 w-full max-w-5xl mx-auto px-6 h-full flex flex-col justify-center items-center text-center"
      >
        {/* Hero Content Group - Moved up to stay on the clear wall area */}
        <div className="mt-[-10vh]">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-2 mb-6"
          >
            <span className="font-body text-[9px] uppercase tracking-[0.8em] text-accent font-bold block">
              Aesthetic Intelligence
            </span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="font-display text-5xl md:text-7xl lg:text-8xl text-white font-light leading-[1.05] tracking-tight text-shadow-editorial mb-8"
          >
            Curate Your <br />Design Reality.
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="font-body text-xs md:text-sm text-white/50 leading-relaxed tracking-[0.1em] max-w-lg mx-auto font-light mb-12"
          >
            Neural-driven interior curation for the modern architectural space. <br className="hidden md:block" />
            Define your vision, and let our AI transform your environment.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-5 items-center justify-center"
          >
            <button
              onClick={onStartProject}
              className="px-8 py-3.5 bg-black/40 backdrop-blur-md text-white border border-white/20 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all shadow-xl flex items-center gap-3 group"
            >
              <Armchair className="w-4 h-4 text-accent" />
              Start Project
            </button>
            
            <button
              onClick={onOpenChat}
              className="px-8 py-3.5 bg-black/40 backdrop-blur-md text-white border border-white/20 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all shadow-xl flex items-center gap-3 group"
            >
              <MessageCircle className="w-4 h-4 text-accent" />
              AI Stylist
            </button>
          </motion.div>
        </div>
      </motion.div>

      {/* Top Left Logo */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }} 
        animate={{ opacity: 1, x: 0 }} 
        className="absolute top-10 left-10 z-30"
      >
        <Link to="/" className="group">
          <h2 className="font-display text-2xl tracking-[0.2em] text-white group-hover:text-accent transition-colors">CasAI</h2>
          <div className="w-0 group-hover:w-full h-px bg-accent transition-all duration-500" />
        </Link>
      </motion.div>

    </div>
  );
};

export default HomeScreen;