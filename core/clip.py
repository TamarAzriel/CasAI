"""CLIP model handling for image and text embeddings."""

from sentence_transformers import SentenceTransformer
from .config import CLIP_MODEL_NAME
import os
from typing import Optional, List
import pandas as pd
import pickle
from PIL import Image

class CLIPModel:
    """Wrapper for CLIP model operations."""
    
    def __init__(self):
        """
        Initialize CLIP model wrapper.
        
        Args:
            model: Optional pre-loaded SentenceTransformer CLIP model
            model_name: Optional model name to load. If model is None, will load using model_name or default.
        """
        self.model = self.load_model()
    
    @staticmethod
    def load_model() -> SentenceTransformer:
        """
        Load CLIP model for image similarity.
        
        Args:
        Returns:
            Loaded SentenceTransformer CLIP model
            
        Raises:
            ImportError: If sentence-transformers is not installed
        """
        try:
            model = SentenceTransformer(CLIP_MODEL_NAME)
            print("✅ CLIP model loaded successfully!")
            return model
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Please run: pip install sentence-transformers"
            )
    
    def encode_text(self, text: str) -> list:
        """
        Encode text into embedding vector.
        
        Args:
            text: Text string to encode
            
        Returns:
            Embedding vector as list
        """
        return self.model.encode(text).tolist()
    
    def encode_image(self, image_path: str) -> list:
        """
        Encode image into embedding vector.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector as list
        """
        from PIL import Image
        img = Image.open(image_path).convert('RGB')
        return self.model.encode(img).tolist()

    def encode_images_from_csv(
            self,
            csv_path: Optional[str] = None,
            images_dir: Optional[str] = None,
            output_path: Optional[str] = None
    ):
        """
        Read CSV, load images, embed with CLIP, and save DataFrame with vectors.

        Args:
            csv_path: Path to CSV file. Defaults to config CSV_FILE.
            images_dir: Directory containing images. Defaults to config IMAGES_DIR.
            output_path: Path to save pickle file. Defaults to config EMBEDDINGS_FILE.

        Returns:
            DataFrame with all CSV columns + 'vector' column containing embeddings
        """

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