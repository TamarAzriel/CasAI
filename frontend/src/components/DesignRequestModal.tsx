import { useState, useRef, ChangeEvent, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, X, Search, Check } from "lucide-react";

// ייבוא קריטי: מניחים שיצרת את types.ts בנתיב זה
import { 
    DetectionItem, 
    RecommendationItem, 
    DesignRequestModalProps 
} from "@/lib/types"; 

// ייבוא utility hooks
import { cn } from "@/lib/utils"; 
import { useToast } from "@/hooks/use-toast"; 

const API_BASE_URL = "http://127.0.0.1:5000";

// הרחבת הפרופס כדי לתמוך בהעברת הקונטקסט למסך הבא
interface ExtendedModalProps extends Omit<DesignRequestModalProps, 'onResults'> {
    onResults: (data: RecommendationItem[], context: { 
        originalImagePath: string | null;
        selectedCropUrl: string | null;
        vision: string;
        externalLinks?: any[];
    }) => void;
}

const DesignRequestModal = ({ isOpen, onClose, onResults }: ExtendedModalProps) => {
    const [uploadedImage, setUploadedImage] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null); 
    const [vision, setVision] = useState("");
    const [isSearching, setIsSearching] = useState(false);
    const [isDetecting, setIsDetecting] = useState(false);
    
    // הסרנו את ה-Mode, עכשיו זה תמיד חיפוש
    const [detectedItems, setDetectedItems] = useState<DetectionItem[]>([]);
    const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);
    const [originalImagePath, setOriginalImagePath] = useState<string | null>(null); 

    useEffect(() => {
        if (!isOpen) {
            setUploadedImage(null);
            setSelectedFile(null);
            setVision("");
            setDetectedItems([]);
            setSelectedItemIndex(null);
            setOriginalImagePath(null);
            setIsSearching(false);
            setIsDetecting(false);
        }
    }, [isOpen]);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast(); 

    // --- זיהוי פריטים (ללא שינוי) ---
    const detectItems = async (file: File) => {
        setIsDetecting(true);
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
            
            // נתיב לקובץ ששמור בצד השרת (appdata/uploads/filename.jpg)
            const path = `appdata/uploads/${file.name}`;
            setOriginalImagePath(path); 

            if (items.length > 0) {
                setSelectedItemIndex(0);
            } else {
                toast({ title: "No Items", description: "No furniture detected.", variant: "default" });
            }
            
        } catch (err) {
            console.error("Detection failed", err);
            toast({ title: "Error", description: "Detection failed.", variant: "destructive" });
        } finally {
            setIsDetecting(false);
        }
    };

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            const reader = new FileReader();
            reader.onloadend = () => setUploadedImage(reader.result as string);
            reader.readAsDataURL(file);
            detectItems(file);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    // --- הלוגיקה (רק חיפוש) ---
    const handleAction = async (e?: React.MouseEvent) => {
        if (e) e.preventDefault(); 

        if (!selectedFile) {
            toast({ title: "Error", description: "Please upload an image.", variant: "destructive" });
            return;
        }
        
        setIsSearching(true);
        const selectedItem = selectedItemIndex !== null ? detectedItems[selectedItemIndex] : null;

        try {
            // הכנת שאילתת גוגל מראש
            let googleQuery = vision.trim();
            if (!googleQuery && selectedItem) {
                googleQuery = selectedItem.class;
            }

            // יצירת שני תהליכים במקביל
            const recommendPromise = (async () => {
                const formData = new FormData();
                if (selectedItem) {
                    formData.append("crop_url", selectedItem.crop_url);
                } else {
                    formData.append("image", selectedFile); 
                }
                formData.append("text", vision);
                
                const res = await fetch(`${API_BASE_URL}/recommend`, { method: "POST", body: formData });
                if (!res.ok) throw new Error("Search failed");
                return res.json();
            })();

            const googleSearchPromise = (async () => {
                if (!googleQuery) return [];
                try {
                    const googleRes = await fetch(`${API_BASE_URL}/google_search`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ query: googleQuery })
                    });
                    if (googleRes.ok) return await googleRes.json();
                } catch (err) {
                    console.error("Google search failed", err);
                }
                return [];
            })();

            // המתנה לשניהם במקביל (זה חוסך המון זמן!)
            const results = await Promise.allSettled([
                recommendPromise,
                googleSearchPromise
            ]);

            const recommendations = results[0].status === 'fulfilled' ? results[0].value : [];
            const externalLinks = results[1].status === 'fulfilled' ? results[1].value : [];

            // מעבירים את התוצאות למסך הבא
            if (onResults && Array.isArray(recommendations)) {
                onResults(recommendations, {
                    originalImagePath: originalImagePath,
                    selectedCropUrl: selectedItem?.crop_url || null,
                    vision: vision,
                    externalLinks: Array.isArray(externalLinks) ? externalLinks : [],
                });
            } else {
                toast({ title: "No results", description: "Could not find any recommendations.", variant: "destructive" });
            }
            onClose();
            
        } catch (error) {
            console.error(error);
            toast({ title: "Error", description: "Something went wrong.", variant: "destructive" });
        } finally {
            setIsSearching(false);
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
                            className="glass-crystal w-full max-w-md pointer-events-auto rounded-[2.5rem] overflow-hidden shadow-[0_0_50px_rgba(197,160,89,0.1)] border border-white/10"
                            initial={{ opacity: 0, y: 60, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 40, scale: 0.95 }}
                            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                        >
                            {/* Close Button */}
                            <button
                                onClick={onClose}
                                className="absolute top-6 right-6 text-white/40 hover:text-white transition-colors z-10"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div className="p-10 md:p-12 relative">
                                {/* Subtle Light Leak */}
                                <div className="absolute -top-24 -left-24 w-64 h-64 bg-accent/10 rounded-full blur-[100px] pointer-events-none" />
                                
                                {/* Title Only (No Tabs) */}
                                <div className="mb-12 text-center">
                                    <span className="font-body text-[9px] uppercase tracking-[0.5em] text-accent mb-2 block">Curation Hub</span>
                                    <h2 className="font-display text-4xl font-light text-white tracking-tight">New Vision</h2>
                                </div>

                                {/* Upload Zone */}
                                <div className="mb-8">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileChange}
                                        accept="image/*"
                                        className="hidden"
                                    />
                                    
                                    <div
                                        onClick={handleUploadClick}
                                        className="upload-zone aspect-[4/3] w-full rounded-[2rem] border-white/10 bg-white/[0.02] hover:bg-white/[0.05] transition-all group/upload"
                                    >
                                        {uploadedImage ? (
                                            <div className="relative w-full h-full group/image rounded-[2rem] overflow-hidden">
                                                <img
                                                    src={uploadedImage}
                                                    alt="Uploaded room"
                                                    className="w-full h-full object-contain"
                                                />
                                                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                                                    <span className="font-body text-[9px] uppercase tracking-[0.3em] text-white bg-black/40 px-5 py-2.5 rounded-xl border border-white/20 backdrop-blur-md shadow-xl">
                                                        Change Photo
                                                    </span>
                                                </div>
                                                {/* Delete Button */}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setUploadedImage(null);
                                                        setSelectedFile(null);
                                                        setDetectedItems([]);
                                                        setSelectedItemIndex(null);
                                                    }}
                                                    className="absolute top-4 right-4 p-2 bg-black/60 hover:bg-black text-white rounded-full backdrop-blur-md opacity-0 group-hover/image:opacity-100 transition-opacity z-10"
                                                >
                                                    <X className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center py-12 relative">
                                                <div className="absolute inset-0 bg-accent/5 rounded-full blur-3xl opacity-0 group-hover/upload:opacity-100 transition-opacity duration-1000" />
                                                <div className="w-14 h-14 border border-accent/30 rounded-full flex items-center justify-center mb-6 group-hover/upload:border-accent group-hover/upload:scale-110 transition-all duration-700 bg-white/[0.02] shadow-[0_0_20px_rgba(197,160,89,0.1)]">
                                                    <Plus className="w-6 h-6 text-accent" />
                                                </div>
                                                <span className="font-body text-[10px] uppercase tracking-[0.3em] text-white/30 group-hover:text-white/60 transition-colors">
                                                    Tap to upload room photo
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Detected Items */}
                                {isDetecting && (
                                    <div className="mb-8 flex flex-col items-center justify-center py-4 bg-white/[0.02] rounded-2xl border border-white/5 animate-pulse">
                                        <div className="w-5 h-5 border-2 border-accent/20 border-t-accent rounded-full animate-spin mb-3" />
                                        <p className="text-white/30 text-[8px] uppercase tracking-[0.4em]">Analyzing Space...</p>
                                    </div>
                                )}

                                {!isDetecting && detectedItems.length > 0 && (
                                    <div className="mb-10">
                                        <p className="text-white/30 text-[9px] uppercase tracking-[0.3em] mb-5 text-center">
                                            Select element to redesign
                                        </p>
                                        <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide justify-center">
                                            {detectedItems.map((item, idx) => (
                                                <div 
                                                    key={idx}
                                                    onClick={() => setSelectedItemIndex(idx)}
                                                    className={cn(
                                                        "relative w-20 h-20 rounded-2xl border cursor-pointer overflow-hidden flex-shrink-0 transition-all duration-500 group/item",
                                                        selectedItemIndex === idx 
                                                            ? "border-accent ring-4 ring-accent/10 scale-110 shadow-[0_0_30px_rgba(197,160,89,0.2)]" 
                                                            : "border-white/5 opacity-40 hover:opacity-100 hover:border-white/20"
                                                    )}
                                                >
                                                    <img 
                                                        src={`${API_BASE_URL}${item.crop_url.replace(/\\/g, '/')}`} 
                                                        className="w-full h-full object-cover" 
                                                    />
                                                    
                                                    <div className={cn(
                                                        "absolute inset-x-0 bottom-0 bg-black/60 backdrop-blur-sm py-1 px-2 transition-transform duration-300",
                                                        selectedItemIndex === idx ? "translate-y-0" : "translate-y-full group-hover/item:translate-y-0"
                                                    )}>
                                                        <p className="text-[7px] text-white/90 uppercase tracking-wider truncate text-center font-medium">
                                                            {item.class.replace('_', ' ')}
                                                        </p>
                                                    </div>

                                                    {selectedItemIndex === idx && (
                                                        <div className="absolute top-1 right-1 bg-accent rounded-full p-0.5 shadow-lg">
                                                            <Check className="w-2.5 h-2.5 text-white" />
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Vision Input */}
                                <div className="mb-10 mt-2">
                                    <label className="block text-[9px] uppercase tracking-[0.3em] text-white/30 mb-2 ml-1">Refine with Keywords</label>
                                    <input
                                        type="text"
                                        value={vision}
                                        onChange={(e) => setVision(e.target.value)}
                                        placeholder="Minimalist, velvet, oak wood..."
                                        className="w-full bg-transparent border-b border-white/10 py-3 text-white placeholder:text-white/20 focus:outline-none focus:border-accent/50 transition-colors font-body text-sm"
                                    />
                                </div>

                                {/* Submit Button */}
                                <div className="mt-2">
                                    <button
                                        onClick={handleAction}
                                        disabled={isSearching || isDetecting || !selectedFile}
                                        className="w-full px-8 py-4 bg-black/40 backdrop-blur-md text-white border border-white/20 rounded-2xl font-body text-[10px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all shadow-xl disabled:opacity-20 disabled:cursor-not-allowed"
                                    >
                                        {isSearching ? (
                                            <span className="flex items-center justify-center gap-2">
                                                <div className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                                Curating Results
                                            </span>
                                        ) : (
                                            "Search Items"
                                        )}
                                    </button>
                                    {!selectedFile && (
                                        <p className="text-[8px] text-white/20 text-center mt-4 uppercase tracking-widest">Upload a photo to begin curation</p>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default DesignRequestModal;