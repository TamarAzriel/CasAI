import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Image as ImageIcon, X } from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:5000";

interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  has_image?: boolean;
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
        content: data.response
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
            className="fixed inset-0 bg-black/50 z-40 backdrop-blur-lg"
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div 
            className="fixed inset-0 z-50 flex items-center justify-center p-6"
            initial={{ opacity: 0, scale: 0.9 }} 
            animate={{ opacity: 1, scale: 1 }} 
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: "spring", damping: 20, stiffness: 150 }}
          >
            <div className="w-full max-w-2xl max-h-[75vh] bg-white/10 backdrop-blur-2xl border border-white/15 rounded-3xl flex flex-col shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="p-8 border-b border-white/10 flex justify-between items-start">
                <h2 className="text-white font-light text-3xl tracking-widest">AI Chat Stylist</h2>
                <button onClick={onClose} className="text-white/40 hover:text-white/60 transition">
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Chat Area */}
              <div className="flex-1 p-8 space-y-6 overflow-hidden flex flex-col">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center flex-1">
                    {/* Welcome Message */}
                    <div className="text-center max-w-md">
                      <ImageIcon className="w-16 h-16 text-white/40 mb-6 mx-auto" />
                      <h3 className="text-white font-light text-xl tracking-widest mb-4">UPLOAD A ROOM PHOTO</h3>
                      <p className="text-white/50 font-light text-sm leading-relaxed">Upload a photo of your room, and I'll analyze the space and provide personalized styling tips and furniture recommendations tailored to your aesthetic.</p>
                    </div>
                  </div>
                )}
                
                {messages.length > 0 && (
                  <div className="flex-1 overflow-y-auto space-y-6 pb-4">
                    {messages.map((msg) => (
                      <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse justify-end" : ""}`}>
                        {/* Avatar */}
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.role === "user" 
                            ? "bg-white/20" 
                            : "bg-white/10"
                        }`}>
                          <span className="text-xs text-white/60">{msg.role === "user" ? "U" : "AI"}</span>
                        </div>
                        
                        {/* Message Container */}
                        <div className={`max-w-[65%] space-y-3 ${msg.role === "user" ? "items-end flex flex-col" : ""}`}>
                           {/* Image Preview */}
                           {msg.has_image && msg.role === "user" && (
                              <motion.div 
                                className="rounded-xl overflow-hidden border border-white/20 shadow-lg"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                              >
                                  <img src={uploadedImagePreview!} alt="Room" className="w-full h-auto max-h-48 object-cover" />
                              </motion.div>
                           )}
                           
                           {/* Message Bubble */}
                           {msg.content && (
                             <motion.div 
                               className={`px-5 py-4 rounded-xl text-sm leading-relaxed whitespace-pre-wrap font-light ${
                                 msg.role === "user" 
                                   ? "bg-white/15 text-white" 
                                   : "bg-white/8 text-white/80"
                               }`}
                               initial={{ opacity: 0, y: 10 }}
                               animate={{ opacity: 1, y: 0 }}
                               transition={{ delay: 0.1 }}
                             >
                               {msg.content}
                             </motion.div>
                           )}
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex gap-4">
                         <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                           <span className="text-xs text-white/40">…</span>
                         </div>
                         <div className="bg-white/8 px-4 py-3 rounded-lg">
                           <div className="flex gap-1 h-2 items-center">
                             <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}/>
                             <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}/>
                             <span className="w-1.5 h-1.5 bg-white/30 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}/>
                           </div>
                         </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div className="p-8 border-t border-white/10 space-y-5">
                 {selectedFile && (
                   <motion.div 
                     className="flex items-center gap-3 bg-white/5 p-4 rounded-lg w-fit border border-white/10 pr-4"
                     initial={{ opacity: 0, y: 10 }}
                     animate={{ opacity: 1, y: 0 }}
                   >
                      <img src={uploadedImagePreview!} className="w-12 h-12 rounded object-cover" />
                      <div className="flex-1">
                        <p className="text-xs text-white/70 font-light">Photo attached</p>
                        <p className="text-xs text-white/40">Ready to analyze</p>
                      </div>
                      <button onClick={() => { setSelectedFile(null); setUploadedImagePreview(null); }} className="hover:bg-white/10 rounded p-1 transition">
                        <X className="w-3 h-3 text-white/40" />
                      </button>
                   </motion.div>
                 )}

                 <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSend();
                        }
                    }}
                    placeholder={messages.length === 0 ? "Describe your style preferences..." : "Ask a follow-up question..."}
                    rows={2}
                    className="w-full bg-transparent text-white placeholder-white/30 focus:outline-none resize-none font-light text-sm border-b border-white/10 pb-3"
                 />

                 <div className="flex gap-3 items-center pt-2">
                   <input 
                     type="file" 
                     ref={fileInputRef}
                     onChange={handleFileChange}
                     accept="image/*"
                     className="hidden"
                   />
                   <button 
                     onClick={() => fileInputRef.current?.click()}
                     className="text-white/40 hover:text-white/60 transition"
                     title="Upload Image"
                   >
                     <ImageIcon className="w-5 h-5" />
                   </button>
                   <div className="flex-1"></div>
                   <button 
                     onClick={handleSend}
                     disabled={isLoading || (!input && !selectedFile) || (!selectedFile && !serverImageFilename)}
                     className="flex items-center gap-2 px-8 py-2 bg-black/40 text-white/70 rounded-lg hover:bg-black/60 hover:text-white disabled:opacity-20 disabled:cursor-not-allowed transition font-light text-sm tracking-widest uppercase border border-white/10"
                   >
                     <Send className="w-4 h-4" />
                     Send
                   </button>
                 </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default StylingChat;