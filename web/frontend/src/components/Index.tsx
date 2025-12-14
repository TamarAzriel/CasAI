const API_BASE_URL = "http://127.0.0.1:5000";

import { motion } from "framer-motion";
import { ArrowLeft, Download, ExternalLink, ShoppingBag } from "lucide-react";
import heroImage from "@/assets/hero-interior.jpg"; 

// --- ממשק מתוקן (תואם ל-Index.tsx) ---
export interface Product {
  id: string | number;
  item_name: string;   // שם המוצר (במקום name)
  item_price: string;  // מחיר (במקום price)
  item_img: string;    // נתיב תמונה (במקום image)
  item_url: string;    // קישור (במקום link)
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
// ------------------------------------------------------------------

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

  // בדיקה אם יש תמונה גנרטיבית להציג
  const showGeneratedSection = generatedImage && generatedImage.length > 100;

  return (
    <motion.div
      className="fixed inset-0 z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* Full-screen Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      <div className="absolute inset-0 bg-black/20" />

      {/* Glass Crystal Content Container */}
      <div className="relative z-10 h-full overflow-y-auto p-4 md:p-8 lg:p-12">
        <motion.div
          className="glass-crystal max-w-6xl mx-auto p-6 md:p-10 lg:p-12"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          {/* Header / Back Button */}
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-body text-xs uppercase tracking-widest">Back to Home</span>
          </button>

          {/* Section 1: Hero - Generated Image (מוצג רק אם קיים) */}
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

              {/* Cinematic Image Container */}
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

              {/* Download Button */}
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

          {/* Section 2: Curated For You - IKEA Recommendations */}
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
                  // הגנה בסיסית: אם אין מוצר, דלג
                  if (!product) return null;

                  return (
                    <motion.a
                      key={product.id}
                      href={product.item_url} // תוקן ל-item_url
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group block glass-crystal hover:bg-white/15 transition-all duration-300"
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: (showGeneratedSection ? 0.6 : 0.3) + index * 0.1, duration: 0.5 }}
                    >
                      {/* Product Image */}
                      <div className="aspect-square overflow-hidden">
                        <img
                          // תוקן: שרשור כתובת השרת + item_img
                          src={product.item_img ? `${API_BASE_URL}/${product.item_img}` : ""}
                          alt={product.item_name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      </div>

                      {/* Product Info */}
                      <div className="p-4">
                        {product.brand && (
                          <span className="font-body text-[10px] uppercase tracking-widest text-accent">
                            {product.brand}
                          </span>
                        )}
                        <h3 className="font-display text-base text-white mt-1 line-clamp-2">
                          {product.item_name} {/* תוקן ל-item_name */}
                        </h3>
                        <div className="flex items-center justify-between mt-3">
                          <span className="font-body text-sm text-white/80">
                            {product.item_price} {/* תוקן ל-item_price */}
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

          {/* Section 3: Shop The Look (נשאר ללא שינוי, לא בשימוש כרגע אבל קיים למניעת שגיאות) */}
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
                      {item.image ? (
                        <div className="w-14 h-14 flex-shrink-0 overflow-hidden border border-white/20">
                          <img
                            src={item.image}
                            alt={item.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="w-14 h-14 flex-shrink-0 border border-white/20 flex items-center justify-center bg-white/5">
                          <ShoppingBag className="w-5 h-5 text-white/30" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="font-body text-[10px] uppercase tracking-widest text-accent">
                          {item.source}
                        </span>
                        <h4 className="font-display text-sm text-white mt-1 line-clamp-2">
                          {item.title}
                        </h4>
                        {item.price && (
                          <span className="font-body text-xs text-white/60 mt-1 block">
                            {item.price}
                          </span>
                        )}
                      </div>
                      <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-accent transition-colors flex-shrink-0" />
                    </div>
                  </motion.a>
                ))}
              </div>
            </motion.section>
          )}

          {/* Bottom CTA */}
          <motion.div
            className="text-center pt-8 border-t border-white/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            <p className="font-body text-xs uppercase tracking-widest text-white/40 mb-6">
              Love your new design?
            </p>
            <button className="btn-editorial">
              Save This Design
            </button>
            <p className="font-body text-[10px] text-white/30 mt-4">
              Create an account to save & revisit your visions
            </p>
          </motion.div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ProjectReveal;