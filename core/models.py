"""Model loading and management utilities.

This is the ONLY file that backend should import from.
It provides a unified interface to load all services.
"""

import os
import pickle
from typing import Optional
import pandas as pd

from .clip import CLIPModel
from .diffusion import DesignGenerationService
from .yolo import YOLODetectionService
from .recommender import Recommender
from .config import EMBEDDINGS_FILE


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
        clip_model = CLIPModel()  # Will load default model automatically
        ikea_df = ModelLoader._load_ikea_dataframe(df_path)
        return Recommender(model=clip_model, embeddings_df=ikea_df)
    
    @staticmethod
    def load_generation_service() -> DesignGenerationService:
        """
        Load generation service for design generation.
        """
        return DesignGenerationService()
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    @staticmethod
    def _load_ikea_dataframe(df_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load IKEA DataFrame from pickle file.
        
        Args:
            df_path: Optional custom path to DataFrame file. If None, uses config default.
            
        Returns:
            DataFrame with product data and embeddings
            
        Raises:
            FileNotFoundError: If DataFrame file doesn't exist
        """
        if df_path is None:
            df_path = str(EMBEDDINGS_FILE)
        
        if not os.path.exists(df_path):
            raise FileNotFoundError(f"IKEA DataFrame not found at {df_path}")
        
        print(f"📖 Loading IKEA DataFrame from {df_path}...")
        with open(df_path, 'rb') as f:
            df = pickle.load(f)
        print(f"✅ Loaded {len(df)} products from DataFrame")
        return df
