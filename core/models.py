"""Model loading and management utilities."""

import os
import pickle
from typing import Optional
import pandas as pd
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer

from .config import (
    YOLO_MODEL_PATH,
    YOLO_MODEL_PATH_PT,
    EMBEDDINGS_FILE,
    CLIP_MODEL_NAME
)


class ModelLoader:
    """Utility class for loading ML models."""
    
    @staticmethod
    def load_yolo_model(model_path: Optional[str] = None) -> YOLO:
        """
        Load YOLO model for furniture detection.
        
        Args:
            model_path: Optional custom path to YOLO model
            
        Returns:
            Loaded YOLO model
            
        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"YOLO model not found at {model_path}")
            return YOLO(model_path, task='detect')
        
        # Try .onnx first, then .pt
        if os.path.exists(YOLO_MODEL_PATH):
            return YOLO(str(YOLO_MODEL_PATH), task='detect')
        elif os.path.exists(YOLO_MODEL_PATH_PT):
            return YOLO(str(YOLO_MODEL_PATH_PT), task='detect')
        else:
            raise FileNotFoundError(
                f"YOLO model not found at {YOLO_MODEL_PATH} or {YOLO_MODEL_PATH_PT}"
            )
    
    @staticmethod
    def load_clip_model() -> SentenceTransformer:
        """
        Load CLIP model for image similarity.
        
        Returns:
            Loaded CLIP model
            
        Raises:
            ImportError: If sentence-transformers is not installed
        """
        try:
            model = SentenceTransformer(CLIP_MODEL_NAME)
            return model
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Please run: pip install sentence-transformers"
            )
    
    @staticmethod
    def load_ikea_dataframe(df_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load IKEA product DataFrame with embeddings.
        
        Args:
            df_path: Optional custom path to pickle file
            
        Returns:
            DataFrame with product data and embeddings
            
        Raises:
            FileNotFoundError: If DataFrame file doesn't exist
            ValueError: If DataFrame is invalid
        """
        path = df_path or str(EMBEDDINGS_FILE)
        
        if not os.path.exists(path):
            error_msg = (
                f"IKEA DataFrame not found at {path}\n\n"
                "Please run the embedding script first:\n"
                "  python embedding/embed-ds.py"
            )
            raise FileNotFoundError(error_msg)
        
        try:
            with open(path, 'rb') as f:
                df = pickle.load(f)
            
            # Verify DataFrame has required columns
            required_cols = [
                'vector', 'item_name', 'item_price', 
                'item_cat', 'image_url', 'product_link'
            ]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"⚠️ Warning: DataFrame missing columns: {missing_cols}")
            
            return df
        except Exception as e:
            raise ValueError(f"Failed to load IKEA DataFrame: {e}")
