"""Script for creating embeddings from CSV and testing recommendations."""

import os
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import CSV_FILE, IMAGES_DIR, EMBEDDINGS_FILE
from core.embeddings import EmbeddingService


def embed_images_from_csv(csv_path: str = None, images_dir: str = None, output_pkl_path: str = None, model=None) -> pd.DataFrame:
    """
    Read CSV, load images, embed with CLIP, and save DataFrame with vectors.
    
    Args:
        csv_path: Path to CSV file. Defaults to config CSV_FILE.
        images_dir: Directory containing images. Defaults to config IMAGES_DIR.
        output_pkl_path: Path to save pickle file. Defaults to config EMBEDDINGS_FILE.
        model: Optional pre-loaded CLIP model. If None, will load one.
    
    Returns:
        DataFrame with all CSV columns + 'vector' column containing embeddings
    """
    embedding_service = EmbeddingService(model=model)
    return embedding_service.encode_images_from_csv(
        csv_path=csv_path,
        images_dir=images_dir,
        output_path=output_pkl_path
    )


if __name__ == "__main__":
    # Check if CSV exists
    if not CSV_FILE.exists():
        print(f"❌ CSV file not found: {CSV_FILE}")
        print("   Please run the scraper first: python embedding/ikea_scrape.py")
        sys.exit(1)
    
    # Create embedding service
    embedding_service = EmbeddingService()
    
    # Create embeddings
    print("\n" + "="*60)
    print("STEP 1: Creating embeddings from CSV")
    print("="*60)
    df_with_embeddings = embed_images_from_csv(
        csv_path=str(CSV_FILE),
        images_dir=str(IMAGES_DIR),
        output_pkl_path=str(EMBEDDINGS_FILE),
        model=embedding_service.model
    )