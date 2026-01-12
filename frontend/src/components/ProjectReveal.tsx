import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Download, ExternalLink, ShoppingBag, Heart, Bookmark, Check, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import heroImage from "@/assets/hero-interior.jpg"; 
import { cn } from "@/lib/utils";
// כתובת השרת
const API_BASE_URL = "http://127.0.0.1:5000";

export interface Product {
  id: string | number;
  item_name: string;   
  item_price: string;  
  item_img: string;    
  item_url: string;    
  item_cat?: string;
  brand?: string;
}

export interface ExternalLink {
  id: string | number;
  title: string;
  source: string;
  price?: string;
  link: string;
  image?: string;
}

interface GenerationContext {
  originalImagePath: string | null;
  selectedCropUrl: string | null;
  vision: string;
}

interface ProjectRevealProps {
  generatedImage: string | null;
  recommendations: Product[];
  externalLinks?: ExternalLink[];
  generationContext?: GenerationContext | null;
  onGeneratedImage?: (base64Image: string) => void;
  onClose: () => void; 
}

interface SavedProject {
  id: string;
  image: string | null;
  recommendations: Product[];
  date: string;
  vision: string;
}

const ProjectReveal = ({
  generatedImage,
  recommendations,
  externalLinks = [],
  generationContext,
  onGeneratedImage,
  onClose,
}: ProjectRevealProps) => {
  const [savedItems, setSavedItems] = useState<Product[]>([]);
  const [isProjectSaved, setIsProjectSaved] = useState(false);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  // Wishlist persistence (localStorage)
  useEffect(() => {
    try {
      const raw = window.localStorage.getItem("casai_wishlist");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setSavedItems(parsed);
        }
      }

      // Check if this specific project is already saved
      const rawProjects = window.localStorage.getItem("casai_projects");
      if (rawProjects && generatedImage) {
        const projects: SavedProject[] = JSON.parse(rawProjects);
        const exists = projects.some(p => p.image === generatedImage);
        setIsProjectSaved(exists);
      }
    } catch (e) {
      console.error("Failed to load data", e);
    }
  }, [generatedImage]);

  const handleSaveProject = () => {
    if (!generatedImage || isProjectSaved) return;

    try {
      const rawProjects = window.localStorage.getItem("casai_projects");
      const projects: SavedProject[] = rawProjects ? JSON.parse(rawProjects) : [];
      
      const newProject: SavedProject = {
        id: Date.now().toString(),
        image: generatedImage,
        recommendations: recommendations,
        date: new Date().toLocaleDateString(),
        vision: generationContext?.vision || "New Design"
      };

      const updatedProjects = [newProject, ...projects];
      window.localStorage.setItem("casai_projects", JSON.stringify(updatedProjects));
      setIsProjectSaved(true);
    } catch (e) {
      console.error("Failed to save project", e);
    }
  };

  useEffect(() => {
    try {
      window.localStorage.setItem("casai_wishlist", JSON.stringify(savedItems));
    } catch (e) {
      console.error("Failed to save wishlist", e);
    }
  }, [savedItems]);

  const toggleSaveItem = (item: Product) => {
    setSavedItems((current) => {
      const exists = current.some((p) => p.item_url === item.item_url);
      if (exists) {
        return current.filter((p) => p.item_url !== item.item_url);
      }
      return [...current, item];
    });
  };

  const handleGenerateDesign = async (image_url: string, id: string) => {
    if (!onGeneratedImage || !generationContext || !generationContext.originalImagePath || !generationContext.selectedCropUrl) {
      console.error("Missing context for generation");
      return;
    }

    setGeneratingId(id);
    try {
      const formData = new FormData();
      formData.append("original_image_path", generationContext.originalImagePath);
      formData.append("selected_crop_url", generationContext.selectedCropUrl);
      formData.append("recommendation_image_url", image_url);
      formData.append("prompt", generationContext.vision || "A modern interior design");

      const res = await fetch(`${API_BASE_URL}/generate_new_design`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Generation failed");
      const data = await res.json();
      
      if (data.generated_image) {
        onGeneratedImage(data.generated_image);
      }
    } catch (err) {
      console.error("Generation failed", err);
    } finally {
      setGeneratingId(null);
    }
  };

  const handleDownload = () => {
    if (!generatedImage) return;
    const link = document.createElement("a");
    link.href = `data:image/jpeg;base64,${generatedImage}`; 
    link.download = "casai-design.jpeg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const showGeneratedSection = generatedImage && generatedImage.length > 100;

  return (
    <motion.div
      className="fixed inset-0 z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* 1. תמונת רקע למסך מלא */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      <div className="absolute inset-0 bg-black/50" />

      {/* Top Left Logo */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }} 
        animate={{ opacity: 1, x: 0 }} 
        className="absolute top-10 left-10 z-30"
      >
        <button onClick={onClose} className="group">
          <h2 className="font-display text-2xl tracking-[0.2em] text-white group-hover:text-accent transition-colors text-left">CasAI</h2>
          <div className="w-0 group-hover:w-full h-px bg-accent transition-all duration-500" />
        </button>
      </motion.div>

      {/* 2. הקונטיינר הראשי עם גלילה */}
      <div className="relative z-10 h-full overflow-y-auto p-4 md:p-8 lg:p-12">
        <motion.div
          className="glass-crystal max-w-6xl mx-auto p-6 md:p-10 lg:p-12"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          {/* כפתור חזרה - עודכן */}
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-body text-xs uppercase tracking-widest">Back</span>
          </button>

          {/* חלק א: תמונת ה-AI (אם קיימת) */}
          {showGeneratedSection && (
            <motion.section
              className="mb-20 pt-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.7 }}
            >
              <div className="flex flex-col md:flex-row gap-12 items-end mb-10">
                <div className="flex-1">
                  <span className="font-body text-[9px] uppercase tracking-[0.5em] text-accent mb-4 block">Neural Vision Realized</span>
                  <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-light text-white leading-none tracking-tight">
                    Your Space, <br />Redefined.
                  </h1>
                </div>
                <div className="flex flex-col items-end gap-4">
                  <span className="font-body text-[10px] uppercase tracking-widest text-white/30 text-right max-w-[200px]">
                    Proprietary AI blending IKEA design with your architectural DNA.
                  </span>
                  <button
                    onClick={handleDownload}
                    className="px-6 py-3 bg-white text-black rounded-xl font-body text-[9px] uppercase tracking-[0.3em] hover:bg-accent hover:text-white transition-all shadow-2xl flex items-center gap-3 group"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download Masterpiece
                  </button>
                  <button
                    onClick={handleSaveProject}
                    className={`px-6 py-3 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] transition-all shadow-2xl flex items-center gap-3 border ${
                      isProjectSaved 
                        ? "bg-accent text-white border-accent" 
                        : "bg-black/40 backdrop-blur-md text-white border-white/20 hover:bg-white/10"
                    }`}
                  >
                    {isProjectSaved ? (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        Project Saved
                      </>
                    ) : (
                      <>
                        <Heart className="w-3.5 h-3.5" />
                        Save Full Design
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="relative group/main">
                <div className="absolute -inset-4 bg-accent/5 rounded-[3rem] blur-2xl opacity-0 group-hover/main:opacity-100 transition-opacity duration-1000" />
                <div className="relative aspect-[16/9] md:aspect-[21/9] overflow-hidden rounded-[2.5rem] border border-white/10 bg-black shadow-[0_50px_100px_-20px_rgba(0,0,0,0.5)]">
                  <img
                    src={`data:image/jpeg;base64,${generatedImage}`}
                    alt="AI Generated Room Design"
                    className="w-full h-full object-contain scale-105 group-hover/main:scale-100 transition-transform duration-[2s] ease-out"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
                  <div className="absolute bottom-10 left-10 flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-accent/20 backdrop-blur-md border border-accent/30 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-accent" />
                    </div>
                    <div>
                      <p className="font-body text-[10px] uppercase tracking-widest text-white">CasAI Generative Engine</p>
                      <p className="font-body text-[8px] uppercase tracking-[0.4em] text-white/40 mt-1">High-Fidelity Architectural Rendering</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.section>
          )}

          {/* חלק ב: המלצות איקאה */}
          {recommendations.length > 0 && (
            <motion.section
              className="mb-20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: showGeneratedSection ? 0.5 : 0.2, duration: 0.7 }}
            >
              <div className="flex items-center justify-between mb-12">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-px bg-accent/30" />
                  <h2 className="font-display text-3xl md:text-4xl font-light text-white tracking-tight">
                    {showGeneratedSection ? "Complementary Pieces" : "Curated Selection"}
                  </h2>
                </div>
                
                <Link 
                  to="/saved" 
                  className="hidden md:flex items-center gap-3 text-white/40 hover:text-accent transition-colors group"
                >
                  <span className="font-body text-[9px] uppercase tracking-[0.3em]">View Collection</span>
                  <Bookmark className="w-3 h-3 group-hover:fill-accent transition-all" />
                </Link>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {recommendations.map((product, index) => {
                  if (!product) return null;

                  const isSaved = savedItems.some((p) => p.item_url === product.item_url);
                  const isGenerating = generatingId === product.id.toString();

                  return (
                    <motion.div
                      key={index}
                      className="group relative block glass-crystal rounded-[2rem] p-4 hover:bg-white/10 transition-all duration-500 border border-white/10 flex flex-col h-full"
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: (showGeneratedSection ? 0.6 : 0.3) + index * 0.1, duration: 0.5 }}
                    >
                      <div className="relative aspect-square overflow-hidden rounded-[1.5rem] mb-6 bg-white/5">
                        {/* Wishlist heart */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            toggleSaveItem(product);
                          }}
                          className="absolute top-3 right-3 z-10 rounded-full bg-black/40 p-2 hover:bg-black/70 transition backdrop-blur-md"
                        >
                          <Heart
                            className={`w-4 h-4 ${
                              isSaved ? "text-accent fill-accent" : "text-white/70"
                            }`}
                          />
                        </button>

                        {/* Simulation Button */}
                        <button
                          type="button"
                          disabled={isGenerating}
                          onClick={() => handleGenerateDesign(product.item_img, product.id.toString())}
                          className={cn(
                            "absolute bottom-3 right-3 z-10 rounded-xl px-4 py-2 flex items-center gap-2 backdrop-blur-md transition-all text-[9px] uppercase tracking-widest font-body",
                            isGenerating 
                              ? "bg-accent text-white animate-pulse" 
                              : "bg-black/60 text-white/90 hover:bg-accent hover:text-white border border-white/10"
                          )}
                        >
                          {isGenerating ? (
                            <>
                              <div className="w-2 h-2 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                              Simulating...
                            </>
                          ) : (
                            <>
                              <Sparkles className="w-3 h-3 text-accent group-hover:text-white transition-colors" />
                              Simulation
                            </>
                          )}
                        </button>

                         {product.item_img ? (
                            <img
                              src={`${API_BASE_URL}/${product.item_img}`}
                              alt={product.item_name || 'Product'}
                              className="w-full h-full object-cover group-hover:scale-105 transition-all duration-700"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'; 
                              }}
                            />
                         ) : (
                            <div className="flex items-center justify-center h-full text-white/20">No Image</div>
                         )}
                      </div>

                      <div className="space-y-3 px-2 flex-1 flex flex-col justify-between">
                        <div className="text-right rtl">
                          <p className="font-body text-[9px] uppercase tracking-[0.3em] text-accent font-medium mb-1">
                            {product.brand || "IKEA SELECTION"}
                          </p>
                          <h3 className="font-display text-lg text-white font-light line-clamp-2 leading-tight">
                            {product.item_name || "Unknown Item"}
                          </h3>
                        </div>
                        <div className="flex justify-between items-center pt-4 border-t border-white/5 mt-auto">
                          <span className="font-body text-sm text-white/40 tracking-wider">
                            {product.item_price || "N/A"}
                          </span>
                          <a 
                            href={product.item_url || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-body text-[10px] uppercase tracking-widest text-white/30 group-hover:text-accent transition-colors flex items-center gap-1"
                          >
                            View
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.section>
          )}

          {/* חלק ג: קישורים חיצוניים */}
          {externalLinks.length > 0 && (
            <motion.section
              className="mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.7 }}
            >
              <div className="flex flex-col gap-2 mb-8">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-px bg-accent" />
                  <h2 className="font-display text-2xl md:text-3xl font-light text-white">
                    More Options
                  </h2>
                </div>
                <p className="font-body text-[11px] uppercase tracking-[0.18em] text-white/50">
                  Additional options that may fit your style from Google Shopping
                </p>
              </div>
              <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide -mx-2 px-2">
                {externalLinks.map((item, index) => (
                    <motion.div
                      key={item.id}
                      className="flex-shrink-0 w-64 glass-crystal p-4 hover:bg-white/15 transition-all duration-300 group relative"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.8 + index * 0.05, duration: 0.5 }}
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-16 h-16 flex-shrink-0 overflow-hidden border border-white/20 relative group/img">
                          {item.image ? (
                             <>
                               <img src={item.image} alt={item.title} className="w-full h-full object-cover" />
                               <button 
                                 onClick={() => handleGenerateDesign(item.image!, item.id.toString())}
                                 disabled={generatingId === item.id.toString()}
                                 className={cn(
                                   "absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover/img:opacity-100 transition-opacity",
                                   generatingId === item.id.toString() && "opacity-100"
                                 )}
                               >
                                 {generatingId === item.id.toString() ? (
                                   <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                 ) : (
                                   <Sparkles className="w-4 h-4 text-accent" />
                                 )}
                               </button>
                             </>
                          ) : (
                             <div className="w-full h-full bg-white/10 flex items-center justify-center"><ShoppingBag className="w-4 h-4"/></div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="font-body text-[10px] uppercase tracking-widest text-accent">{item.source}</span>
                          <h4 className="font-display text-sm text-white mt-1 line-clamp-2">{item.title}</h4>
                          <span className="font-body text-xs text-white/60 mt-1 block">{item.price}</span>
                          <a 
                            href={item.link} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-[8px] uppercase tracking-[0.2em] text-white/30 hover:text-white mt-2 inline-block transition-colors"
                          >
                            View Source
                          </a>
                        </div>
                      </div>
                    </motion.div>
                ))}
              </div>
            </motion.section>
          )}

          {/* חלק ד: Wishlist שמור */}
          {savedItems.length > 0 && (
            <motion.section
              className="mt-4 mb-8"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-8 h-px bg-accent" />
                <h3 className="font-display text-lg font-light text-white">
                  Saved for later
                </h3>
              </div>

              <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                {savedItems.map((item) => (
                  <div
                    key={item.item_url}
                    className="flex-shrink-0 w-40 glass-crystal p-3 hover:bg-white/10 transition-all duration-200 group/saved relative"
                  >
                    <div className="aspect-square mb-2 overflow-hidden bg-white/5 relative group/img">
                      {item.item_img && (
                        <>
                          <img
                            src={`${API_BASE_URL}/${item.item_img}`}
                            alt={item.item_name}
                            className="w-full h-full object-cover"
                          />
                          <button 
                            onClick={() => handleGenerateDesign(item.item_img, item.item_url)}
                            disabled={generatingId === item.item_url}
                            className={cn(
                              "absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover/img:opacity-100 transition-opacity",
                              generatingId === item.item_url && "opacity-100"
                            )}
                          >
                            {generatingId === item.item_url ? (
                              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                            ) : (
                              <Sparkles className="w-4 h-4 text-accent" />
                            )}
                          </button>
                        </>
                      )}
                    </div>
                    <p className="font-display text-xs text-white line-clamp-2 mb-1">
                      {item.item_name}
                    </p>
                    <div className="flex justify-between items-center">
                      <p className="font-body text-[11px] text-white/70">
                        {item.item_price}
                      </p>
                      <a href={item.item_url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="w-2.5 h-2.5 text-white/20 hover:text-white transition-colors" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </motion.section>
          )}

          <motion.div
            className="text-center pt-8 border-t border-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <p className="font-body text-xs uppercase tracking-widest text-white/40 mb-6">
              {isProjectSaved ? "Design added to your collection" : "Love your new design?"}
            </p>
            <button 
              onClick={handleSaveProject}
              disabled={isProjectSaved || !generatedImage}
              className={cn(
                "px-8 py-3.5 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] transition-all shadow-xl flex items-center gap-2 mx-auto",
                isProjectSaved 
                  ? "bg-accent text-white border border-accent/20" 
                  : "bg-black/40 backdrop-blur-md text-white border border-white/20 hover:bg-white/10"
              )}
            >
              {isProjectSaved ? (
                <>
                  <Check className="w-3 h-3" />
                  Saved to Projects
                </>
              ) : (
                "Save This Design"
              )}
            </button>
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ProjectReveal;