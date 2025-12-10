import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import HomeScreen from "@/components/HomeScreen";
import DesignRequestModal from "@/components/DesignRequestModal";
import ProjectReveal, { Product, ExternalLink } from "@/components/ProjectReveal";
import heroImage from "@/assets/hero-interior.jpg";

// Mock IKEA recommendations data
const mockRecommendations: Product[] = [
  {
    id: "1",
    name: "SÖDERHAMN Modular Sofa",
    brand: "IKEA",
    price: "$1,299",
    image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400&h=400&fit=crop",
    link: "https://ikea.com",
  },
  {
    id: "2",
    name: "STOCKHOLM Floor Lamp",
    brand: "IKEA",
    price: "$199",
    image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",
    link: "https://ikea.com",
  },
  {
    id: "3",
    name: "LISABO Coffee Table",
    brand: "IKEA",
    price: "$149",
    image: "https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=400&h=400&fit=crop",
    link: "https://ikea.com",
  },
  {
    id: "4",
    name: "SKURUP Pendant Lamp",
    brand: "IKEA",
    price: "$34.99",
    image: "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop",
    link: "https://ikea.com",
  },
];

// Mock Google Shopping external links
const mockExternalLinks: ExternalLink[] = [
  {
    id: "e1",
    title: "Modern Velvet Armchair",
    source: "West Elm",
    price: "$799",
    link: "https://westelm.com",
    image: "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=200&h=200&fit=crop",
  },
  {
    id: "e2",
    title: "Marble Side Table",
    source: "CB2",
    price: "$349",
    link: "https://cb2.com",
    image: "https://images.unsplash.com/photo-1499933374294-4584851497cc?w=200&h=200&fit=crop",
  },
  {
    id: "e3",
    title: "Wool Area Rug 8x10",
    source: "Rugs USA",
    price: "$459",
    link: "https://rugsusa.com",
    image: "https://images.unsplash.com/photo-1600166898405-da9535204843?w=200&h=200&fit=crop",
  },
  {
    id: "e4",
    title: "Ceramic Table Lamp",
    source: "Target",
    price: "$89",
    link: "https://target.com",
  },
  {
    id: "e5",
    title: "Linen Throw Pillows Set",
    source: "Anthropologie",
    price: "$128",
    link: "https://anthropologie.com",
    image: "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=200&h=200&fit=crop",
  },
];

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string>(heroImage);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  const handleGenerate = (image: string | null) => {
    setGeneratedImage(image || heroImage);
    setIsModalOpen(false);
    setShowResults(true);
  };

  const handleBackToHome = () => {
    setShowResults(false);
    setGeneratedImage(heroImage);
  };

  return (
    <div className="relative min-h-screen">
      <AnimatePresence mode="wait">
        {showResults ? (
          <ProjectReveal
            key="results"
            generatedImage={generatedImage}
            recommendations={mockRecommendations}
            externalLinks={mockExternalLinks}
            onBack={handleBackToHome}
          />
        ) : (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: showSplash ? 0 : 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <HomeScreen onStartProject={() => setIsModalOpen(true)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Splash screen overlay */}
      <AnimatePresence>
        {showSplash && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-background"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <motion.h1
              className="font-display text-6xl md:text-8xl font-light tracking-tight text-foreground"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
            >
              CasAI
            </motion.h1>
          </motion.div>
        )}
      </AnimatePresence>

      <DesignRequestModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onGenerate={handleGenerate}
      />
    </div>
  );
};

export default Index;
