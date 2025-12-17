import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HomeScreen from "@/components/HomeScreen";
import DesignRequestModal from "@/components/DesignRequestModal";
import ProjectReveal from "@/components/ProjectReveal";

// נניח שיש לנו סוג עבור הקונטקסט
interface SearchContext {
    originalImagePath: string | null;
    selectedCropUrl: string | null;
    vision: string;
}

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [realRecommendations, setRealRecommendations] = useState<any[]>([]);
  
  // כאן נשמור את הקונטקסט (לשימוש עתידי ב-Redesign או לחזרה למודל)
  const [currentContext, setCurrentContext] = useState<SearchContext | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2500);
    return () => clearTimeout(timer);
  }, []);

  // עדכנתי את הפונקציה לקבל גם את ה-context
  const handleResultsFound = (data: any[], context?: SearchContext) => {
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
    if (context) setCurrentContext(context); // שמירת המידע
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
            onClose={() => { 
                setShowResults(false); 
              setRealRecommendations([]); 
              setIsModalOpen(true);
            }}
          />
        ) : (
          <motion.div 
            key="home" 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            transition={{ duration: 0.6 }}
          >
            <HomeScreen onStartProject={() => setIsModalOpen(true)} />
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSplash && (
          <motion.div 
            className="fixed inset-0 z-50 flex items-center justify-center glass-crystal" 
            exit={{ opacity: 0, transition: { duration: 0.8 } }}
          >
            <motion.h1 
              className="font-display text-6xl text-white" 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }}
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
        // הסרתי את onImageGenerated כי DesignRequestModal החדש שלך (מהשלב הקודם) לא משתמש בו,
        // אבל אם עדיין יש לך אותו שם, אפשר להשאיר.
      />
    </div>
  );
};

export default Index;