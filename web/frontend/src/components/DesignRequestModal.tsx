import { useState, useRef, ChangeEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, Search, Sparkles, Check } from "lucide-react";

// ייבוא קריטי: מניחים שיצרת את types.ts בנתיב זה
import { 
    DetectionItem, 
    RecommendationItem, 
    DesignRequestModalProps 
} from "@/lib/types"; 

// ייבוא utility hooks
import { cn } from "@/lib/utils"; // ודא שאתה מייבא את cn
import { useToast } from "@/hooks/use-toast"; // ודא שאתה מייבא את useToast


// הגדרת כתובת השרת
const API_BASE_URL = "http://127.0.0.1:5000";

// הקומפוננטה כעת משתמשת ב-Props המיובאים
const DesignRequestModal = ({ isOpen, onClose, onResults, onImageGenerated }: DesignRequestModalProps) => {
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null); // קובץ התמונה האמיתי
    const [vision, setVision] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    
    const [mode, setMode] = useState<'search' | 'redesign'>('search');
    const [detectedItems, setDetectedItems] = useState<DetectionItem[]>([]);
    const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);
    // State קריטי לשמירת נתיב התמונה המקורית בשרת (לצורך Redesign)
    const [originalImagePath, setOriginalImagePath] = useState<string | null>(null); 

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast(); 

    // --- פונקציות עזר ל-Backend ---

    const detectItems = async (file: File) => {
        setIsLoading(true);
        setDetectedItems([]);
        setSelectedItemIndex(null);
        setOriginalImagePath(null); 
        
        const formData = new FormData();
        formData.append("image", file);
        
        try {
            const res = await fetch(`${API_BASE_URL}/detect`, { method: "POST", body: formData });
            if (!res.ok) throw new Error("Detection failed");
            
            const items: DetectionItem[] = await res.json();
            setDetectedItems(items);
            
            // --- שמירת נתיב התמונה המקורית ---
            // הבקאנד שומר את התמונה המלאה ב-'uploads/filename'.
            const path = `uploads/${file.name}`;
            setOriginalImagePath(path); 
            console.log("Original Image Path Saved:", path);

            if (items.length > 0) {
                setSelectedItemIndex(0);
                toast({ title: "Items Detected", description: `Found ${items.length} items. Select one to proceed.` });
            } else {
                toast({ title: "No Items", description: "No furniture detected. Try a different photo.", variant: "destructive" });
            }
            
        } catch (err) {
            console.error("Detection failed", err);
            toast({ title: "Error", description: "Detection failed or server is unreachable.", variant: "destructive" });
        } finally {
            setIsLoading(false);
        }
    };


    // --- שינוי קובץ ---

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setUploadedImage(reader.result as string);
            reader.readAsDataURL(file);

            // 1. שמירת קובץ
            // 2. זיהוי אוטומטי של רהיטים
            detectItems(file);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };


    // --- הלוגיקה הראשית ל-Generate / Search ---

    const handleAction = async (e?: React.MouseEvent) => {
        if (e) e.preventDefault(); 

        if (!selectedFile) {
            toast({ title: "Error", description: "Please upload an image.", variant: "destructive" });
            return;
        }
        
        setIsLoading(true);
        const selectedItem = selectedItemIndex !== null ? detectedItems[selectedItemIndex] : null;

        try {
            if (mode === 'redesign') {
                // --- 1. עיצוב מחדש (/generate_design) ---
                if (!selectedItem || !originalImagePath) {
                     toast({ title: "Error", description: "Detection results are missing for redesign.", variant: "destructive" });
                     return;
                }
                if (!vision.trim()) {
                     toast({ title: "Error", description: "Please describe the desired redesign style.", variant: "destructive" });
                     return;
                }
                
                const formData = new FormData();
                formData.append("original_image_path", originalImagePath);
                formData.append("selected_crop_url", selectedItem.crop_url);
                formData.append("prompt", vision);
                
                const res = await fetch(`${API_BASE_URL}/generate_design`, { method: "POST", body: formData });
                if (!res.ok) throw new Error("Redesign failed");
                
                const data: { generated_image: string } = await res.json();
                if (data.generated_image && onImageGenerated) {
                    onImageGenerated(data.generated_image); // Base64
                    onClose();
                }
                
            } else {
                // --- 2. חיפוש חכם (/recommend/image) ---
                const formData = new FormData();
                
                if (selectedItem) {
                    // א. חיפוש פריט ספציפי (שולחים את ה-URL של הקרופ)
                    formData.append("crop_url", selectedItem.crop_url);
                } else if (selectedFile) {
                    // ב. פולבק: אם אין זיהוי, שולחים את התמונה המלאה ל-Backend
                    formData.append("image", selectedFile); 
                } else {
                    throw new Error("Missing image input.");
                }
                
                formData.append("text", vision);

                const res = await fetch(`${API_BASE_URL}/recommend/image`, { method: "POST", body: formData });
                if (!res.ok) throw new Error("Search failed");

                const data: RecommendationItem[] = await res.json();
                if (onResults) onResults(data);
                onClose();
            }
        } catch (error) {
            console.error(error);
            toast({ title: "Error", description: "Something went wrong or server is unreachable.", variant: "destructive" });
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="fixed inset-0 z-40 bg-black/60"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        onClick={onClose}
                    />

                    {/* Glass Modal */}
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 pointer-events-none"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <motion.div
                            className="glass-crystal w-full max-w-md pointer-events-auto"
                            initial={{ opacity: 0, y: 60, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 40, scale: 0.95 }}
                            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                        >
                            {/* Close Button */}
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div className="p-8 md:p-10">
                                
                                {/* Title and Mode Selector */}
                                <div className="flex justify-between items-end mb-8">
                                    <h2 className="font-display text-3xl font-light text-white">New Vision</h2>
                                    <div className="flex gap-4 text-[10px] tracking-widest uppercase mb-1">
                                        <button onClick={() => setMode('search')} className={cn("pb-1 border-b transition-colors", mode === 'search' ? "text-white border-white" : "text-white/40 border-transparent")}>
                                            <Search className="inline w-3 h-3 mr-1 mb-0.5" /> Find
                                        </button>
                                        <button onClick={() => setMode('redesign')} className={cn("pb-1 border-b transition-colors", mode === 'redesign' ? "text-white border-white" : "text-white/40 border-transparent")}>
                                            <Sparkles className="inline w-3 h-3 mr-1 mb-0.5" /> Redesign
                                        </button>
                                    </div>
                                </div>

                                {/* Upload Zone */}
                                <div className="mb-6">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileChange}
                                        accept="image/*"
                                        className="hidden"
                                    />
                                    
                                    <div
                                        onClick={handleUploadClick}
                                        className="upload-zone aspect-[4/3] w-full"
                                    >
                                        {uploadedImage ? (
                                            <div className="relative w-full h-full">
                                                <img
                                                    src={uploadedImage}
                                                    alt="Uploaded room"
                                                    className="w-full h-full object-cover"
                                                />
                                                <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                    <span className="font-body text-xs uppercase tracking-widest text-white">
                                                        Change Photo
                                                    </span>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center py-12">
                                                <div className="w-10 h-10 border border-white/30 flex items-center justify-center mb-4">
                                                    <Plus className="w-5 h-5 text-white/60" />
                                                </div>
                                                <span className="font-body text-xs uppercase tracking-widest text-white/60">
                                                    Tap to upload room photo
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* אזור הבחירה החכם */}
                                {detectedItems.length > 0 && (
                                    <div className="mb-6">
                                        <p className="text-white/40 text-[10px] uppercase tracking-widest mb-2">
                                            {mode === 'search' ? "Select Item to Search:" : "Select Item to Redesign:"}
                                        </p>
                                        <div className="flex gap-2 overflow-x-auto pb-2">
                                            {detectedItems.map((item, idx) => (
                                                <div 
                                                    key={idx}
                                                    onClick={() => setSelectedItemIndex(idx)}
                                                    className={cn(
                                                        "relative w-14 h-14 rounded border cursor-pointer overflow-hidden flex-shrink-0 transition-all",
                                                        selectedItemIndex === idx ? "border-white opacity-100 ring-1 ring-white" : "border-white/20 opacity-50 hover:opacity-80"
                                                    )}
                                                >
                                                    {/*
                                                    * התיקון הקריטי: חיבור API_BASE_URL והחלפת לוכסנים
                                                    */}
                                                    <img 
                                                        src={`${API_BASE_URL}${item.crop_url.replace(/\\/g, '/')}`} 
                                                        className="w-full h-full object-cover" 
                                                    />
                                                    
                                                    {selectedItemIndex === idx && (
                                                        <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                                                            <Check className="w-4 h-4 text-white" />
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}


                                {/* Vision Input */}
                                <div className="mb-8">
                                    <textarea
                                        value={vision}
                                        onChange={(e) => setVision(e.target.value)}
                                        placeholder={mode === 'search' ? "Describe item style or name..." : "Describe the desired new style..."}
                                        rows={3}
                                        className="input-editorial w-full resize-none font-body text-sm"
                                    />
                                </div>

                                {/* Submit Button */}
                                <button
                                    onClick={handleAction}
                                    disabled={isLoading}
                                    className="btn-editorial w-full bg-charcoal text-bone hover:bg-charcoal/90 disabled:opacity-50"
                                >
                                    {isLoading ? "Processing..." : mode === 'search' ? "Search Items" : "Generate Redesign"}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default DesignRequestModal;