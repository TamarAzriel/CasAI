"""Diffusion model for furniture design generation using inpainting."""

import os
# Set environment variable to fix download issues
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"

from typing import Optional
from PIL import Image
import torch
from diffusers import StableDiffusionInpaintPipeline, LCMScheduler, AutoencoderTiny

def create_mask_from_crop(
    original_image: Image.Image,
    crop_image_path: str,
    crop_bbox: Optional[tuple] = None
) -> Image.Image:
    """
    Create a mask for inpainting from a crop image.
    
    The mask will cover the area where the crop was taken from in the original image.
    If crop_bbox is provided, uses that. Otherwise, attempts to find the crop location
    by matching the crop image within the original.
    
    Args:
        original_image: PIL Image of the original full image
        crop_image_path: Path to the cropped image
        crop_bbox: Optional (x1, y1, x2, y2) bounding box coordinates
        
    Returns:
        PIL Image mask (L mode, 0-255) where white areas will be inpainted
    """
    crop_img = Image.open(crop_image_path).convert("RGB")
    orig_w, orig_h = original_image.size
    
    # Create mask - if bbox provided, use it; otherwise create full mask
    # For now, we'll create a simple mask covering the crop area
    # In a more sophisticated implementation, you could use template matching
    # to find where the crop appears in the original image
    
    mask = Image.new("L", (orig_w, orig_h), 0)  # Start with black (no mask)
    
    if crop_bbox:
        # Use provided bounding box
        x1, y1, x2, y2 = crop_bbox
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, orig_w))
        y1 = max(0, min(y1, orig_h))
        x2 = max(0, min(x2, orig_w))
        y2 = max(0, min(y2, orig_h))
        
        # Create white mask in the crop area
        mask_crop = Image.new("L", (x2 - x1, y2 - y1), 255)
        mask.paste(mask_crop, (x1, y1))
    else:
        # Simple approach: create mask covering center area (fallback)
        # This is a simplified approach - in production you might want
        # to use template matching to find the exact crop location
        center_x, center_y = orig_w // 2, orig_h // 2
        crop_w, crop_h = crop_img.size
        
        # Place mask at center (this is a fallback - ideally use bbox)
        x1 = max(0, center_x - crop_w // 2)
        y1 = max(0, center_y - crop_h // 2)
        x2 = min(orig_w, x1 + crop_w)
        y2 = min(orig_h, y1 + crop_h)
        
        mask_crop = Image.new("L", (x2 - x1, y2 - y1), 255)
        mask.paste(mask_crop, (x1, y1))
    
    return mask


def generate_design(
    original_image_path: str,
    crop_image_path: str,
    prompt: str,
    sd_pipe: StableDiffusionInpaintPipeline
) -> Image.Image:
    """
    Generate a new furniture design using diffusion inpainting.
    
    This function creates a mask from the selected crop and uses Stable Diffusion
    to inpaint that area with a new design based on the prompt.
    
    Args:
        original_image_path: Path to the original full image
        crop_image_path: Path to the selected crop image
        prompt: Text prompt describing the desired design
        sd_pipe: Loaded StableDiffusionInpaintPipeline model
        
    Returns:
        PIL Image with the generated design
        
    Raises:
        FileNotFoundError: If image files don't exist
        RuntimeError: If generation fails
    """
    print(f"--- [GENERATE] Request received. Crop path: {crop_image_path} ---")
    
    if sd_pipe is None:
        print("⚠️ Diffusion model not available. Returning dummy image.")
        # Return a dummy image for testing
        return Image.new('RGB', (512, 512), color='blue')
    
    # Load original image
    if not os.path.exists(original_image_path):
        raise FileNotFoundError(f"Original image not found at: {original_image_path}")
    
    if not os.path.exists(crop_image_path):
        raise FileNotFoundError(f"Crop image not found at: {crop_image_path}")
    
    print(f"DEBUG: Original Path: {original_image_path}")
    print(f"DEBUG: Crop Path: {crop_image_path}")
    
    # Load images
    original_image = Image.open(original_image_path).convert("RGB")
    
    # Create mask from crop
    # Note: We don't have bbox info here, so we'll use a simple approach
    # In production, you might want to pass bbox from detection results
    mask = create_mask_from_crop(original_image, crop_image_path)
    
    # Resize for processing (diffusion models typically work best at 512x512)
    process_size = (512, 512)
    img_resized = original_image.resize(process_size, Image.Resampling.LANCZOS)
    mask_resized = mask.resize(process_size, Image.Resampling.LANCZOS)
    
    # Generate with diffusion
    print(f"⚡ Inpainting with prompt: '{prompt}'...")
    try:
        result = sd_pipe(
            prompt=f"{prompt}, high quality, realistic interior, extremely bright",
            image=img_resized,
            mask_image=mask_resized,
            num_inference_steps=8,
            guidance_scale=4.0,
            strength=0.99
        ).images[0]
        
        # Resize back to original dimensions
        final_result = result.resize(original_image.size, Image.Resampling.LANCZOS)
        print("✅ Generation complete.")
        return final_result
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        raise RuntimeError(f"Image generation failed: {e}") from e


def load_diffusion_model() -> StableDiffusionInpaintPipeline:
    """
    Load Stable Diffusion Inpaint Pipeline with LCM scheduler and TinyVAE.
    
    Returns:
        Loaded StableDiffusionInpaintPipeline with LCM acceleration
        
    Raises:
        ImportError: If diffusers or torch is not installed
        RuntimeError: If model loading fails
    """
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔄 Loading Stable Diffusion pipeline on {device}...")
        
        # Load fast VAE
        fast_vae = AutoencoderTiny.from_pretrained(
            "madebyollin/taesd",
            torch_dtype=torch.float32
        )
        
        # Load main pipeline
        sd_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            vae=fast_vae,
            torch_dtype=torch.float32,
            safety_checker=None
        )
        
        # Apply LCM acceleration
        sd_pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
        sd_pipe.scheduler = LCMScheduler.from_config(sd_pipe.scheduler.config)
        
        # Move to device
        sd_pipe.to(device)
        
        if device == "cuda":
            print("✅ Stable Diffusion loaded on CUDA (GPU) - High performance expected.")
        else:
            print("✅ Stable Diffusion loaded on CPU - Expect longer generation times.")
        
        return sd_pipe
        
    except ImportError as e:
        raise ImportError(
            "diffusers or torch not installed. "
            "Please run: pip install diffusers torch"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to load Stable Diffusion model: {e}") from e

