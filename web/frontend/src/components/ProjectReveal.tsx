import { motion } from "framer-motion";
import { ArrowLeft, Download, ExternalLink, ShoppingBag } from "lucide-react";
import heroImage from "@/assets/hero-interior.jpg"; 

// כתובת השרת
const API_BASE_URL = "http://127.0.0.1:5000";

// --- ממשק המוצר (מותאם לנתונים מ-Index.tsx) ---
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

interface ProjectRevealProps {
  generatedImage: string | null;
  recommendations: Product[];
  externalLinks?: ExternalLink[];
  onClose: () => void; 
}

const ProjectReveal = ({
  generatedImage,
  recommendations,
  externalLinks = [],
  onClose,
}: ProjectRevealProps) => {
  
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
          {/* כפתור חזרה */}
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-body text-xs uppercase tracking-widest">Back to Home</span>
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

              <div className="relative aspect-[16/9] md:aspect-[21/9] overflow-hidden border border-white/20">
                <img
                  src={`data:image/jpeg;base64,${generatedImage}`}
                  alt="AI Generated Room Design"
                  className="w-full h-full object-cover"
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

          {/* חלק ב: המלצות איקאה (החלק החשוב!) */}
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
                  // הגנה: אם אין מוצר, אל תרנדר אותו (מונע קריסה)
                  if (!product) return null;

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
                      {/* תמונת המוצר */}
                      <div className="aspect-square overflow-hidden bg-white/5 relative">
                         {product.item_img ? (
                            <img
                              src={`${API_BASE_URL}/${product.item_img}`}
                              alt={product.item_name || 'Product'}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              onError={(e) => {
                                // במקרה של שגיאת טעינה, הסתר את התמונה או שים פלייסהולדר
                                (e.target as HTMLImageElement).style.display = 'none'; 
                              }}
                            />
                         ) : (
                            <div className="flex items-center justify-center h-full text-white/20">No Image</div>
                         )}
                      </div>

                      {/* פרטי המוצר */}
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
                      </div>
                    </motion.a>
                  );
                })}
              </div>
            </motion.section>
          )}

          {/* חלק ג: קישורים חיצוניים (אם יש) */}
          {externalLinks.length > 0 && (
            <motion.section
              className="mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7, duration: 0.7 }}
            >
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-px bg-accent" />
                <h2 className="font-display text-2xl md:text-3xl font-light text-white">
                  Shop The Look
                </h2>
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

          {/* תחתית */}
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