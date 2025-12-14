"""Model loading and management utilities.

This is the ONLY file that backend should import from.
It provides a unified interface to load all services.
"""

import os
import pickle
from typing import Optional
import pandas as pd

from .config import EMBEDDINGS_FILE
from .clip import load_clip_model as _load_clip_model
from .yolo import load_yolo_model as _load_yolo_model, YOLODetectionService
from .diffusion import load_diffusion_model as _load_diffusion_model, generate_design
from .recommender import Recommender


class ModelLoader:
    """Service factory for loading ML models and services.
    
    This class provides high-level service interfaces that backend should use.
    All services are pre-configured and ready to use.
    """
    
    # ========================================================================
    # Public Service Methods (Backend should only use these)
    # ========================================================================
    
    @staticmethod
    def load_detection_service(model_path: Optional[str] = None) -> YOLODetectionService:
        """
        Load detection service for furniture detection.
        
        Args:
            model_path: Optional custom path to YOLO model
            
        Returns:
            YOLODetectionService instance ready to use
        """
        return YOLODetectionService(model_path=model_path)
    
    @staticmethod
    def load_recommendation_service(df_path: Optional[str] = None) -> Recommender:
        """
        Load recommendation service with CLIP model and IKEA DataFrame.
        
        Args:
            df_path: Optional custom path to DataFrame file
            
        Returns:
            Recommender instance ready to use
        """
        clip_model = _load_clip_model()
        ikea_df = ModelLoader._load_ikea_dataframe(df_path)
        return Recommender(clip_model, ikea_df)
    
    @staticmethod
    def load_generation_service():
        """
        Load generation service with pre-loaded diffusion model.
        
        Returns:
            Function that generates designs: generate(original_path, crop_path, prompt) -> Image
        """
        diffusion_model = _load_diffusion_model()
        
        def generate(original_image_path: str, crop_image_path: str, prompt: str):
            """Generate design using pre-loaded diffusion model."""
            return generate_design(original_image_path, crop_image_path, prompt, diffusion_model)
        
        return generate
    
    # ========================================================================
    # Internal Helper Methods (Not for backend use)
    # ========================================================================
    
    @staticmethod
    def _load_ikea_dataframe(df_path: Optional[str] = None) -> pd.DataFrame:
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
                print(f"Warning: DataFrame missing columns: {missing_cols}")
            
            return df
        except Exception as e:
            raise ValueError(f"Failed to load IKEA DataFrame: {e}") from e


# Public API exports
__all__ = ['ModelLoader']
