"""Embedding service for image and text encoding using CLIP."""

import os
from typing import Optional, List
import numpy as np
import pandas as pd
import pickle
from PIL import Image
from sentence_transformers import SentenceTransformer

from .config import CLIP_MODEL_NAME, IMAGES_DIR, CSV_FILE, EMBEDDINGS_FILE


class EmbeddingService:
    """Service for creating and managing CLIP embeddings."""
    
    def __init__(self, model: Optional[SentenceTransformer] = None):
        """
        Initialize embedding service.
        
        Args:
            model: Optional pre-loaded CLIP model. If None, will load one.
        """
        self.model = model or self._load_model()
    
    @staticmethod
    def _load_model() -> SentenceTransformer:
        """Load and return CLIP model."""
        print("🤖 Loading CLIP model...")
        model = SentenceTransformer(CLIP_MODEL_NAME)
        print("✅ CLIP model loaded successfully!")
        return model
    
    def encode_image(self, image_path: str) -> np.ndarray:
        """
        Encode an image file into an embedding vector.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image encoding fails
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            img = Image.open(image_path).convert('RGB')
            embedding = self.model.encode(img)
            return embedding
        except Exception as e:
            raise ValueError(f"Failed to encode image {image_path}: {e}")
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode text into an embedding vector.
        
        Args:
            text: Text string to encode
            
        Returns:
            Embedding vector as numpy array
        """
        return self.model.encode(text)
    
    def encode_images_from_csv(
        self,
        csv_path: Optional[str] = None,
        images_dir: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Read CSV, load images, embed with CLIP, and save DataFrame with vectors.
        
        Args:
            csv_path: Path to CSV file. Defaults to config CSV_FILE.
            images_dir: Directory containing images. Defaults to config IMAGES_DIR.
            output_path: Path to save pickle file. Defaults to config EMBEDDINGS_FILE.
        
        Returns:
            DataFrame with all CSV columns + 'vector' column containing embeddings
        """
        csv_path = csv_path or str(CSV_FILE)
        images_dir = images_dir or str(IMAGES_DIR)
        output_path = output_path or str(EMBEDDINGS_FILE)
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"📖 Reading CSV from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} products from CSV")
        
        if not os.path.exists(images_dir):
            print(f"⚠️ Warning: Images directory not found: {images_dir}")
            print("   Creating directory. Make sure images are downloaded.")
            os.makedirs(images_dir, exist_ok=True)
        
        vectors = []
        successful = 0
        failed = 0
        
        print("🔄 Processing images and creating embeddings...")
        for idx, row in df.iterrows():
            image_file = row.get('image_file', '')
            if pd.isna(image_file) or not image_file:
                vectors.append(None)
                failed += 1
                continue
            
            image_path = os.path.join(images_dir, str(image_file))
            
            try:
                if os.path.exists(image_path):
                    img = Image.open(image_path).convert('RGB')
                    embedding = self.model.encode(img)
                    vectors.append(embedding)
                    successful += 1
                else:
                    # Try to download from image_url if local file doesn't exist
                    image_url = row.get('image_url', '')
                    if image_url and not pd.isna(image_url):
                        try:
                            import requests
                            response = requests.get(image_url, timeout=10)
                            if response.status_code == 200:
                                img = Image.open(requests.get(image_url, stream=True).raw).convert('RGB')
                                embedding = self.model.encode(img)
                                vectors.append(embedding)
                                successful += 1
                                # Save the image locally
                                with open(image_path, 'wb') as f:
                                    f.write(response.content)
                            else:
                                vectors.append(None)
                                failed += 1
                        except Exception:
                            vectors.append(None)
                            failed += 1
                    else:
                        vectors.append(None)
                        failed += 1
            except Exception:
                vectors.append(None)
                failed += 1
            
            # Progress indicator
            if (idx + 1) % 50 == 0:
                print(f"   Processed {idx + 1}/{len(df)} images... (Success: {successful}, Failed: {failed})")
        
        # Add vectors to DataFrame
        df['vector'] = vectors
        
        # Filter out rows with None vectors
        df_with_vectors = df[df['vector'].notna()].copy()
        
        print(f"✅ Embedding complete! Successfully embedded {successful} images, {failed} failed")
        print(f"   Saving DataFrame with {len(df_with_vectors)} products to {output_path}...")
        
        # Save DataFrame as pickle
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(df_with_vectors, f)
        
        print(f"✅ Saved embeddings to {output_path}")
        
        return df_with_vectors
