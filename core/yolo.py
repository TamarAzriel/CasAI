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
    
    def __init__(self, yolo_model: Optional[YOLO] = None, model_path: Optional[str] = None):
        """
        Initialize detection service.
        
        Args:
            yolo_model: Optional pre-loaded YOLO model. If None, loads from config.
            model_path: Optional custom path to YOLO model. If None, uses config paths.
        """
        if yolo_model is not None:
            self.yolo_model = yolo_model
        else:
            # Load model from config
            self.yolo_model = self.load_model(model_path)
    
    def detect_furniture(
        self,
        image_path: str,
        save_dir: str,
        conf_threshold: float = YOLO_CONF_THRESHOLD
    ) -> list[dict]:
        """
        Detect furniture in image using YOLO and save cropped images.
        
        Args:
            image_path: Path to input image
            save_dir: Directory to save cropped images (must exist)
            conf_threshold: Confidence threshold for detection
            
        Returns:
            List of dictionaries with detection results including:
            - File_name: Name of saved crop file
            - class: Furniture class name
            - path: Full path to saved crop
            - bbox: Bounding box coordinates [x1, y1, x2, y2]
            - confidence: Detection confidence score
            - crop_url: URL path for serving the crop
            
        Raises:
            ValueError: If image cannot be read
            FileNotFoundError: If save_dir doesn't exist
        """
        # Ensure save_dir exists - this is infrastructure responsibility
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
                # Convert coordinates safely
                box = boxes.xyxy[i].cpu().numpy().astype(int)
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                
                yolo_class_name = result.names.get(class_id)
                if yolo_class_name is None:
                    continue
                
                # Save cropped image
                file_name = f"{base_name}_{counter}_{yolo_class_name}.jpg"
                save_path = os.path.join(save_dir, file_name)
                
                crop_img = pil_image.crop(tuple(box.tolist()))
                crop_img.save(save_path)
                
                # Create public URL path (relative to appdata/detect route)
                # Backend serves files from /appdata/detect/<filename>
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
        """
        Load YOLO model for furniture detection.
        
        Args:
            model_path: Optional custom path to YOLO model. If None, loads model from config.
            
        Returns:
            Loaded YOLO model
            
        Raises:
            FileNotFoundError: If custom model_path is provided but doesn't exist
        """
        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"YOLO model not found at {model_path}")
            return YOLO(model_path, task='detect')
        
        # Load raw YOLO model from config (will download automatically if not cached)
        return YOLO(YOLO_MODEL_NAME, task='detect')
