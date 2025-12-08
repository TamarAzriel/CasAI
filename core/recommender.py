"""Recommendation engine for furniture similarity search."""

import os
from typing import Optional
import numpy as np
import pandas as pd
from PIL import Image
from sentence_transformers import SentenceTransformer

from .config import get_style_description


class Recommender:
    """Recommendation engine using CLIP embeddings for similarity search."""
    
    def __init__(self, model: SentenceTransformer, embeddings_df: pd.DataFrame):
        """
        Initialize recommender with model and embeddings.
        
        Args:
            model: CLIP model for encoding queries
            embeddings_df: DataFrame with 'vector' column containing embeddings
        """
        self.model = model
        self.embeddings_df = self._prepare_embeddings(embeddings_df)
    
    @staticmethod
    def _prepare_embeddings(embeddings_df: pd.DataFrame) -> pd.DataFrame:
        """Filter and prepare embeddings DataFrame."""
        valid_df = embeddings_df[embeddings_df['vector'].notna()].copy()
        if valid_df.empty:
            raise ValueError("No valid embeddings found in DataFrame")
        return valid_df
    
    def _encode_query(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None
    ) -> tuple[np.ndarray, list[str]]:
        """
        Encode query (text and/or image) into embedding vector.
        
        Args:
            query_text: Optional text query
            query_image_path: Optional path to query image
            
        Returns:
            Tuple of (query_vector, embedding_types)
        """
        query_embeddings = []
        embedding_types = []
        
        # Handle image if provided
        if query_image_path is not None:
            if not os.path.exists(query_image_path):
                raise FileNotFoundError(f"Query image not found: {query_image_path}")
            try:
                print("🖼️  Encoding IMAGE embedding...")
                img = Image.open(query_image_path).convert('RGB')
                img_embedding = self.model.encode(img)
                query_embeddings.append(img_embedding)
                embedding_types.append("IMAGE")
                print("✅ Image embedding created successfully")
            except Exception as e:
                raise ValueError(f"Failed to encode query image: {e}")
        
        # Handle text if provided
        if query_text is not None and query_text.strip():
            # Check if it's a style name
            style_desc = get_style_description(query_text)
            print(f"📝 Encoding TEXT embedding for: '{query_text}'...")
            text_embedding = self.model.encode(style_desc)
            query_embeddings.append(text_embedding)
            embedding_types.append("TEXT")
            print("✅ Text embedding created successfully")
        
        # Check if we have at least one embedding
        if len(query_embeddings) == 0:
            raise ValueError("At least one of query_text or query_image_path must be provided")
        
        # Combine embeddings if both provided (weighted average)
        if len(query_embeddings) == 2:
            print("🔀 Combining BOTH embeddings (image + text) with equal weights...")
            query_vector = (query_embeddings[0] + query_embeddings[1]) / 2.0
            print("✅ Combined embedding created successfully")
        else:
            query_vector = query_embeddings[0]
            print(f"✅ Using {embedding_types[0]} embedding only")
        
        print(f"🎯 Final embedding type: {' + '.join(embedding_types)}")
        
        return query_vector, embedding_types
    
    def _calculate_similarities(
        self,
        query_vector: np.ndarray,
        product_vectors: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarities between query and product vectors.
        
        Args:
            query_vector: Query embedding vector
            product_vectors: Array of product embedding vectors
            
        Returns:
            Array of similarity scores
        """
        # Normalize query vector
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        
        # Normalize product vectors
        product_norms = product_vectors / (np.linalg.norm(product_vectors, axis=1, keepdims=True) + 1e-8)
        
        # Calculate cosine similarities
        similarities = np.dot(product_norms, query_norm)
        
        return similarities
    
    def recommend(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None,
        top_k: int = 10
    ) -> pd.DataFrame:
        """
        Get top-k recommendations based on query.
        
        Args:
            query_text: Optional text query (e.g., "modern sofa" or style name)
            query_image_path: Optional path to query image
            top_k: Number of recommendations to return (default: 10)
        
        Returns:
            DataFrame with top_k recommendations including similarity scores
        """
        # Encode query
        query_vector, embedding_types = self._encode_query(query_text, query_image_path)
        
        # Get product vectors
        product_vectors = np.array([v.flatten() for v in self.embeddings_df['vector'].values])
        
        # Calculate similarities
        similarities = self._calculate_similarities(query_vector, product_vectors)
        
        # Add similarity scores to DataFrame
        results_df = self.embeddings_df.copy()
        results_df['similarity'] = similarities
        
        # Sort by similarity and return top_k
        top_results = results_df.nlargest(top_k, 'similarity').copy()
        
        print(f"✅ Found {len(top_results)} recommendations")
        
        return top_results
