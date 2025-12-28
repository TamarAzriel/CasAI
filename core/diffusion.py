"""Furniture design generation using Google Gemini 2.5 Flash API."""

import os
import io
import traceback
from typing import Optional
from google.genai import types
from google import genai
from PIL import Image
from dotenv import load_dotenv


class DesignGenerationService:
    """Service for generating furniture designs using Google Gemini 2.5 Flash API."""
    
    def __init__(self):
        """Initialize the design generation service."""
        load_dotenv()
        api_key = os.getenv("NanoBanana_API_KEY")
        if not api_key:
            raise ValueError("NanoBanana_API_KEY not found in environment variables")
        self._client = genai.Client(api_key=api_key)
    
    def generate_design(
        self,
        original_image_path: str,
        crop_image_path: str,
        recommendation_image_path: str, # הפכנו את זה לחובה, כי הלוגיקה החדשה חייבת המלצה
        prompt: Optional[str] = None,
        item_name: str = "furniture",
        save_path: Optional[str] = None
    ) -> Optional[Image.Image]:
        
        print(f"--- [START] Generating design combining 3 images ---")
        
        try:
            # 1. פתיחת שלוש התמונות (במקום person1, person2...)
            # אלו התמונות האמיתיות מהמערכת שלך
            print("📂 Loading images...")
            img_original = Image.open(original_image_path)
            img_crop = Image.open(crop_image_path)
            
            # וידוא שתמונת ההמלצה קיימת לפני שפותחים
            if not os.path.exists(recommendation_image_path):
                 raise FileNotFoundError(f"Recommendation image not found at: {recommendation_image_path}")
            img_recommendation = Image.open(recommendation_image_path)

            # 2. הגדרת הפרומפט (ההוראה למודל)
            # אנחנו אומרים לו במפורש: קח את החדר, תזהה את מה שיש בקרופ, ותחליף אותו במה שיש בהמלצה.
            user_description = prompt if (prompt and prompt.strip()) else f"a new {item_name}"

            final_prompt = (
                f"In the original room image, please replace the object shown in the crop image "
                f"with the following: {user_description}. "
                f"Use the recommendation image as a reference for the exact style and design. "
                f"Ensure the result integrates naturally with the room's lighting, shadows, and perspective."
            )
            print(f"📝 Prompt instruction: {final_prompt}")

            # 3. בניית רשימת התוכן (Contents)
            # זה החלק הקריטי - שולחים את הטקסט ואת כל שלוש התמונות יחד
            contents = [
                final_prompt,          # ההוראה המילולית
                img_original,          # תמונת החדר המלאה (הקשר)
                img_crop,              # האובייקט שצריך להחליף (הישן)
                img_recommendation     # האובייקט החדש מאיקאה
            ]

            # הגדרות איכות
            aspect_ratio = "4:3" 
            resolution = "2K"

            print("🚀 Sending request to Gemini (this might take a moment)...")
            
            # 4. שליחת הבקשה (בדיוק כמו בקוד הדוגמה)
            # שיניתי ל-gemini-2.0-flash כי הוא היציב ביותר כרגע שעובד לך
            response = self._client.models.generate_content(
                model="gemini-3-pro-image-preview", 
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'], # מבקש גם טקסט וגם תמונה
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=resolution
                    ),
                )
            )

            # 5. עיבוד התשובה ושמירה (כמו בלולאת ה-for בדוגמה)
            generated_image = None
            if response.parts:
                for part in response.parts:
                    # אם המודל החזיר טקסט הסבר, נדפיס אותו
                    if part.text is not None:
                         print(f"💬 Gemini says: {part.text}")
                    
                    # אם המודל החזיר תמונה (בעזרת אופרטור הוולרוס :=)
                    elif image := part.as_image():
                        generated_image = image
                        
                        if save_path:
                            # וידוא שהתיקייה קיימת לפני השמירה
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            # שמירת הקובץ (במקום "office.png")
                            generated_image.save(save_path)
                            print(f"✅ Image saved successfully to: {save_path}")
                        
                        return generated_image # מחזירים את אובייקט התמונה
            else:
                 # אם הגענו לכאן, גוגל חסם את הבקשה (בדרך כלל בטיחות)
                 print("⚠️ Gemini blocked the request or returned empty parts (check safety filters).")
                 return None

        except FileNotFoundError as e:
             print(f"❌ Image file not found error: {e}")
             raise
        except Exception as e:
            print(f"❌ Error during generation process:")
            # הדפסת שגיאה מלאה כדי שנבין מה קרה
            traceback.print_exc()
            raise RuntimeError(f"Generation failed: {e}")