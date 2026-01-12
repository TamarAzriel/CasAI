import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Trash2, ExternalLink, ShoppingBag, Heart } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import heroImage from "@/assets/hero-interior.jpg";

const API_BASE_URL = "http://127.0.0.1:5000";

interface Product {
  id: string | number;
  item_name: string;
  item_price: string;
  item_img: string;
  item_url: string;
  item_cat?: string;
  brand?: string;
}

interface SavedProject {
  id: string;
  image: string | null;
  recommendations: Product[];
  date: string;
  vision: string;
}

const SavedItems = () => {
  const [savedItems, setSavedItems] = useState<Product[]>([]);
  const [savedProjects, setSavedProjects] = useState<SavedProject[]>([]);
  const [activeTab, setActiveTab] = useState<"pieces" | "projects">("pieces");
  const navigate = useNavigate();

  useEffect(() => {
    try {
      // Load Wishlist Items
      const rawItems = window.localStorage.getItem("casai_wishlist");
      if (rawItems) {
        const parsed = JSON.parse(rawItems);
        if (Array.isArray(parsed)) {
          setSavedItems(parsed);
        }
      }

      // Load Saved Projects
      const rawProjects = window.localStorage.getItem("casai_projects");
      if (rawProjects) {
        const parsed = JSON.parse(rawProjects);
        if (Array.isArray(parsed)) {
          setSavedProjects(parsed);
        }
      }
    } catch (e) {
      console.error("Failed to load wishlist", e);
    }
  }, []);

  const removeItem = (itemUrl: string) => {
    const updated = savedItems.filter((item) => item.item_url !== itemUrl);
    setSavedItems(updated);
    window.localStorage.setItem("casai_wishlist", JSON.stringify(updated));
  };

  const removeProject = (projectId: string) => {
    const updated = savedProjects.filter((p) => p.id !== projectId);
    setSavedProjects(updated);
    window.localStorage.setItem("casai_projects", JSON.stringify(updated));
  };

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden bg-black">
      {/* Background */}
      <div
        className="fixed inset-0 bg-cover bg-center bg-no-repeat z-0 opacity-40"
        style={{ backgroundImage: `url(${heroImage})` }}
      />
      <div className="fixed inset-0 bg-black/60 z-0" />

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

      {/* Content */}
      <div className="relative z-10 p-6 md:p-12 lg:p-20 min-h-screen flex flex-col">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-12"
        >
          <button 
            onClick={() => navigate(-1)} 
            className="inline-flex items-center gap-2 text-white/60 hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="font-body text-[10px] uppercase tracking-[0.3em]">Back to Gallery</span>
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="max-w-7xl mx-auto w-full flex-1"
        >
          <header className="mb-16 border-b border-white/10 pb-12 flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="max-w-2xl">
              <h1 className="font-display text-5xl md:text-7xl text-white font-light tracking-tight mb-4">
                Curated <br />Collection.
              </h1>
              <p className="font-body text-white/40 text-sm tracking-wide leading-relaxed uppercase">
                A bespoke selection of pieces curated by your AI stylist. <br />
                Your personal aesthetic library, saved for your next project.
              </p>
            </div>
            <div className="flex flex-col items-end">
              <span className="font-display text-4xl text-white/20 font-light">
                {activeTab === "pieces" ? savedItems.length : savedProjects.length}
              </span>
              <span className="font-body text-[9px] uppercase tracking-[0.4em] text-white/30">
                {activeTab === "pieces" ? "Total Pieces" : "Total Projects"}
              </span>
            </div>
          </header>

          {/* Tabs */}
          <div className="flex gap-12 mb-12 border-b border-white/10">
            <button 
              onClick={() => setActiveTab("pieces")}
              className={`pb-4 font-body text-[11px] uppercase tracking-[0.4em] transition-all relative focus:outline-none ${activeTab === "pieces" ? "text-white" : "text-white/30 hover:text-white/60"}`}
            >
              Pieces
              {activeTab === "pieces" && (
                <motion.div 
                  layoutId="tab-active" 
                  className="absolute bottom-[-1px] left-0 right-0 h-px bg-accent shadow-[0_0_10px_rgba(212,175,55,0.5)]" 
                />
              )}
            </button>
            <button 
              onClick={() => setActiveTab("projects")}
              className={`pb-4 font-body text-[11px] uppercase tracking-[0.4em] transition-all relative focus:outline-none ${activeTab === "projects" ? "text-white" : "text-white/30 hover:text-white/60"}`}
            >
              Full Designs
              {activeTab === "projects" && (
                <motion.div 
                  layoutId="tab-active" 
                  className="absolute bottom-[-1px] left-0 right-0 h-px bg-accent shadow-[0_0_10px_rgba(212,175,55,0.5)]" 
                />
              )}
            </button>
          </div>

          {activeTab === "pieces" ? (
            savedItems.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-40 text-center">
                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-8 border border-white/10">
                  <Heart className="w-8 h-8 text-white/20" />
                </div>
                <h2 className="font-display text-2xl text-white mb-4">Your collection is empty.</h2>
                <p className="text-white/40 font-light max-w-sm mx-auto mb-8">Begin your journey by starting a new design project and saving pieces that resonate with your vision.</p>
                <Link to="/" className="px-8 py-3.5 bg-black/40 backdrop-blur-md text-white border border-white/20 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all shadow-xl inline-flex items-center justify-center">Start Project</Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-x-8 gap-y-16 pb-20">
                <AnimatePresence mode="popLayout">
                  {savedItems.map((item, index) => (
                    <motion.div
                      key={item.item_url}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ delay: index * 0.05 }}
                      className="group glass-crystal rounded-[2rem] p-4 hover:bg-white/10 transition-all duration-500 border border-white/10 flex flex-col h-full"
                    >
                      <div className="relative aspect-square overflow-hidden rounded-[1.5rem] mb-6 bg-white/5">
                        <img
                          src={`${API_BASE_URL}/${item.item_img}`}
                          alt={item.item_name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-all duration-700"
                        />
                        <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <a 
                            href={item.item_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center scale-90 group-hover:scale-100 transition-transform duration-300"
                          >
                            <ExternalLink className="w-5 h-5" />
                          </a>
                        </div>
                        <button
                          onClick={() => removeItem(item.item_url)}
                          className="absolute top-4 right-4 p-2 bg-black/40 text-white/60 hover:text-white hover:bg-black/60 rounded-full backdrop-blur-md transition-all z-20"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="space-y-3 px-2 flex-1 flex flex-col justify-between text-right rtl">
                        <div>
                          <p className="font-body text-[9px] uppercase tracking-[0.3em] text-accent font-medium mb-1">
                            {item.brand || "IKEA SELECTION"}
                          </p>
                          <h3 className="font-display text-lg text-white font-light line-clamp-2 leading-tight">
                            {item.item_name}
                          </h3>
                        </div>
                        <div className="flex justify-between items-center pt-4 border-t border-white/5 mt-auto">
                          <span className="font-body text-sm text-white/40 tracking-wider">
                            {item.item_price}
                          </span>
                          <div className="w-2 h-2 rounded-full bg-accent/40 group-hover:bg-accent transition-colors" />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )
          ) : (
            savedProjects.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-40 text-center">
                <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-8 border border-white/10">
                  <ShoppingBag className="w-8 h-8 text-white/20" />
                </div>
                <h2 className="font-display text-2xl text-white mb-4">No designs saved yet.</h2>
                <p className="text-white/40 font-light max-w-sm mx-auto mb-8">Full room visualizations created by AI will appear here once you save them.</p>
                <Link to="/" className="px-8 py-3.5 bg-black/40 backdrop-blur-md text-white border border-white/20 rounded-xl font-body text-[9px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all shadow-xl inline-flex items-center justify-center">Start Project</Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pb-20">
                <AnimatePresence mode="popLayout">
                  {savedProjects.map((project, index) => (
                    <motion.div
                      key={project.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ delay: index * 0.1 }}
                      className="group glass-crystal rounded-[2.5rem] overflow-hidden border border-white/10 flex flex-col"
                    >
                      <div className="relative aspect-[16/9] bg-black">
                        <img
                          src={`data:image/jpeg;base64,${project.image}`}
                          alt={project.vision}
                          className="w-full h-full object-cover group-hover:scale-105 transition-all duration-1000"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                        <div className="absolute bottom-6 left-8 text-left">
                          <p className="font-body text-[8px] uppercase tracking-[0.4em] text-accent mb-1">{project.date}</p>
                          <h3 className="font-display text-2xl text-white font-light">{project.vision}</h3>
                        </div>
                        <button
                          onClick={() => removeProject(project.id)}
                          className="absolute top-6 right-6 p-2.5 bg-black/40 text-white/40 hover:text-white hover:bg-black/60 rounded-full backdrop-blur-md transition-all z-20"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="p-8 flex items-center justify-between bg-white/[0.02]">
                        <div className="flex -space-x-3">
                          {project.recommendations.slice(0, 4).map((item, i) => (
                            <div key={i} className="w-10 h-10 rounded-full border border-black overflow-hidden bg-white/10">
                              <img src={`${API_BASE_URL}/${item.item_img}`} className="w-full h-full object-cover" />
                            </div>
                          ))}
                          {project.recommendations.length > 4 && (
                            <div className="w-10 h-10 rounded-full border border-black bg-white/5 flex items-center justify-center text-[10px] text-white/40 backdrop-blur-md">
                              +{project.recommendations.length - 4}
                            </div>
                          )}
                        </div>
                        <button className="text-[9px] uppercase tracking-[0.3em] text-white/40 hover:text-white transition-colors flex items-center gap-2 group/btn">
                          View Design
                          <ExternalLink className="w-3 h-3 group-hover/btn:translate-x-1 transition-transform" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )
          )}
        </motion.div>

        <footer className="mt-auto pt-12 border-t border-white/10 text-center pb-8">
          <p className="font-body text-[9px] uppercase tracking-[0.5em] text-white/20 italic">
            CasAI • The Future of Interior Consciousness
          </p>
        </footer>
      </div>
    </div>
  );
};

export default SavedItems;
