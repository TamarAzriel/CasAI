"""YOLO detection handling for furniture detection."""

import os
import cv2
from typing import Optional
from PIL import Image
from ultralytics import YOLO

from .config import (
    YOLO_CONF_THRESHOLD,
    YOLO_MODEL_NAME
)


class YOLODetectionService:
    """Service for detecting furniture in images using YOLO."""
    
    # --- הרשימה המעודכנת (Whitelist) ---
    # הוספנו את 72 (מקרר) כדי לנסות לתפוס ארונות גבוהים
    FURNITURE_IDS = [
        56, # Chair (כיסא)
        57, # Couch (ספה)
        58, # Potted plant (עציץ)
        59, # Bed (מיטה)
        60, # Dining Table (שולחן)
        62, # TV (טלויזיה - לפעמים רלוונטי לשידה מתחת)
        72, # Refrigerator (טריק: ארונות בגדים מזוהים לפעמים כמקררים)
        75  # Vase (אגרטל)
    ]

    def __init__(self, yolo_model: Optional[YOLO] = None, model_path: Optional[str] = None):
        """
        Initialize detection service.
        """
        if yolo_model is not None:
            self.yolo_model = yolo_model
        else:
            self.yolo_model = self.load_model(model_path)

    def detect_furniture(
        self,
        image_path: str,
        save_dir: str,
        conf_threshold: float = YOLO_CONF_THRESHOLD
    ) -> list[dict]:
        """
        Detect furniture in image using YOLO and save cropped images.
        Only allows items defined in FURNITURE_IDS.
        """
        if not os.path.exists(save_dir):
            raise FileNotFoundError(f"Save directory does not exist: {save_dir}")

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
                box = boxes.xyxy[i].cpu().numpy().astype(int)
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())

                # --- סינון: בודק אם זה רהיט (או "מקרר/ארון") ---
                if class_id not in self.FURNITURE_IDS:
                    continue
                # -----------------------------------------------

                yolo_class_name = result.names.get(class_id)
                # אם תפסנו מקרר, נשנה את השם שלו ל-wardrobe כדי שזה ייראה טוב
                if class_id == 72:
                    yolo_class_name = "wardrobe_or_cupboard"

                if yolo_class_name is None:
                    continue

                # Save cropped image
                file_name = f"{base_name}_{counter}_{yolo_class_name}.jpg"
                save_path = os.path.join(save_dir, file_name)

                crop_img = pil_image.crop(tuple(box.tolist()))
                crop_img.save(save_path)

                crop_url = f"/appdata/detect/{file_name}"

                detected_photos.append({
                    'File_name': file_name,
                    'class': yolo_class_name,
                    'path': save_path,
                    'bbox': box.tolist(),
                    'confidence': confidence,
                    'crop_url': crop_url,
                })
                counter += 1

        return detected_photos


    @staticmethod
    def load_model(model_path: Optional[str] = None) -> YOLO:
        """Load YOLO model for furniture detection."""
        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"YOLO model not found at {model_path}")
            return YOLO(model_path, task='detect')

        return YOLO(YOLO_MODEL_NAME, task='detect')