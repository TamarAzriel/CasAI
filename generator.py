"""Generative AI module for furniture redesign using YOLO-Segmentation and Stable Diffusion."""

import os
# הגדרת משתנה סביבה כדי לעקוף בעיות SSL בהורדה של Hugging Face
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"

import sys
import numpy as np
import torch
import cv2
from PIL import Image
from ultralytics import YOLO
from diffusers import StableDiffusionInpaintPipeline, LCMScheduler, AutoencoderTiny

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# 1. הגדרות מערכת
# ==========================================
CONFIG = {
    "DEVICE": "cuda" if torch.cuda.is_available() else "cpu",
    "SEG_MODEL_PATH": "yolov8n-seg.pt"  # המודל שמחזיר צלליות מדויקות
}

# ==========================================
# 2. מודול גנרטיבי (Generative Module)
# ==========================================
def initialize_generative_models():
    """
    טוען את המודלים בצורה חכמה שעוקפת שגיאות VAE ואופטימיזציות למהירות.
    """
    print("\n--- 1. Script Started ---") 
    print("🎨 [GenAI] Loading Ultra-Fast Models...")
    
    # 1. טעינת YOLO
    yolo_model = None
    try:
        yolo_model = YOLO(CONFIG['SEG_MODEL_PATH'])
        print("✅ YOLO Segmentation Loaded.")
    except Exception as e:
        print(f"❌ Failed to load YOLO: {e}")
        return None, None

    # 2. טעינת Stable Diffusion + TinyVAE (בשיטה חדשה לעקיפת שגיאות)
    sd_pipe = None
    try:
        # טוען את המפענח המהיר (Tiny VAE) ראשון
        fast_vae = AutoencoderTiny.from_pretrained(
            "madebyollin/taesd", 
            torch_dtype=torch.float32
        )

        # טעינת הצינור הראשי תוך הזרקת ה-VAE המהיר *מיד*
        sd_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            vae=fast_vae,              
            torch_dtype=torch.float32,
            safety_checker=None
        )
        
        # הזרקת LCM למהירות
        sd_pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
        sd_pipe.scheduler = LCMScheduler.from_config(sd_pipe.scheduler.config)

        sd_pipe.to(CONFIG['DEVICE'])
        print("✅ Stable Diffusion (Ultra-Fast) Loaded.")
        
    except Exception as e:
        print(f"❌ Failed to load Stable Diffusion: {e}")
        return None, None
    
    print("--- 2. Models Loaded ---") 

    return yolo_model, sd_pipe

def generate_new_furniture_design(image_path, prompt, yolo_model, sd_pipe):
    """
    מקבל תמונה, מוצא רהיט (צללית מדויקת), ומצייר עליו מחדש בשיא המהירות.
    """
    if not yolo_model or not sd_pipe:
        print("❌ Models not loaded correctly.")
        return None

    # --- שלב א: זיהוי וחיתוך (YOLO Segmentation) ---
    print(f"🕵️ Detecting & Segmenting furniture...")
    
    # הוספתי conf=0.25 כדי לוודא שהוא לא מפספס דברים בגלל ביטחון נמוך
    results = yolo_model(image_path, conf=0.25, verbose=False)
    
    if not results or not results[0].masks:
        print("❌ No objects or masks detected.")
        return None

    # *** לוגיקה מתוקנת: שימוש ברשימת מילים נרדפות ***
    target_keywords = [] # רשימת המילים שהמודל יחפש
    prompt_lower = prompt.lower()
    
    # 1. ספה / כורסה (חשוב: הוספנו את couch לרשימת המטרות)
    if any(word in prompt_lower for word in ["sofa", "couch", "divan", "loveseat"]):
        target_keywords = ['sofa', 'couch'] 
    # 2. שולחן
    elif any(word in prompt_lower for word in ["table", "desk", "counter", "stand"]):
        target_keywords = ['table', 'desk']
    # 3. כיסא
    elif any(word in prompt_lower for word in ["chair", "armchair", "stool", "ottoman"]):
        target_keywords = ['chair', 'seat']
    # 4. מיטה
    elif any(word in prompt_lower for word in ["bed", "mattress", "futon"]):
        target_keywords = ['bed']
        
    print(f"🎯 Target keywords based on prompt: {target_keywords if target_keywords else 'Any big furniture'}")
    
    
    best_mask = None
    max_area = 0
    names = yolo_model.names

    for i, mask_data in enumerate(results[0].masks.data):
        cls_id = int(results[0].boxes.cls[i])
        name = names[cls_id].lower()
        
        # --- תוספת לדיבוג: נראה בדיוק מה המודל מוצא ---
        conf = float(results[0].boxes.conf[i])
        print(f"   👁️ Found object: '{name}' (Confidence: {conf:.2f})")
        # ---------------------------------------------

        mask_np = mask_data.cpu().numpy()
        area = np.sum(mask_np)

        is_relevant = False
        
        # בדיקה האם השם שהמודל מצא נמצא ברשימת המטרות שלנו
        if target_keywords:
            if any(keyword in name for keyword in target_keywords): 
                is_relevant = True
        else:
            # Fallback: אם לא זיהינו כלום בפרומפט, קח רהיטים גדולים
            if name in ['sofa', 'couch', 'bed', 'chair', 'table', 'dining table']:
                is_relevant = True

        if is_relevant:
            # אם מצאנו רהיט רלוונטי, נבדוק אם הוא הכי גדול שמצאנו עד כה
            if area > max_area:
                max_area = area
                best_mask = results[0].masks.xy[i]
                print(f"      ✅ Selected candidate: {name} (New max area)")

    if best_mask is None:
        print("⚠️ Target furniture not found. Try simplifying the prompt or using a clearer image.")
        return None

    # --- שלב ב: הכנת מסיכה בינארית מדויקת ---
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    mask_cv = np.zeros((h, w), dtype=np.uint8)
    polygon = np.array(best_mask, dtype=np.int32)
    cv2.fillPoly(mask_cv, [polygon], 255)
    
    kernel = np.ones((10, 10), np.uint8)
    mask_cv = cv2.dilate(mask_cv, kernel, iterations=1)
    mask = Image.fromarray(mask_cv, mode="L")
    
    mask.save("debug_mask.png")

    # --- שלב ג: גנרציה סופר-אגרסיבית (LCM) ---
    process_size = (512, 512) 
    img_resized = img.resize(process_size)
    mask_resized = mask.resize(process_size)

    print(f"⚡ Inpainting...")
    result = sd_pipe(
        prompt=f"{prompt}, high quality, realistic interior, extremely bright, clean, highly detailed",
        image=img_resized,
        mask_image=mask_resized,
        num_inference_steps=8,
        guidance_scale=5.0,
        strength=0.99 
    ).images[0]

    return result.resize(img.size)
# ==========================================
# בדיקה מקומית (Main)
# ==========================================
# ==========================================
# בדיקה מקומית (Main)
# ==========================================
if __name__ == "__main__":
    
    print("⚠️ Test run is temporarily disabled.") 

    """  <-- התחלת ההערה כאן
    
    yolo, sd = initialize_generative_models()
    
    if yolo and sd:
        test_img = "test_room.jpeg"
        
        if os.path.exists(test_img):
            print(f"✅ Found input image: {test_img}")
            
            prompt = "Deep forest green velvet sofa, brass legs, Midcentury style" 
            print(f"🚀 Generating new design with prompt: '{prompt}'")
            
            res = generate_new_furniture_design(test_img, prompt, yolo, sd)
            
            if res:
                output_filename = "redesigned_room_final.png"
                res.save(output_filename)
                print(f"\n✨ Done! Image saved as: {output_filename}")
            else:
                print("\n⚠️ Generation failed in the final step.")
        else:
            print(f"\n❌ ERROR: Input image '{test_img}' not found.")
            print("💡 Tip: Make sure you have a file named 'test_room.jpeg' in the same folder.")

    """  # <-- סיום ההערה כאן