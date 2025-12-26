"""Furniture design generation using Google Gemini 2.5 Flash API."""

import os
import io
from typing import Optional
from google.genai import types
from google import genai
from PIL import Image
from dotenv import load_dotenv


# Initialize Gemini client
def init_gemini_client():
    """Initialize Gemini client with API key from environment."""
    api_key = os.getenv("NanoBanana_API_KEY")
    if not api_key:
        raise ValueError("NanoBanana_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


def generate_design(
    original_image_path: str,
    crop_image_path: str,
    prompt: str = None,
    recommendation_image_path: str = None,
    item_name: str = "furniture",
    sd_pipe = None 
) -> Image.Image:
    """
    גרסה מעודכנת המשתמשת ב-Gemini 2.5 Flash (NanoBanana API)
    """
    load_dotenv()
    
    # 1. בדיקת קבצים
    if not os.path.exists(original_image_path):
        raise FileNotFoundError(f"Original image not found: {original_image_path}")

    # 2. אתחול ה-Client (הוספתי verify=False ליתר ביטחון בגלל בעיית ה-SSL שראינו)
    client = genai.Client(
        api_key=os.getenv("NanoBanana_API_KEY"),
    )

    # 3. בניית הפרומפט המשופר (כדי שגמני ישמור על שאר החדר)
    enhanced_prompt = (
        f"Create an image based on this room. Please replace ONLY the {item_name} "
        f"according to this request: '{prompt}'. "
        f"Keep the rest of the room (walls, floor, lighting, and other objects) exactly the same. "
        f"The new {item_name} should blend naturally into the scene."
    )

    # 4. הכנת התמונות למשלוח
    original_img = Image.open(original_image_path)
    contents = [enhanced_prompt, original_img]

    # אם יש תמונת המלצה, נוסיף גם אותה כרפרנס ויזואלי
    if recommendation_image_path and os.path.exists(recommendation_image_path):
        rec_img = Image.open(recommendation_image_path)
        contents.append("Here is a reference for the style/color:")
        contents.append(rec_img)

    print(f"--- [GENERATE] Sending request to Gemini 2.5 Flash for {item_name} ---")

    # 5. קריאה ל-API
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
        )
    except Exception as e:
        print(f"❌ Error calling Gemini: {e}")
        raise RuntimeError(f"Generation failed: {e}")

    # 6. שליפת התמונה מהתגובה והחזרתה
    generated_image = None
    for part in response.parts:
        if part.inline_data is not None:
            generated_image = part.as_image()
            # שמירה מקומית לגיבוי (אופציונלי)
            generated_image.save("last_generated_output.png")
            break
            
    if generated_image is None:
        # אם גמני החזיר רק טקסט (למשל הודעת שגיאה או סירוב)
        for part in response.parts:
            if part.text:
                print(f"⚠️ Gemini returned text: {part.text}")
        raise RuntimeError("Gemini did not return an image part.")

    print("✅ Design generated successfully!")
    return generated_image

def old_generate_design(
    original_image_path: str,
    crop_image_path: str,
    prompt: str = None,
    recommendation_image_path: str = None,
    item_name: str = "furniture",
    sd_pipe = None  # No longer used, kept for backwards compatibility
) -> Image.Image:
    """
    Generate a new furniture design using Google Gemini 2.5 Flash.
    
    Sends the original image with a description of the desired changes
    to Gemini, which generates an improved design.
    
    Args:
        original_image_path: Path to the original full image
        crop_image_path: Path to the selected crop image (for reference)
        prompt: Text prompt describing the desired design
        recommendation_image_path: Path to recommendation product image
        item_name: Name of the furniture item
        sd_pipe: Deprecated, not used
        
    Returns:
        PIL Image with the generated design
        
    Raises:
        FileNotFoundError: If image files don't exist
        RuntimeError: If generation fails
    """
    print(f"--- [GENERATE] Request received. Crop path: {crop_image_path} ---")
    
    # Verify files exist
    if not os.path.exists(original_image_path):
        raise FileNotFoundError(f"Original image not found at: {original_image_path}")
    
    if not os.path.exists(crop_image_path):
        raise FileNotFoundError(f"Crop image not found at: {crop_image_path}")
    
    if recommendation_image_path and not os.path.exists(recommendation_image_path):
        print(f"⚠️  Recommendation image not found, using text prompt instead")
        recommendation_image_path = None
    
    # Initialize Gemini client
    try:
        client = init_gemini_client()
    except ValueError as e:
        print(f"❌ Error: {e}")
        raise RuntimeError("Cannot initialize Gemini client") from e
    
    # Load original image
    original_image = Image.open(original_image_path).convert("RGB")
    
    print(f"DEBUG: Original Path: {original_image_path}")
    print(f"DEBUG: Crop Path: {crop_image_path}")
    if recommendation_image_path:
        print(f"DEBUG: Recommendation Image Path: {recommendation_image_path}")
    if prompt:
        print(f"DEBUG: User prompt: '{prompt}'")
    
    # Build the prompt for Gemini
    if recommendation_image_path:
        recommendation_img = Image.open(recommendation_image_path).convert("RGB")
        
        print(f"⚡ Using recommendation image as reference for: {item_name}")
        
        # Extract color from recommendation
        import numpy as np
        rec_array = np.array(recommendation_img)
        h, w = rec_array.shape[:2]
        center_region = rec_array[h//4:3*h//4, w//4:3*w//4]
        pixels = center_region.reshape(-1, 3)
        dominant_color = np.median(pixels, axis=0).astype(int)
        r, g, b = dominant_color
        
        # Determine color name
        color_name = "dark"
        if r < 100 and g < 100 and b < 100:
            color_name = "black"
        elif r > 200 and g > 150 and b < 100:
            color_name = "brown"
        elif r > 150 and g < 100 and b > 150:
            color_name = "purple"
        elif r > 200 and g > 180 and b < 100:
            color_name = "beige"
        elif r > 100 and g > 100 and b > 150:
            color_name = "blue"
        elif r > 100 and g > 150 and b < 100:
            color_name = "green"
        
        print(f"⚡ Detected color: {color_name} (RGB: {r}, {g}, {b})")
        
        gemini_prompt = (
            f"I have a room image. I want to change the {item_name} to match "
            f"this reference image (which shows a {color_name} {item_name}). "
            f"Please modify only the {item_name} in the room image to look like the reference, "
            f"while keeping everything else (walls, other furniture, lighting) the same. "
            f"Make the changes look natural and realistic."
        )
        
        print(f"⚡ Enhanced prompt: '{gemini_prompt}'")
        
        # Call Gemini with both images
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[
                    gemini_prompt,
                    types.Part(inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=_image_to_bytes(original_image)
                    )),
                    "Here's the reference image:",
                    types.Part(inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=_image_to_bytes(recommendation_img)
                    )),
                ],
            )
        except Exception as e:
            print(f"❌ Gemini generation failed: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}") from e
    else:
        # Use text prompt only
        gemini_prompt = (
            f"I have a room image. I want to change the {item_name} according to this description: '{prompt}'. "
            f"Please modify only the {item_name} in the room image based on the description, "
            f"while keeping everything else (walls, other furniture, lighting) the same. "
            f"Make the changes look natural and realistic."
        )
        
        print(f"⚡ Enhanced prompt: '{gemini_prompt}'")
        
        # Call Gemini with original image
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[
                    gemini_prompt,
                    types.Part(inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=_image_to_bytes(original_image)
                    )),
                ],
            )
        except Exception as e:
            print(f"❌ Gemini generation failed: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}") from e
    
    # Extract generated image from response
    generated_image = None
    for part in response.parts:
        if part.inline_data is not None:
            try:
                generated_image = part.as_image()
                break
            except Exception:
                continue
    
    if generated_image is None:
        # Try text response as fallback
        for part in response.parts:
            if part.text is not None:
                print(f"⚠️  Gemini returned text instead of image: {part.text}")
        raise RuntimeError("Gemini did not return a generated image")
    
    print("✅ Generation complete.")
    return generated_image


def _image_to_bytes(image: Image.Image) -> bytes:
    """Convert PIL Image to JPEG bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def load_diffusion_model():
    """
    Deprecated: No longer needed with Gemini API.
    
    Returns None for backwards compatibility.
    """
    print("⚠️  load_diffusion_model() is deprecated. Using Gemini API instead.")
    return None

