"""Recommendation engine for furniture similarity search."""

import os
from typing import Optional
import numpy as np
import pandas as pd
from PIL import Image
from sentence_transformers import SentenceTransformer
import requests
import json
import urllib.parse
from dotenv import load_dotenv 

from .config import get_style_description
import google.generativeai as genai # pyright: ignore[reportMissingImports]
from PIL import Image


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
        
        # הגדרת מפתח ה-API של גוגל
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("⚠️ GEMINI_API_KEY not found in environment variables.")
            self.gemini_model = None

         # טוען את המשתנים מהקובץ .env
        load_dotenv()

        
        # --- DEBUG קריטי: הדפסת שמות העמודות ---
        print(f"DEBUG: Recommendation DF Columns: {self.embeddings_df.columns.tolist()}")
    
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


def search_google_shopping(query):
    """
    Google Shopping search using Serper.dev
    Returns stable, user-safe links
    """

    url = "https://google.serper.dev/shopping"

    # שליפת המפתח מהקובץ הסודי
    api_key = os.getenv("SERPER_API_KEY")

    # בדיקת בטיחות: אם המפתח לא נמצא, מחזירים רשימה ריקה כדי לא לקרוס
    if not api_key:
        print("Error: SERPER_API_KEY not found in .env file.")
        return []

    payload = {
        "q": query,
        "gl": "il",
        "hl": "he"
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
            safe_title = urllib.parse.quote(title)

            # ✅ לינק יציב שתמיד עובד (חיפוש בגוגל שופינג לפי הכותרת)
            stable_link = f"https://www.google.com/search?q={safe_title}&tbm=shop"

            products.append({
                "title": title,
                "price": item.get("price"),
                "source": item.get("source"),
                "image": item.get("imageUrl"),
                "link": stable_link,  # הלינק הזה ייפתח בוודאות
                "raw_link": item.get("link")  # שומרים את המקור למקרה הצורך
            })

        return products

    except Exception as e:
        print(f"Error searching Google Shopping: {e}")
        return []
    
    # בתוך core/recommender.py

    def chat_with_designer(self, image_path, messages):
        """
        ניהול שיחה עם Gemini Pro Vision (חינם).
        """
        if not self.gemini_model:
            return "Error: GEMINI_API_KEY is missing."

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