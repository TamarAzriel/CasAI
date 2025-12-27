"""Recommendation engine for furniture similarity search."""

import os
from typing import Optional
import numpy as np
import pandas as pd
from PIL import Image
import requests
import urllib.parse
from dotenv import load_dotenv

from .clip import CLIPModel
from .config import get_style_description


class Recommender:
    """Recommendation engine using CLIP embeddings for similarity search."""
    
    def __init__(self, model: CLIPModel, embeddings_df: pd.DataFrame):
        """
        Initialize recommender with model and embeddings.
        
        Args:
            model: CLIPModel instance for encoding queries
            embeddings_df: DataFrame with 'vector' column containing embeddings
        """
        self.model = model
        self.embeddings_df = self._prepare_embeddings(embeddings_df)
        
        # Load environment variables
        load_dotenv()


    @staticmethod
    def _prepare_embeddings(embeddings_df: pd.DataFrame) -> pd.DataFrame:
        """Filter and prepare embeddings DataFrame."""
        valid_df = embeddings_df[embeddings_df['vector'].notna()].copy()
        if valid_df.empty:
            raise ValueError("No valid embeddings found in DataFrame")
        return valid_df
    
    def _encode(
        self,
        query_text: Optional[str] = None,
        query_image_path: Optional[str] = None,
        alpha: float = 0.5
    ) -> np.ndarray:
        """
        Encode query (text and/or image) into embedding vector.
        
        Args:
            query_text: Optional text query
            query_image_path: Optional path to query image
            alpha: Weight for text embedding when both are provided (default: 0.5)
            
        Returns:
            Query embedding vector as numpy array
        """
        if query_text and query_image_path:
            # Both text and image provided - combine with weighted average
            query_text = get_style_description(query_text)
            text_embedding = np.array(self.model.encode_text(query_text))
            image_embedding = np.array(self.model.encode_image(query_image_path))
            # Weighted combination
            combined = alpha * text_embedding + (1 - alpha) * image_embedding
            return combined.flatten()
        elif query_text:
            # Text only
            query_text = get_style_description(query_text)
            text_embedding = np.array(self.model.encode_text(query_text))
            return text_embedding.flatten()
        elif query_image_path:
            # Image only
            image_embedding = np.array(self.model.encode_image(query_image_path))
            return image_embedding.flatten()
        else:
            raise ValueError("Either query_text or query_image_path must be provided")
    
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
        top_k: int = 10,
        alpha: float = 0.5
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
        query_vector = self._encode(query_text, query_image_path, alpha)
        
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

    def search_google_shopping(self, query: str) -> list[dict]:
        """
        Google Shopping search using Serper.dev API.
        Returns stable, user-safe links to Google Shopping results.
        
        Args:
            query: Search query string
            
        Returns:
            List of product dictionaries with title, price, source, image, link
            Each product has:
            - title: Product name
            - price: Product price (if available)
            - source: Store/source name
            - image: Product image URL
            - link: Stable Google Shopping search link
            - raw_link: Original product link (if available)
        """
        url = "https://google.serper.dev/shopping"
        
        # Get API key from environment
        api_key = os.getenv("SERPER_API_KEY")
        
        if not api_key:
            print("⚠️ Error: SERPER_API_KEY not found in environment variables.")
            return []

        payload = {
            "q": query,
            "gl": "il",  # Country: Israel
            "hl": "he"   # Language: Hebrew
        }

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            results = response.json()

            shopping_results = results.get("shopping", [])
            products = []

            for item in shopping_results:
                title = item.get("title", "")
                if not title:
                    continue
                
                # Create stable Google Shopping search link
                safe_title = urllib.parse.quote(title)
                stable_link = f"https://www.google.com/search?q={safe_title}&tbm=shop"

                products.append({
                    "title": title,
                    "price": item.get("price"),
                    "source": item.get("source", ""),
                    "image": item.get("imageUrl", ""),
                    "link": stable_link,
                    "raw_link": item.get("link", "")  # Original product link
                })

            print(f"✅ Found {len(products)} Google Shopping results for '{query}'")
            return products

        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching Google Shopping (network): {e}")
            return []
        except Exception as e:
            print(f"❌ Error searching Google Shopping: {e}")
            import traceback
            traceback.print_exc()
            return []

    
    #TODO: need to know if it work correctly i didnt look at this code yet
    def chat_with_designer(self, image_path, messages):
        """
        ניהול שיחה עם Gemini Pro Vision (חינם).
        """
        try:
            # טעינת התמונה
            img = Image.open(image_path)

            # בניית הפרומפט
            # Gemini עובד הכי טוב כשנותנים לו את התמונה ואת כל ההיסטוריה כטקסט רציף או כרשימה
            
            prompt_parts = [
                "You are CasAI, an expert interior designer. Analyze the image and answer the user's questions.",
                "Be helpful, concise, and professional. If the user asks in Hebrew, answer in Hebrew.",
                img # התמונה עצמה נכנסת כחלק מהפרומפט!
            ]

            # הוספת היסטוריית השיחה לפרומפט כדי שיהיה הקשר
            history_text = "\nChat History:\n"
            for msg in messages:
                role = "User" if msg['role'] == "user" else "CasAI"
                history_text += f"{role}: {msg['content']}\n"
            
            prompt_parts.append(history_text)
            prompt_parts.append("\nCasAI (Your response):")

            # שליחה למודל
            response = self.gemini_model.generate_content(prompt_parts)
            return response.text

        except Exception as e:
            print(f"Gemini Error: {e}")
            return "מצטערת, הייתה בעיה בתקשורת עם המעצבת. נסה שוב."