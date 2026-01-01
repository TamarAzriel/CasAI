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
import google.generativeai as genai  # type: ignore

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
            self.gemini_model = None
        else:
            # 3. הגדרת המפתח מול הספרייה של גוגל
            genai.configure(api_key=api_key)
            try:
                # 4. יצירת המודל
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                print("✅ Gemini Designer is ready!")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
                self.gemini_model = None

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

    def recommend(
            self,
            query_text: Optional[str] = None,
            query_image_path: Optional[str] = None,
            top_k: int = 10,
            alpha: float = 0.5,
            category_filter=None
    ) -> pd.DataFrame:
        """
        Get top-k recommendations with SMART category filtering.
        """
        # 1. יצירת וקטור חיפוש
        query_vector = self._encode(query_text, query_image_path, alpha)

        df_to_search = self.embeddings_df.copy()

        # 2. לוגיקת סינון קטגוריה משופרת (Smart Filtering)
        if category_filter and category_filter != 'None':
            print(f"🔍 Trying to filter by category: '{category_filter}'")

            # שלב א': ניסיון להתאמה מדויקת (Exact Match)
            exact_match = df_to_search[df_to_search['item_cat'] == category_filter]

            if len(exact_match) > 0:
                df_to_search = exact_match
                print(f"   ✅ Found exact match! ({len(df_to_search)} items)")
            else:
                # שלב ב': ניסיון להתאמה חלקית (Partial Match)
                print(f"   ⚠️ No exact match. Trying partial match...")

                # מנקים מילים כמו 'frame' ומנרמלים לאותיות קטנות
                # לדוגמה: 'Bed frame' יהפוך ל-'bed' וימצא את 'Double beds'
                search_term = category_filter.lower().replace("frame", "").replace("dining", "").strip()

                # חיפוש חלקי (מכיל את המילה)
                partial_match = df_to_search[
                    df_to_search['item_cat'].astype(str).str.lower().str.contains(search_term, regex=False)
                ]

                if len(partial_match) > 0:
                    df_to_search = partial_match
                    print(f"   ✅ Found partial match for '{search_term}'! ({len(df_to_search)} items)")
                else:
                    # שלב ג': כישלון בסינון
                    print(f"   ❌ Filter failed completely for '{category_filter}'.")
                    print("   💡 DEBUG: Here are the available categories in your CSV:")
                    # הדפסת הקטגוריות הקיימות כדי שתוכלי לתקן במידת הצורך
                    try:
                        print(sorted(self.embeddings_df['item_cat'].astype(str).unique()))
                    except:
                        print("Could not print categories.")

                    print("   --- Falling back to full database search ---")
                    # כאן הוא חוזר לחפש בהכל (זה מה שגרם לארונות להופיע, אבל לפחות נדע למה)

        # 3. חישוב דמיון ויזואלי
        product_vectors = np.array([v for v in df_to_search['vector'].values])
        similarities = self._calculate_similarities(query_vector, product_vectors)
        df_to_search['similarity'] = similarities

        # 4. חישוב עונש על גודל (Size Penalty)
        target_w, target_l = None, None

        # מנסים לחשב גודל רק אם יש תמונה
        if query_image_path:
            target_w, target_l = self.estimate_dimensions(query_image_path)

        def calculate_final_score(row):
            score = row['similarity']

            # אם אין מידות להשוואה, מחזירים ציון רגיל
            if target_w is None or pd.isna(row.get('width')):
                return score

            # חישוב עונש על חוסר התאמה
            diff_w = abs(row['width'] - target_w) / max(target_w, 1)
            diff_l = abs(row['length'] - target_l) / max(target_l, 1)
            penalty = (diff_w + diff_l) / 2

            # הפחתת הציון
            return score - (penalty * 0.4)

        df_to_search['final_score'] = df_to_search.apply(calculate_final_score, axis=1)

        # 5. מיון והחזרה
        top_results = df_to_search.sort_values('final_score', ascending=False).head(top_k).copy()

        print(f"✅ Returning {len(top_results)} recommendations")
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
        """ניהול שיחה עם Gemini Pro Vision."""
        try:
            img = Image.open(image_path)
            prompt_parts = [
                "You are CasAI, an expert interior designer. Analyze the image and answer the user's questions.",
                "Be helpful, concise, and professional. If the user asks in Hebrew, answer in Hebrew.",
                img
            ]
            history_text = "\nChat History:\n"
            for msg in messages:
                role = "User" if msg['role'] == "user" else "CasAI"
                history_text += f"{role}: {msg['content']}\n"

            prompt_parts.append(history_text)
            prompt_parts.append("\nCasAI (Your response):")

            response = self.gemini_model.generate_content(prompt_parts)
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "Sorry, there was a communication issue with the designer."

    def estimate_dimensions(self, image_path):
        """
        משתמש ב-Gemini להערכת מידות הרהיט מהתמונה.
        """
        if not self.gemini_model:
            return None, None

        try:
            img = Image.open(image_path)
            prompt = """
            Analyze the furniture in this image. 
            Based on standard furniture sizes and room proportions, estimate its:
            1. Width (in cm)
            2. Length/Depth (in cm)

            Return ONLY a JSON object like this, with no extra text: 
            {"width": 160, "length": 200}
            """
            response = self.gemini_model.generate_content(contents=[prompt, img])

            # חילוץ ה-JSON מתוך הטקסט
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                w = data.get('width')
                l = data.get('length')
                print(f"📏 Gemini estimated dimensions: {w}x{l} cm")
                return w, l

        except Exception as e:
            print(f"⚠️ Error estimating dimensions: {e}")

        return None, None