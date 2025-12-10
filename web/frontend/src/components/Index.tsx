import { useState, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HomeScreen from "@/components/HomeScreen";
import DesignRequestModal from "@/components/DesignRequestModal";
import SearchResults from "@/components/SearchResults"; 

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [results, setResults] = useState<any[]>([]); 
  
  // Ref for scrolling to results
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  // פונקציה שתופעל כשיש תוצאות מהמודל
  const handleResultsFound = (data: any[]) => {
    setResults(data);
    // גלילה חלקה לתוצאות
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  return (
    <div className="relative min-h-screen">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: showSplash ? 0 : 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <HomeScreen onStartProject={() => setIsModalOpen(true)} />
      </motion.div>

      {/* אזור התוצאות - יוצג רק אם יש תוצאות */}
      <div ref={resultsRef}>
        <SearchResults results={results} />
      </div>

      <AnimatePresence>
        {showSplash && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-background"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.h1
              className="font-display text-6xl md:text-8xl font-light tracking-tight text-foreground"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.2 }}
            >
              CasAI
            </motion.h1>
          </motion.div>
        )}
      </AnimatePresence>

      <DesignRequestModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        onResults={handleResultsFound} 
      />
    </div>
  );
};

export default Index;