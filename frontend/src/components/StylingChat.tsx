import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Image as ImageIcon, X } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:5000";

interface Product {
  item_name: string;
  item_price: string;
  item_img: string;
  item_url: string;
}

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  has_image?: boolean;
  recommendations?: Product[];
}

interface StylingChatProps {
  isOpen: boolean;
  onClose: () => void;
}

const StylingChat = ({ isOpen, onClose }: StylingChatProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedImagePreview, setUploadedImagePreview] = useState<string | null>(null);
  const [serverImageFilename, setServerImageFilename] = useState<string | null>(null); // שומר את שם הקובץ בשרת
  const [isLoading, setIsLoading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setUploadedImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSend = async () => {
    if ((!input.trim() && !selectedFile) || isLoading) return;

    const newUserMsg: Message = {
      id: Date.now(),
      role: "user",
      content: input,
      has_image: !!selectedFile
    };
    
    const newMessages = [...messages, newUserMsg];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const formData = new FormData();
      // שולחים לשרת רק את הטקסט
      const apiMessages = newMessages.map(m => ({ role: m.role, content: m.content }));
      formData.append("messages", JSON.stringify(apiMessages));
      
      // טיפול בתמונה: אם חדשה, שולחים קובץ. אם קיימת, שולחים את שמה.
      if (selectedFile) {
        formData.append("image", selectedFile);
      } else if (serverImageFilename) {
        formData.append("image_filename", serverImageFilename);
      } else {
        // מקרה קצה: אין תמונה בכלל (לא אמור לקרות אם חוסמים כפתור)
      }

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Chat error");
      const data = await res.json();

      const aiMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: data.response,
        recommendations: data.recommendations
      };
      
      setMessages(prev => [...prev, aiMsg]);
      
      if (data.image_filename) {
        setServerImageFilename(data.image_filename);
        setSelectedFile(null); // מנקים את הבחירה המקומית כי זה כבר בשרת
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now(), role: "assistant", content: "Error connecting to server." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div 
            className="fixed inset-0 bg-black/40 z-40 backdrop-blur-md"
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div 
            className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 pointer-events-none"
            initial={{ opacity: 0, scale: 1.05, filter: "blur(20px)" }} 
            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }} 
            exit={{ opacity: 0, scale: 1.05, filter: "blur(20px)" }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            {/* Dynamic Architectural Lighting */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <motion.div 
                animate={{ 
                  scale: [1, 1.2, 1],
                  opacity: [0.3, 0.5, 0.3],
                  x: [0, 50, 0],
                  y: [0, -30, 0]
                }}
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute top-1/4 -left-1/4 w-[800px] h-[800px] bg-accent/10 rounded-full blur-[150px]"
              />
              <motion.div 
                animate={{ 
                  scale: [1.2, 1, 1.2],
                  opacity: [0.2, 0.4, 0.2],
                  x: [0, -50, 0],
                  y: [0, 30, 0]
                }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="absolute bottom-1/4 -right-1/4 w-[600px] h-[600px] bg-white/5 rounded-full blur-[120px]"
              />
            </div>

            <div className="glass-crystal w-full max-w-3xl h-[85vh] pointer-events-auto flex flex-col shadow-[0_50px_100px_rgba(0,0,0,0.4),0_0_80px_rgba(197,160,89,0.1)] overflow-hidden border border-white/10 rounded-[3rem] relative">
              {/* Internal Accent Line */}
              <div className="absolute inset-[1px] rounded-[3rem] border border-white/5 pointer-events-none" />
              
              {/* Header - Editorial Style */}
              <div className="p-12 md:p-14 flex justify-between items-start relative bg-white/[0.01]">
                <div className="space-y-6">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: 60 }}
                    transition={{ delay: 0.5, duration: 1 }}
                    className="h-px bg-accent/60" 
                  />
                  <div className="space-y-2">
                    <span className="font-body text-[10px] uppercase tracking-[0.8em] text-accent/80 font-medium block">Bespoke Dialogue</span>
                    <h2 className="font-display text-5xl font-light text-white tracking-tight">Stylist AI</h2>
                  </div>
                </div>
                <button 
                  onClick={onClose} 
                  className="p-5 hover:bg-white/5 rounded-full transition-all group -mt-4 border border-transparent hover:border-white/10"
                >
                  <X className="w-6 h-6 text-white/20 group-hover:text-white transition-colors" />
                </button>
              </div>

              {/* Chat Area - Focused & Clean */}
              <div className="flex-1 overflow-y-auto scrollbar-hide px-12 md:px-20 py-12 space-y-20">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center space-y-12 opacity-20">
                    <motion.div 
                      animate={{ y: [0, -10, 0] }}
                      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                      className="w-24 h-24 border border-white/10 rounded-full flex items-center justify-center"
                    >
                      <ImageIcon className="w-8 h-8 text-white" />
                    </motion.div>
                    <p className="font-body text-[12px] text-white font-light tracking-[0.7em] uppercase max-w-xs leading-[2.5]">
                      Describe your architectural vision to begin curation.
                    </p>
                  </div>
                )}
                
                {messages.map((msg) => (
                  <motion.div 
                    key={msg.id} 
                    initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    transition={{ duration: 0.8 }}
                    className="flex flex-col space-y-8"
                  >
                    {/* Message Header/Label */}
                    <div className={`flex items-center gap-8 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                      <span className="font-body text-[9px] uppercase tracking-[0.6em] text-white/30 font-semibold italic">
                        {msg.role === "user" ? "Inquiry" : "Designer Response"}
                      </span>
                      <div className="flex-1 h-px bg-white/[0.03]" />
                    </div>

                    <div className={`flex flex-col ${msg.role === "user" ? "items-end text-right" : "items-start text-right"} dir-rtl`}>
                      {msg.has_image && msg.role === "user" && (
                        <div className="mb-10 rounded-[2.5rem] overflow-hidden border border-white/10 shadow-2xl max-w-[85%] bg-black">
                          <img src={uploadedImagePreview!} alt="Space" className="w-full object-cover max-h-[500px] opacity-90" />
                        </div>
                      )}
                      
                      <div 
                        dir="rtl"
                        className={`max-w-[95%] text-[13px] font-light leading-relaxed tracking-wide font-body text-white/80 whitespace-pre-wrap ${msg.role === "assistant" ? "pr-8 border-r-2 border-accent/40" : "pr-8 border-r border-white/10"}`}
                      >
                        {msg.content}
                      </div>

                      {/* Product Recommendations within Chat */}
                      {msg.role === "assistant" && msg.recommendations && msg.recommendations.length > 0 && (
                        <div className="mt-10 flex gap-6 overflow-x-auto pb-8 editorial-scrollbar w-full -mr-16 pr-16">
                          {msg.recommendations.map((product, pIdx) => (
                            <motion.a
                              key={pIdx}
                              href={product.item_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              initial={{ opacity: 0, x: 20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: 0.2 + (pIdx * 0.1), duration: 0.6 }}
                              className="min-w-[200px] max-w-[200px] group/card bg-white/[0.02] border border-white/5 p-4 rounded-2xl hover:bg-white/[0.05] transition-all hover:border-accent/20"
                            >
                              <div className="aspect-[4/5] rounded-xl overflow-hidden mb-4 bg-black shadow-lg">
                                <img 
                                  src={`${API_BASE_URL}${product.item_img}`} 
                                  alt={product.item_name}
                                  className="w-full h-full object-cover group-hover/card:scale-110 transition-transform duration-1000 ease-out"
                                />
                              </div>
                              <p className="text-[10px] text-white/60 font-medium line-clamp-2 mb-2 h-7 leading-tight tracking-wide uppercase font-body">{product.item_name}</p>
                              <div className="flex justify-between items-center">
                                <span className="text-[9px] text-accent font-body tracking-[0.3em] font-semibold">{product.item_price}</span>
                                <div className="w-8 h-px bg-accent/20 group-hover/card:w-12 transition-all duration-500" />
                              </div>
                            </motion.a>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
                
                {isLoading && (
                  <div className="flex items-center gap-8 px-6">
                    <motion.div 
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="w-5 h-5 border-2 border-accent/10 border-t-accent rounded-full" 
                    />
                    <span className="text-[10px] uppercase tracking-[0.7em] text-accent/60 font-medium animate-pulse">Curating Architectural Excellence...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area - High-End Architectural Bar */}
              <div className="px-12 md:px-16 pb-16 pt-8 bg-gradient-to-t from-black/40 to-transparent relative">
                 <AnimatePresence>
                   {selectedFile && (
                     <motion.div 
                       className="mb-10 flex items-center gap-10 bg-white/[0.03] p-6 border border-white/10 rounded-3xl backdrop-blur-xl"
                       initial={{ opacity: 0, y: 30, scale: 0.95 }}
                       animate={{ opacity: 1, y: 0, scale: 1 }}
                       exit={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
                     >
                        <div className="relative group">
                          <img src={uploadedImagePreview!} className="w-20 h-20 rounded-2xl object-cover shadow-2xl border border-white/10 group-hover:scale-105 transition-transform duration-500" />
                          <div className="absolute inset-0 bg-accent/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="flex-1">
                          <p className="text-[10px] uppercase tracking-[0.5em] text-accent font-bold">Visual Curation Context</p>
                          <p className="text-[11px] text-white/40 truncate mt-2 font-light italic">{selectedFile.name}</p>
                        </div>
                        <button onClick={() => { setSelectedFile(null); setUploadedImagePreview(null); }} className="p-4 text-white/20 hover:text-white transition-all hover:bg-white/5 rounded-full">
                          <X className="w-5 h-5" />
                        </button>
                     </motion.div>
                   )}
                 </AnimatePresence>

                 <motion.div 
                    layout
                    className="flex items-center gap-10 group bg-white/[0.03] p-5 rounded-[2rem] border border-white/10 hover:border-accent/30 transition-all duration-700 shadow-2xl"
                  >
                   <div className="flex-1 pl-4">
                     <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                handleSend();
                            }
                        }}
                        placeholder="Share your architectural vision..."
                        className="w-full bg-transparent text-white placeholder:text-white/10 focus:outline-none font-light text-[14px] font-body caret-accent"
                     />
                   </div>
                   
                   <div className="flex items-center gap-6 border-l border-white/10 pl-8">
                     <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />
                     <button 
                       onClick={() => fileInputRef.current?.click()}
                       className="text-white/20 hover:text-accent transition-all p-3 hover:scale-110 active:scale-90"
                     >
                       <ImageIcon className="w-6 h-6" />
                     </button>
                     <button 
                       onClick={handleSend}
                       disabled={isLoading || (!input && !selectedFile)}
                       className="px-12 py-4 bg-white/[0.03] hover:bg-accent text-white hover:text-black border border-white/10 hover:border-accent rounded-2xl font-body text-[11px] uppercase tracking-[0.6em] font-bold transition-all duration-500 disabled:opacity-5 active:scale-95 whitespace-nowrap shadow-xl"
                     >
                       Transmit
                     </button>
                   </div>
                 </motion.div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default StylingChat;