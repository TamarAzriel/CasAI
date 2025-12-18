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

    def get_style_advice(self, user_image_path: str, user_text: str) -> Dict[str, Any]:
        """
        AI Stylist Logic: Returns both a friendly advice paragraph and a list of items.
        """
        if not self.openai_client:
            raise ValueError("OpenAI API Key is missing.")

        base64_image = self._encode_image_to_base64(user_image_path)
        
        # --- השינוי העיקרי: הפרומפט מבקש "שיח" ---
        prompt = f"""
        You are a warm, professional interior designer named "CasAI". 
        The user sent a photo of their room and said: "{user_text}".
        
        Your Goal:
        1. Analyze the room's atmosphere and the user's request.
        2. Write a short, friendly paragraph (2-3 sentences) explaining what is missing and why. Speak directly to the user (e.g., "I noticed your room has... so I recommend...").
        3. Suggest exactly 3 physical items to buy that solve the problem.
        
        Output Format (JSON ONLY):
        {{
            "advice": "Your friendly explanation here...",
            "items": [
                {{ "item_name": "...", "reason": "...", "search_query": "..." }},
                ...
            ]
        }}
        """

        print("🤖 Asking GPT-4o for advice + items...")
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=600
        )

        content = response.choices[0].message.content
        clean_json = content.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(clean_json)
        except json.JSONDecodeError:
            # Fallback למקרה של שגיאה בפורמט
            data = {"advice": "Here are some items that might help!", "items": []}

        advice_text = data.get("advice", "")
        suggestions = data.get("items", [])

        print(f"💡 Designer Advice: {advice_text}")

        final_items = []

        # (לוגיקת החיפוש הקיימת נשארת אותו דבר)
        for item in suggestions:
            query_vec = self.model.encode(item['search_query'])
            product_vectors = np.array([v.flatten() for v in self.embeddings_df['vector'].values])
            sims = self._calculate_similarities(query_vec, product_vectors)
            best_idx = np.argmax(sims)
            best_score = sims[best_idx]
            
            result_item = {
                "ai_suggestion": item['item_name'],
                "ai_reason": item['reason'],
                "search_query": item['search_query'],
                "source": "unknown"
            }

            if best_score > 0.24:
                row = self.embeddings_df.iloc[best_idx]
                result_item.update({
                    "source": "local_ikea",
                    "item_name": row.get('item_name', 'Unknown'),
                    "item_price": row.get('item_price', ''),
                    "item_url": row.get('product_link', ''),
                    "item_img": row.get('image_file', ''),
                    "similarity": float(best_score)
                })
            else:
                result_item["source"] = "google_search"
            
            final_items.append(result_item)

        # מחזירים אובייקט שמכיל גם את העצה וגם את הפריטים
        return {
            "advice": advice_text,
            "recommendations": final_items
        }