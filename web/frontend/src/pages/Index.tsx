import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HomeScreen from "@/components/HomeScreen";
import DesignRequestModal from "@/components/DesignRequestModal";
import ProjectReveal from "@/components/ProjectReveal";

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  
  // נתונים אמיתיים בלבד
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [realRecommendations, setRealRecommendations] = useState<any[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2500);
    return () => clearTimeout(timer);
  }, []);

  const handleResultsFound = (data: any[]) => {
    // עיבוד התוצאות מהשרת לפורמט של האתר
    const formatted = data.map((item, i) => ({
        id: String(i),
        item_name: item.item_name || item.name,
        item_price: item.item_price || item.price,
        item_cat: item.item_cat || "Furniture",
        item_url: item.item_url || item.link,
        item_img: item.item_img || item.image
    }));
    
    setRealRecommendations(formatted);
    setGeneratedImage(null);
    setIsModalOpen(false);
    setShowResults(true);
  };

  const handleImageGenerated = (base64Image: string) => {
    setGeneratedImage(base64Image);
    setRealRecommendations([]);
    setIsModalOpen(false);
    setShowResults(true);
  };

  return (
    <div className="relative min-h-screen">
      <AnimatePresence mode="wait">
        {showResults ? (
          <ProjectReveal 
            key="results"
            generatedImage={generatedImage}
            recommendations={realRecommendations}
            onClose={() => { setShowResults(false); setRealRecommendations([]); }}
          />
        ) : (
          <motion.div key="home" initial={{ opacity: 0 }} animate={{ opacity: showSplash ? 0 : 1 }} transition={{ duration: 0.6 }}>
            <HomeScreen onStartProject={() => setIsModalOpen(true)} />
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSplash && (
          <motion.div className="fixed inset-0 z-50 flex items-center justify-center bg-background" exit={{ opacity: 0 }}>
            <motion.h1 className="font-display text-6xl" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>CasAI</motion.h1>
          </motion.div>
        )}
      </AnimatePresence>

      <DesignRequestModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        onResults={handleResultsFound} 
        onImageGenerated={handleImageGenerated}
      />
    </div>
  );
};

export default Index;