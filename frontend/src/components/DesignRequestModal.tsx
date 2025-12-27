import { useState, useRef, ChangeEvent } from "react";
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
    const [isLoading, setIsLoading] = useState(false);
    
    // הסרנו את ה-Mode, עכשיו זה תמיד חיפוש
    const [detectedItems, setDetectedItems] = useState<DetectionItem[]>([]);
    const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);
    const [originalImagePath, setOriginalImagePath] = useState<string | null>(null); 

    const fileInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast(); 

    // --- זיהוי פריטים (ללא שינוי) ---
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
            
            // נתיב לקובץ ששמור בצד השרת (appdata/uploads/filename.jpg)
            const path = `appdata/uploads/${file.name}`;
            setOriginalImagePath(path); 

            if (items.length > 0) {
                setSelectedItemIndex(0);
                // הודעת הטוסט הועלתה כי הייתה גדולה ומפריעה ויזואלית
            } else {
                toast({ title: "No Items", description: "No furniture detected.", variant: "destructive" });
            }
            
        } catch (err) {
            console.error("Detection failed", err);
            toast({ title: "Error", description: "Detection failed.", variant: "destructive" });
        } finally {
            setIsLoading(false);
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
        
        setIsLoading(true);
        const selectedItem = selectedItemIndex !== null ? detectedItems[selectedItemIndex] : null;

        try {
            // תמיד מבצעים חיפוש (recommend/image)
            const formData = new FormData();
            
            if (selectedItem) {
                formData.append("crop_url", selectedItem.crop_url);
            } else {
                formData.append("image", selectedFile); 
            }
            
            formData.append("text", vision);

            const res = await fetch(`${API_BASE_URL}/recommend`, { method: "POST", body: formData });
            if (!res.ok) throw new Error("Search failed");

            const data: RecommendationItem[] = await res.json();

            // בקשת קישורים מגוגל (Shopping) 
            // נבנה שאילתא: קודם מהטקסט של המשתמש, ואם ריק - מהמחלקה של הפריט שזוהה
            let externalLinks: any[] = [];
            let googleQuery = vision.trim();
            if (!googleQuery && selectedItem) {
                googleQuery = selectedItem.class;
            }

            if (googleQuery) {
                try {
                    const googleRes = await fetch(`${API_BASE_URL}/google_search`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ query: googleQuery })
                    });
                    if (googleRes.ok) {
                        externalLinks = await googleRes.json();
                    }
                } catch (googleErr) {
                    console.error("Google search failed", googleErr);
                }
            }
            
            // מעבירים את התוצאות + המידע שנצטרך למסך הבא (כולל קישורי גוגל)
            if (onResults) {
                onResults(data, {
                    originalImagePath: originalImagePath,
                    selectedCropUrl: selectedItem?.crop_url || null,
                    vision: vision,
                    externalLinks,
                });
            }
            onClose();
            
        } catch (error) {
            console.error(error);
            toast({ title: "Error", description: "Something went wrong.", variant: "destructive" });
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
                                
                                {/* Title Only (No Tabs) */}
                                <div className="flex justify-between items-end mb-8">
                                    <h2 className="font-display text-3xl font-light text-white">New Vision</h2>
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
                                                    className="w-full h-full object-contain"
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

                                {/* Detected Items */}
                                {detectedItems.length > 0 && (
                                    <div className="mb-6">
                                        <p className="text-white/40 text-[10px] uppercase tracking-widest mb-2">
                                            Select Item to Search:
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
                                <div className="mb-8 mt-4">
                                    <textarea
                                        value={vision}
                                        onChange={(e) => setVision(e.target.value)}
                                        placeholder="Describe item style or name (optional)..."
                                        rows={3}
                                        className="input-editorial w-full resize-none font-body text-sm py-1"
                                    />
                                </div>

                                {/* Submit Button */}
                                <button
                                    onClick={handleAction}
                                    disabled={isLoading}
                                    className="btn-editorial w-full bg-charcoal text-bone hover:bg-charcoal/90 disabled:opacity-50"
                                >
                                    {isLoading ? "Processing..." : "Search Items"}
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