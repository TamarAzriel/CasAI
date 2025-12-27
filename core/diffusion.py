"""Furniture design generation using Google Gemini 2.5 Flash API."""

import os
import io
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
        prompt: Optional[str] = None,
        recommendation_image_path: Optional[str] = None,
        item_name: str = "furniture",
        save_path: Optional[str] = None
    ) -> Image.Image:
        """
        Generate a modified design image using Gemini 2.5 Flash.

        - Replaces the area defined by `crop_image_path` in the scene at
          `original_image_path` according to `prompt`.
        - Optionally uses `recommendation_image_path` as a visual reference.
        - Saves the resulting image to `save_path` and returns a PIL Image.
        
        Args:
            original_image_path: Path to original room image
            crop_image_path: Path to cropped furniture image
            save_path: Path to save the generated image
            prompt: Optional text prompt for generation
            recommendation_image_path: Optional path to reference image
            item_name: Name of furniture item
            
        Returns:
            Generated PIL Image
            
        Raises:
            FileNotFoundError: If input images don't exist
            RuntimeError: If generation fails
        """
        # Validate input files
        if not os.path.exists(original_image_path):
            raise FileNotFoundError(f"Original image not found: {original_image_path}")
        if not os.path.exists(crop_image_path):
            raise FileNotFoundError(f"Cropped image not found: {crop_image_path}")
        if recommendation_image_path and not os.path.exists(recommendation_image_path):
            raise FileNotFoundError(f"Recommendation image not found: {recommendation_image_path}")

        # Initialize client
        client = self._init_client()

        # Build prompt
        prompt_text = (
            prompt.strip() if prompt else f"Replace the {item_name} in the scene with a natural-looking {item_name}."
        )
        enhanced_prompt = (
            f"Create an image based on this room. Replace ONLY the {item_name} I uploaded according to this request: '")
        enhanced_prompt += prompt_text
        enhanced_prompt += (
            "'. Keep the rest of the room (walls, floor, lighting, and other objects) exactly the same. "
            "The new item should blend naturally into the scene."
        )

        original_buf = self._img_to_buffer(original_image_path)
        crop_buf = self._img_to_buffer(crop_image_path)

        contents = [enhanced_prompt, original_buf, crop_buf]

        rec_buf = self._img_to_buffer(recommendation_image_path)
        contents.append("Here is a reference for the style/color:")
        contents.append(rec_buf)

        print(f"--- [GENERATE] Sending request to Gemini 2.5 Flash for {item_name} ---")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=contents,
            )
        except Exception as e:
            print(f"❌ Error calling Gemini: {e}")
            raise RuntimeError(f"Generation failed: {e}")

        # Extract image from response
        generated_image = None
        for part in getattr(response, "parts", []):
            if getattr(part, "inline_data", None) is not None:
                generated_image = part.as_image()
                break

        if generated_image is None:
            # If Gemini returned only text, log and raise
            for part in getattr(response, "parts", []):
                if getattr(part, "text", None):
                    print(f"⚠️ Gemini returned text: {part.text}")
            raise RuntimeError("Gemini did not return an image part.")

        # Save image if save_path is provided
        if save_path:
            # Ensure destination directory exists
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)

            # If save_path is a directory, create a filename
            if os.path.isdir(save_path) or save_path.endswith(os.path.sep):
                save_path = os.path.join(save_path, f"generated_{item_name}.jpg")
            # If no extension provided, add .png
            if not os.path.splitext(save_path)[1]:
                save_path = save_path + f"_{item_name}.png"
    
            generated_image.save(save_path, format="JPEG", quality=95)
            print(f"✅ Design generated and saved to {save_path}")

    @staticmethod
    def _img_to_buffer(img_path: str) -> io.BytesIO:
        """Helper to convert PIL image to bytes buffer (PNG)."""
        img = Image.open(img_path)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    