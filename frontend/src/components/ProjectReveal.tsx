import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Download, ExternalLink, ShoppingBag, Heart } from "lucide-react";
import heroImage from "@/assets/hero-interior.jpg"; 

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

const ProjectReveal = ({
  generatedImage,
  recommendations,
  externalLinks = [],
  generationContext,
  onGeneratedImage,
  onClose,
}: ProjectRevealProps) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [savedItems, setSavedItems] = useState<Product[]>([]);

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
    } catch (e) {
      console.error("Failed to load wishlist", e);
    }
  }, []);

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

  // סימולציית התקדמות רכה ומינימלית בזמן ההמתנה
  useEffect(() => {
    if (!isGenerating) {
      setGenerationProgress(0);
      return;
    }
    let current = 0;
    const interval = setInterval(() => {
      current = Math.min(current + 2, 90); // לא עובר 90% עד שהשרת מסיים
      setGenerationProgress(current);
    }, 200);
    return () => clearInterval(interval);
  }, [isGenerating]);

  const handleGeneratePreview = async () => {
    if (!generationContext || isGenerating) return;
    const { originalImagePath, selectedCropUrl, vision } = generationContext;
    if (!originalImagePath || !selectedCropUrl || !vision.trim()) return;

    try {
      setIsGenerating(true);
      const formData = new FormData();
      formData.append("original_image_path", originalImagePath);
      formData.append("selected_crop_url", selectedCropUrl);
      formData.append("prompt", vision);

      const res = await fetch(`${API_BASE_URL}/generate_new_design`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Generation failed");
      }

      const data = await res.json();
      if (data.generated_image && onGeneratedImage) {
        onGeneratedImage(data.generated_image);
      }
    } catch (error) {
      console.error("Generate design failed", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateFromRecommendation = async (product: Product) => {
    if (!generationContext || isGenerating) return;
    const { originalImagePath, selectedCropUrl } = generationContext;
    if (!originalImagePath || !selectedCropUrl || !product.item_img) return;

    try {
        setIsGenerating(true);
        const formData = new FormData();
        formData.append("original_image_path", originalImagePath);
        formData.append("selected_crop_url", selectedCropUrl);
        formData.append("recommendation_image_url", product.item_img); // ודאי שזה אכן URL של ת
        formData.append("prompt", `A ${product.item_name} design`);     // ודאי שזה הטקסט

        const res = await fetch(`${API_BASE_URL}/generate_new_design`, {
            method: "POST",
            body: formData,
        });

        if (!res.ok) throw new Error("Generation failed");

        const data = await res.json();
        
        // כאן התיקון: data.generated_image הוא הסטרינג של התמונה מהשרת
        if (data.generated_image && onGeneratedImage) {
            onGeneratedImage(data.generated_image);
        }
    } catch (error) {
        console.error("Generate from recommendation failed", error);
    } finally {
        setIsGenerating(false);
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
      <div className="absolute inset-0 bg-black/20" />

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
              className="mb-16"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.7 }}
            >
              <h1 className="font-display text-3xl md:text-5xl lg:text-6xl font-light text-white mb-8">
                Your Vision, Realized
              </h1>

              <div className="relative aspect-[16/9] md:aspect-[21/9] overflow-hidden border border-white/20 bg-black">
                <img
                  src={`data:image/jpeg;base64,${generatedImage}`}
                  alt="AI Generated Room Design"
                  className="w-full h-full object-contain"
                />
                <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 bg-gradient-to-t from-black/70 via-black/30 to-transparent">
                  <span className="font-body text-xs uppercase tracking-widest text-white/70">
                    AI Generated Design • CasAI
                  </span>
                </div>
              </div>

              <div className="mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <span className="font-body text-xs uppercase tracking-widest text-white/40">
                  Premium AI Rendering
                </span>
                <button
                  onClick={handleDownload}
                  className="btn-editorial flex items-center gap-3"
                >
                  <Download className="w-4 h-4" />
                  Download High-Res
                </button>
              </div>
            </motion.section>
          )}

          {/* חלק ביניים: הזמנה להדמיה לפני ההמלצות - גרסה נקייה ומינימלית */}
          {!showGeneratedSection && generationContext && (
            <motion.section
              className="mb-10"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.4 }}
            >
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-t border-white/10 pt-6">
                <div className="space-y-1">
                  <p className="font-body text-[11px] uppercase tracking-[0.22em] text-white/45">
                    Curious how this could look as a full scene?
                  </p>
                  <p className="font-body text-sm text-white/70 max-w-md">
                    Generate a clean AI visualization of your space using this piece and your description.
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <button
                    onClick={handleGeneratePreview}
                    disabled={isGenerating}
                    className="px-7 py-3 text-[11px] tracking-[0.2em] uppercase font-light border border-white/40 text-white bg-transparent hover:bg-white/10 transition disabled:opacity-60"
                  >
                    {isGenerating ? (
                      <div className="flex flex-col items-center gap-1">
                        <span className="font-body text-[11px] tracking-[0.18em] uppercase text-white/70">
                          Rendering {generationProgress}%
                        </span>
                        <div className="w-24 h-px bg-white/15 overflow-hidden">
                          <div
                            className="h-full bg-white/80 transition-all duration-200"
                            style={{ width: `${generationProgress}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      "Generate Inspiration"
                    )}
                  </button>
                </div>
              </div>
            </motion.section>
          )}

          {/* חלק ב: המלצות איקאה */}
          {recommendations.length > 0 && (
            <motion.section
              className="mb-16"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: showGeneratedSection ? 0.5 : 0.2, duration: 0.7 }}
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-px bg-accent" />
                <h2 className="font-display text-2xl md:text-3xl font-light text-white">
                  Curated For You
                </h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {recommendations.map((product, index) => {
                  if (!product) return null;

                  const isSaved = savedItems.some((p) => p.item_url === product.item_url);

                  return (
                    <motion.a
                      key={index}
                      href={product.item_url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group block glass-crystal hover:bg-white/15 transition-all duration-300"
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: (showGeneratedSection ? 0.6 : 0.3) + index * 0.1, duration: 0.5 }}
                    >
                      <div className="aspect-square overflow-hidden bg-white/5 relative">
                        {/* Wishlist heart */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            toggleSaveItem(product);
                          }}
                          className="absolute top-3 right-3 z-10 rounded-full bg-black/40 p-2 hover:bg-black/70 transition"
                        >
                          <Heart
                            className={`w-4 h-4 ${
                              isSaved ? "text-accent fill-accent" : "text-white/70"
                            }`}
                          />
                        </button>
                         {product.item_img ? (
                            <img
                              src={`${API_BASE_URL}/${product.item_img}`}
                              alt={product.item_name || 'Product'}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'; 
                              }}
                            />
                         ) : (
                            <div className="flex items-center justify-center h-full text-white/20">No Image</div>
                         )}
                      </div>

                      <div className="p-4">
                        {product.brand && (
                          <span className="font-body text-[10px] uppercase tracking-widest text-accent">
                            {product.brand}
                          </span>
                        )}
                        <h3 className="font-display text-base text-white mt-1 line-clamp-2">
                          {product.item_name || "Unknown Item"}
                        </h3>
                        <div className="flex items-center justify-between mt-3">
                          <span className="font-body text-sm text-white/80">
                            {product.item_price || "N/A"}
                          </span>
                          <span className="font-body text-xs uppercase tracking-widest text-white/50 group-hover:text-accent transition-colors flex items-center gap-1">
                            View
                            <ExternalLink className="w-3 h-3" />
                          </span>
                        </div>
                        
                        {/* Generate Button */}
                        {generationContext && (
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleGenerateFromRecommendation(product);
                            }}
                            disabled={isGenerating}
                            className="w-full mt-3 px-3 py-2 text-[9px] tracking-[0.18em] uppercase font-light border border-white/30 text-white bg-white/5 hover:bg-white/15 transition disabled:opacity-50"
                          >
                            {isGenerating ? "Generating..." : "Visualize"}
                          </button>
                        )}
                      </div>
                    </motion.a>
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
                  <motion.a
                    key={item.id}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 w-60 glass-crystal p-4 hover:bg-white/15 transition-all duration-300 group"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.05, duration: 0.5 }}
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-14 h-14 flex-shrink-0 overflow-hidden border border-white/20">
                        {item.image ? (
                           <img src={item.image} alt={item.title} className="w-full h-full object-cover" />
                        ) : (
                           <div className="w-full h-full bg-white/10 flex items-center justify-center"><ShoppingBag className="w-4 h-4"/></div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-body text-[10px] uppercase tracking-widest text-accent">{item.source}</span>
                        <h4 className="font-display text-sm text-white mt-1 line-clamp-2">{item.title}</h4>
                        <span className="font-body text-xs text-white/60 mt-1 block">{item.price}</span>
                      </div>
                    </div>
                  </motion.a>
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
                  <a
                    key={item.item_url}
                    href={item.item_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 w-40 glass-crystal p-3 hover:bg-white/10 transition-all duration-200"
                  >
                    <div className="aspect-square mb-2 overflow-hidden bg-white/5">
                      {item.item_img && (
                        <img
                          src={`${API_BASE_URL}/${item.item_img}`}
                          alt={item.item_name}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                    <p className="font-display text-xs text-white line-clamp-2 mb-1">
                      {item.item_name}
                    </p>
                    <p className="font-body text-[11px] text-white/70">
                      {item.item_price}
                    </p>
                  </a>
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
            <p className="font-body text-xs uppercase tracking-widest text-white/40 mb-6">Love your new design?</p>
            <button className="btn-editorial">Save This Design</button>
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ProjectReveal;