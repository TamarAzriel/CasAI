import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HomeScreen from "@/components/HomeScreen";
import DesignRequestModal from "@/components/DesignRequestModal";
import ProjectReveal from "@/components/ProjectReveal";
import StylingChat from "@/components/StylingChat";

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  
  // נתונים אמיתיים בלבד
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [realRecommendations, setRealRecommendations] = useState<any[]>([]);
  const [externalLinks, setExternalLinks] = useState<any[]>([]);
  const [generationContext, setGenerationContext] = useState<{
    originalImagePath: string | null;
    selectedCropUrl: string | null;
    vision: string;
  } | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2500);
    return () => clearTimeout(timer);
  }, []);

  const handleResultsFound = (
    data: any[],
    context?: {
      originalImagePath: string | null;
      selectedCropUrl: string | null;
      vision: string;
      externalLinks?: any[];
    }
  ) => {
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
    setExternalLinks(context?.externalLinks || []);
    setGenerationContext(
      context
        ? {
            originalImagePath: context.originalImagePath,
            selectedCropUrl: context.selectedCropUrl,
            vision: context.vision,
          }
        : null
    );
    setGeneratedImage(null);
    setIsModalOpen(false);
    setShowResults(true);
  };

  const handleImageGenerated = (base64Image: string) => {
    setGeneratedImage(base64Image);
    setRealRecommendations([]);
    // נשארים באותו מסך, רק מוסיפים את ההדמיה למעלה
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
            externalLinks={externalLinks}
            generationContext={generationContext}
            onGeneratedImage={handleImageGenerated}
            onClose={() => { 
              // חזרה מההמלצות למסך העלאת התמונה (המודאל)
              setShowResults(false); 
              setRealRecommendations([]); 
              setExternalLinks([]);
              setGenerationContext(null);
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
            <HomeScreen 
              onStartProject={() => setIsModalOpen(true)}
              onOpenChat={() => setIsChatOpen(true)}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* הרכיב החדש של הצ'אט */}
      <StylingChat 
         isOpen={isChatOpen} 
         onClose={() => setIsChatOpen(false)}
      />

      <AnimatePresence>
        {showSplash && (
          <motion.div 
            className="fixed inset-0 z-50 flex items-center justify-center glass-crystal" 
            exit={{ opacity: 0, transition: { duration: 0.8 } }}
          >
            <motion.h1 
              // הוספתי כאן את text-white
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
        onImageGenerated={handleImageGenerated}
      />
    </div>
  );
};

export default Index;