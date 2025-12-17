// web/frontend/src/lib/types.ts

// --- 1. Interface עבור אובייקט זיהוי (Detection Item) ---
// מבנה נתון שמגיע מ- /detect
export interface DetectionItem {
  crop_url: string; // Public URL for image display (e.g., /appdata/detect/...)
  path: string; // Local file system path (for Backend use, e.g., 'appdata/detect/...')
  class: string; // The detected item class (e.g., 'sofa')
  File_name: string;
  bbox: number[]; // [x1, y1, x2, y2]
  confidence: number;
}

// --- 2. Interface עבור המלצות מוצר (Recommendation Item) ---
// מבנה נתון שמגיע מ- /recommend/image ו- /recommend/text
export interface RecommendationItem {
  item_name: string;
  item_price: string;
  item_cat: string;
  item_url: string;
  item_img: string; 
  score?: number; 
}

// --- 3. Interface עבור קישור חיצוני (Google Shopping וכו') ---
export interface ExternalLinkItem {
  id: string | number;
  title: string;
  source: string;
  price?: string;
  link: string;
  image?: string;
}

// --- 4. Interface עבור Props של הקומפוננטה (אם נרצה לייצא אותה) ---
export interface DesignRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onResults?: (data: RecommendationItem[], extras?: { externalLinks?: ExternalLinkItem[] }) => void; 
  onImageGenerated?: (base64Image: string) => void;
}