"""Furniture detection utilities using YOLO."""

import os
import cv2
from typing import List, Dict
from PIL import Image
from ultralytics import YOLO

import sys
import os

# Add parent directory to path for imports (assuming the structure is correct)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import (
    TARGET_CLASSES,
    YOLO_CONF_THRESHOLD,
    map_yolo_class_to_app_class
)


class DetectionService:
    """Service for detecting furniture in images using YOLO."""
    
    def __init__(self, yolo_model: YOLO):
        """
        Initialize detection service.
        
        Args:
            yolo_model: Loaded YOLO model
        """
        self.yolo_model = yolo_model
    
    def detect_furniture(
        self,
        image_path: str,
        save_dir: str = 'appdata/detect/',
        conf_threshold: float = YOLO_CONF_THRESHOLD
    ) -> List[Dict]:
        """
        Detect furniture in image using YOLO and save cropped images.
        """
        os.makedirs(save_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        imagecv = cv2.imread(image_path)
        if imagecv is None:
            raise ValueError(f"Could not read image from {image_path}")
        
        # YOLO prediction
        results = self.yolo_model.predict(
            source=imagecv,
            conf=conf_threshold,
            verbose=False
        )
        
        result = results[0]
        boxes = result.boxes
        detected_photos = []
        
        if boxes is not None and len(boxes) > 0:
            img_rgb = cv2.cvtColor(imagecv, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            counter = 1
            
            for i in range(len(boxes)):
                # Convert coordinates safely
                box = boxes.xyxy[i].cpu().numpy().astype(int)
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                
                yolo_class_name = result.names.get(class_id)
                if yolo_class_name is None:
                    continue
                
                app_class_name = map_yolo_class_to_app_class(yolo_class_name)
                
                if app_class_name not in TARGET_CLASSES:
                    continue
                
                # --- שמירה ויצירת נתיבים (התיקון שהוספנו) ---
                file_name = f"{base_name}_{counter}_{app_class_name}.jpg"
                save_path = os.path.join(save_dir, file_name)
                
                crop_img = pil_image.crop(tuple(box.tolist()))
                crop_img.save(save_path)
                
                # יצירת ה-URL הציבורי (crop_url)
                normalized_path = os.path.normpath(save_path).replace(os.path.sep, '/')
                if not normalized_path.startswith('/'):
                    normalized_path = '/' + normalized_path
                # ---------------------------------------------
                
                detected_photos.append({
                    'File_name': file_name,
                    'class': app_class_name,
                    'path': save_path,
                    'bbox': box.tolist(),
                    'confidence': confidence,
                    # --- המפתח שפתר את ה-KeyError ---
                    'crop_url': normalized_path, 
                    # ----------------------------------
                })
                counter += 1
        
        return detected_photos