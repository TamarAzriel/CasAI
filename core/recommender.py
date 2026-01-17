"""Recommendation engine for furniture similarity search."""

import os
from typing import Optional
import numpy as np
import pandas as pd
from PIL import Image
import requests
import urllib.parse
import json
import re
from dotenv import load_dotenv
from google import genai  # NEW SDK
from google.genai import types

from .clip import CLIPModel
from .config import get_style_description


class Recommender:
    """Recommendation engine using CLIP embeddings for similarity search."""

    def __init__(self, model: CLIPModel, embeddings_df: pd.DataFrame):
        """
        Initialize recommender with model, embeddings, and Gemini.
        """
        self.model = model
        self.embeddings_df = self._prepare_embeddings(embeddings_df)

        # 1. טעינת קובץ ה-env
        load_dotenv()

        # 2. שליפת המפתח (תמיכה בשני השמות הנפוצים)
        api_key = os.getenv("AIChat_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            print("⚠️ Warning: API Key not found in .env file")
            self.client = None
        else:
            # 3. הגדרת ה-Client החדש
            try:
                os.environ['GOOGLE_API_USE_REST'] = 'true'
                self.client = genai.Client(api_key=api_key)
                self.model_name = 'gemini-2.5-flash'
                print(f"✅ Gemini Designer is ready with model: {self.model_name}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini Client: {e}")
                self.client = None

        # --- חילוץ מידות מה-CSV של איקאה בעת הטעינה ---
        def extract_dimensions(name):
            # מחפש תבנית של מספרים כמו 160x200 בתוך שם המוצר
            if not isinstance(name, str): return None, None
            match = re.search(r'(\d+)\s*[xX*]\s*(\d+)', name)
            if match:
                return int(match.group(1)), int(match.group(2))
            return None, None

        if 'item_name' in self.embeddings_df.columns:
            print("📏 Extracting dimensions from IKEA catalog...")
            dims = self.embeddings_df['item_name'].map(extract_dimensions)
            self.embeddings_df['width'], self.embeddings_df['length'] = zip(*dims)

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
        """Encode query (text and/or image) into embedding vector."""
        if query_text and query_image_path:
            query_text = get_style_description(query_text)
            text_embedding = np.array(self.model.encode_text(query_text))
            image_embedding = np.array(self.model.encode_image(query_image_path))
            combined = alpha * text_embedding + (1 - alpha) * image_embedding
            return combined.flatten()
        elif query_text:
            query_text = get_style_description(query_text)
            text_embedding = np.array(self.model.encode_text(query_text))
            return text_embedding.flatten()
        elif query_image_path:
            image_embedding = np.array(self.model.encode_image(query_image_path))
            return image_embedding.flatten()
        else:
            raise ValueError("Either query_text or query_image_path must be provided")

    def _calculate_similarities(
            self,
            query_vector: np.ndarray,
            product_vectors: np.ndarray
    ) -> np.ndarray:
        """Calculate cosine similarities."""
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        product_norms = product_vectors / (np.linalg.norm(product_vectors, axis=1, keepdims=True) + 1e-8)
        similarities = np.dot(product_norms, query_norm)
        return similarities

    def analyze_query(self, query_text: str, image_path: Optional[str] = None):
        """
        Analyses both text and image in ONE Gemini call to save time.
        """
        if not self.client:
            return "None", None, None

        try:
            prompt = """
            You are a furniture expert. Analyze the user request and image.
            Return ONLY a JSON object: {"category": "...", "width": 120, "length": 60}
            """
            
            contents = [prompt]
            if query_text: contents.append(f"User request: {query_text}")
            if image_path: contents.append(Image.open(image_path))
                
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('category', 'None'), data.get('width'), data.get('length')
                
        except Exception as e:
            print(f"⚠️ Error in combined analysis: {e}")
            
        return "None", None, None

    def recommend(
            self,
            query_text: Optional[str] = None,
            query_image_path: Optional[str] = None,
            top_k: int = 10,
            alpha: float = 0.5,
            category_filter=None,
            precomputed_dims=(None, None)
    ) -> pd.DataFrame:
        """
        Get top-k recommendations with SMART category filtering.
        """
        # 1. יצירת וקטור חיפוש
        query_vector = self._encode(query_text, query_image_path, alpha)

        df_to_search = self.embeddings_df.copy()

        # 2. לוגיקת סינון קטגוריה משופרת (Smart Filtering)
        target_cat = category_filter
        if target_cat and target_cat != 'None':
            print(f"🔍 Trying to filter by category: '{target_cat}'")
            # ... (rest of filtering logic)
            exact_match = df_to_search[df_to_search['item_cat'] == target_cat]
            if len(exact_match) > 0:
                df_to_search = exact_match
            else:
                search_term = target_cat.lower().replace("frame", "").replace("dining", "").strip()
                partial_match = df_to_search[
                    df_to_search['item_cat'].astype(str).str.lower().str.contains(search_term, regex=False)
                ]
                if len(partial_match) > 0:
                    df_to_search = partial_match

        # 3. חישוב דמיון ויזואלי
        product_vectors = np.array([v for v in df_to_search['vector'].values])
        similarities = self._calculate_similarities(query_vector, product_vectors)
        df_to_search['similarity'] = similarities

        # 4. שימוש במידות שהוערכו מראש (כדי לחסוך קריאת API)
        target_w, target_l = precomputed_dims
        
        # אם לא הועברו מידות, והמשתמש לא סיפק קטגוריה (שאולי כבר הכילה מידות), מנסים פעם אחרונה
        if target_w is None and query_image_path:
             # רק אם ממש חייבים, עושים קריאה נפרדת (אבל בשימוש נכון זה לא יקרה)
             target_w, target_l = self.estimate_dimensions(query_image_path)

        def calculate_final_score(row):
            score = row['similarity']
            if target_w is None or pd.isna(row.get('width')):
                return score
            diff_w = abs(row['width'] - target_w) / max(target_w, 1)
            diff_l = abs(row['length'] - target_l) / max(target_l, 1)
            penalty = (diff_w + diff_l) / 2
            return score - (penalty * 0.4)

        df_to_search['final_score'] = df_to_search.apply(calculate_final_score, axis=1)
        top_results = df_to_search.sort_values('final_score', ascending=False).head(top_k).copy()
        return top_results

    def search_google_shopping(self, query: str) -> list[dict]:
        """Google Shopping search using Serper.dev API."""
        url = "https://google.serper.dev/shopping"
        api_key = os.getenv("SERPER_API_KEY")

        if not api_key:
            print("⚠️ Error: SERPER_API_KEY not found in environment variables.")
            return []

        payload = {"q": query, "gl": "il", "hl": "he"}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            response.raise_for_status()
            results = response.json()

            products = []
            for item in results.get("shopping", []):
                title = item.get("title", "")
                if not title: continue
                safe_title = urllib.parse.quote(title)

                products.append({
                    "title": title,
                    "price": item.get("price"),
                    "source": item.get("source", ""),
                    "image": item.get("imageUrl", ""),
                    "link": f"https://www.google.com/search?q={safe_title}&tbm=shop",
                    "raw_link": item.get("link", "")
                })

            print(f"✅ Found {len(products)} Google Shopping results")
            return products

        except Exception as e:
            print(f"❌ Error searching Google Shopping: {e}")
            return []

    def chat_with_designer(self, image_path, messages):
        """ניהול שיחה עם Gemini והצעת פריטים מהמאגר באופן אוטומטי."""
        if not self.client:
            return {"text": "Designer service not available. Please check your API key.", "recommendations": []}
            
        try:
            history_text = "Chat History:\n"
            for msg in messages:
                role = "User" if msg['role'] == "user" else "CasAI"
                history_text += f"{role}: {msg['content']}\n"

            prompt = f"""
            You are CasAI, an expert interior designer. Analyze the situation and answer the user's questions.
            Be helpful, concise, and professional. If the user asks in Hebrew, answer in Hebrew.
            
            IMPORTANT DIRECTIONS:
            1. Your advice should be specific. If you suggest a piece of furniture, describe its style, material, and color.
            2. For every specific piece of furniture you recommend in your text, you MUST provide a highly descriptive search query in the 'search_queries' list.
            3. The 'search_queries' should be in English and include the type, style, and color (e.g., "minimalist black metal coffee table" instead of just "table").
            4. Your response MUST be a valid JSON object.
            
            JSON format:
            {{
              "response_text": "Your helpful text response here (in Hebrew if the user asked in Hebrew)...",
              "search_queries": ["descriptive search term 1", "descriptive search term 2"] 
            }}

            {history_text}
            CasAI (Response in JSON):
            """
            
            contents = [prompt]
            if image_path and os.path.exists(image_path):
                try:
                    contents.append(Image.open(image_path))
                except:
                    pass
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            
            # Extract JSON from response
            json_text = response.text.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].strip()
            
            try:
                data = json.loads(json_text)
                response_text = data.get("response_text", "")
                search_queries = data.get("search_queries", [])
                
                all_recs = []
                if search_queries:
                    for query in search_queries:
                        # Search for the best matches in our database
                        recs = self.recommend(query_text=query, top_k=2)
                        for _, row in recs.iterrows():
                            all_recs.append({
                                'item_name': row.get('item_name', ''),
                                'item_price': row.get('item_price', ''),
                                'item_url': row.get('product_link', ''),
                                'item_img': f"/data/ikea_il_images/{row['image_file']}" if pd.notna(row.get('image_file')) else row.get('image_url', '')
                            })

                return {
                    "text": response_text,
                    "recommendations": all_recs
                }
            except:
                # Fallback if Gemini returns plain text instead of JSON
                return {
                    "text": response.text,
                    "recommendations": []
                }

        except Exception as e:
            print(f"Gemini Error: {e}")
            return {"text": "Sorry, I'm having trouble thinking right now. Let's try again in a moment.", "recommendations": []}

    def estimate_dimensions(self, image_path):
        """
        משתמש ב-Gemini להערכת מידות הרהיט מהתמונה.
        """
        if not self.client:
            return None, None

        try:
            img = Image.open(image_path)
            prompt = """
            Analyze the furniture in this image. 
            Based on standard furniture sizes and room proportions, estimate its:
            1. Width (in cm)
            2. Length/Depth (in cm)

            Return ONLY a JSON object: {"width": 160, "length": 200}
            """
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img],
                config=types.GenerateContentConfig(temperature=0.1)
            )

            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('width'), data.get('length')

        except Exception as e:
            print(f"⚠️ Error estimating dimensions: {e}")

        return None, None