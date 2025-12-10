"""Generative AI module for furniture redesign AND recommendations."""

import os
# הגדרת משתנה סביבה לתיקון בעיות הורדה
os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"

import sys
import numpy as np
import pickle
import torch
import cv2
from PIL import Image, ImageDraw
from ultralytics import YOLO
from diffusers import StableDiffusionInpaintPipeline, LCMScheduler, AutoencoderTiny

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# מנסים לייבא את המודולים הישנים (עבור החיפוש), אם הם קיימים
try:
    from core.config import get_style_description
    from core.models import ModelLoader
except ImportError:
    print("⚠️ Warning: 'core' modules not found. Search functionality might be limited.")
    ModelLoader = None

# ==========================================
# 1. הגדרות מערכת (System Configuration)
# ==========================================
CONFIG = {
    "DEVICE": "cuda" if torch.cuda.is_available() else "cpu",
    "REPO_DIR": 'ObjectDetectionProject-IKEAFurnituresRecommender',
    "EMBEDDINGS_FILE": 'furniture_embeddings.npy',
    "METADATA_FILE": 'furniture_metadata.pkl',
    "SEG_MODEL_PATH": "yolov8n-seg.pt"  # המודל החדש לזיהוי מדויק
}

# ==========================================
# 2. מודול חיפוש והמלצות (Recommender Module) - מהקובץ הישן
# ==========================================
def initialize_search_engine():
    """
    טוען את מודל החיפוש (CLIP) ואת בסיס הנתונים של איקאה.
    """
    print("📚 [Search] Loading CLIP model and Data...")
    
    if not ModelLoader:
        print("❌ ModelLoader not available.")
        return None, None, None

    # בדיקת התקנות והורדת דאטה
    if not os.path.exists(CONFIG['REPO_DIR']):
        print("📦 Cloning IKEA dataset...")
        os.system(f"git clone https://github.com/sophiachann/{CONFIG['REPO_DIR']}.git")

    model_loader = ModelLoader()
    model = model_loader.load_clip_model()
    
    # טעינת זיכרון
    if os.path.exists(CONFIG['EMBEDDINGS_FILE']):
        embeddings = np.load(CONFIG['EMBEDDINGS_FILE'])
        with open(CONFIG['METADATA_FILE'], 'rb') as f:
            metadata = pickle.load(f)
        print("✅ [Search] System Ready.")
    else:
        print("⚠️ Data missing! Please run indexing script first.")
        embeddings, metadata = None, None

    return model, embeddings, metadata

def get_recommendations(item_name, chosen_style, model, embeddings, metadata, top_k=4):
    """
    מבצע חיפוש רהיטים לפי טקסט.
    """
    if embeddings is None or model is None:
        return []
    
    style_desc = get_style_description(chosen_style) if 'get_style_description' in globals() else chosen_style
    full_query = f"{style_desc} {item_name}"
    print(f"🔍 [Search] Query: '{full_query}'")

    query_vec = model.encode(full_query)
    norm_data = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norm_query = np.linalg.norm(query_vec)
    similarities = np.dot(embeddings / norm_data, query_vec / norm_query)

    top_indices = np.argsort(similarities)[::-1][:50]
    raw_results = [(metadata[i], similarities[i]) for i in top_indices]
    
    # סינון שם הקובץ
    target = item_name.lower().rstrip('s')
    filtered = [r for r in raw_results if target in os.path.basename(r[0]).lower()]
    
    return filtered[:top_k] if filtered else raw_results[:top_k]

# ==========================================
# 3. מודול גנרטיבי חדש (Generative Module: YOLO + SD-LCM)
# ==========================================
def initialize_generative_models():
    """
    טוען את המודלים המהירים (Ultra-Fast) והמתוקנים.
    """
    print("\n--- [GenAI] Loading Generative Models ---")
    
    # 1. טעינת YOLO
    yolo_model = None
    try:
        yolo_model = YOLO(CONFIG['SEG_MODEL_PATH'])
        print("✅ YOLO Segmentation Loaded.")
    except Exception as e:
        print(f"❌ Failed to load YOLO: {e}")
        return None, None

    # 2. טעינת Stable Diffusion + TinyVAE + LCM
    sd_pipe = None
    try:
        # VAE מהיר
        fast_vae = AutoencoderTiny.from_pretrained("madebyollin/taesd", torch_dtype=torch.float32)

        # Pipeline ראשי
        sd_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            vae=fast_vae,              
            torch_dtype=torch.float32,
            safety_checker=None
        )
        
        # האצת LCM
        sd_pipe.load_lora_weights("latent-consistency/lcm-lora-sdv1-5")
        sd_pipe.scheduler = LCMScheduler.from_config(sd_pipe.scheduler.config)

        sd_pipe.to(CONFIG['DEVICE'])
        print("✅ Stable Diffusion (Ultra-Fast) Loaded.")
        
    except Exception as e:
        print(f"❌ Failed to load Stable Diffusion: {e}")
        return None, None
    
    return yolo_model, sd_pipe

def generate_new_furniture_design(image_path, prompt, yolo_model, sd_pipe):
    """
    הפונקציה המתוקנת: מזהה ספות (גם אם קוראים להן Couch) ומציירת מהר.
    """
    if not yolo_model or not sd_pipe:
        print("❌ Models not loaded correctly.")
        return None

    # --- שלב א: זיהוי וחיתוך ---
    print(f"🕵️ Detecting & Segmenting furniture in {image_path}...")
    results = yolo_model(image_path, conf=0.25, verbose=False)
    
    if not results or not results[0].masks:
        print("❌ No objects or masks detected.")
        return None

    # לוגיקה חכמה למילים נרדפות
    target_keywords = []
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["sofa", "couch", "divan", "loveseat"]):
        target_keywords = ['sofa', 'couch'] 
    elif any(word in prompt_lower for word in ["table", "desk", "counter"]):
        target_keywords = ['table', 'desk']
    elif any(word in prompt_lower for word in ["chair", "seat", "stool"]):
        target_keywords = ['chair', 'seat']
    elif any(word in prompt_lower for word in ["bed", "mattress"]):
        target_keywords = ['bed']
        
    print(f"🎯 Target keywords: {target_keywords if target_keywords else 'Auto-detect'}")

    best_mask = None
    max_area = 0
    names = yolo_model.names

    for i, mask_data in enumerate(results[0].masks.data):
        cls_id = int(results[0].boxes.cls[i])
        name = names[cls_id].lower()
        
        mask_np = mask_data.cpu().numpy()
        area = np.sum(mask_np)

        is_relevant = False
        if target_keywords:
            if any(k in name for k in target_keywords): is_relevant = True
        else:
            if name in ['sofa', 'couch', 'bed', 'chair', 'table']: is_relevant = True

        if is_relevant and area > max_area:
            max_area = area
            best_mask = results[0].masks.xy[i]
            print(f"   ✅ Selected: {name} (Area: {area:.0f})")

    if best_mask is None:
        print("⚠️ Target furniture not found.")
        return None

    # --- שלב ב: מסכה ---
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    mask_cv = np.zeros((h, w), dtype=np.uint8)
    polygon = np.array(best_mask, dtype=np.int32)
    cv2.fillPoly(mask_cv, [polygon], 255)
    kernel = np.ones((10, 10), np.uint8)
    mask_cv = cv2.dilate(mask_cv, kernel, iterations=1)
    mask = Image.fromarray(mask_cv, mode="L")
    
    # --- שלב ג: גנרציה (LCM) ---
    process_size = (512, 512) 
    img_resized = img.resize(process_size)
    mask_resized = mask.resize(process_size)

    print(f"⚡ Inpainting...")
    result = sd_pipe(
        prompt=f"{prompt}, high quality, realistic interior, extremely bright",
        image=img_resized,
        mask_image=mask_resized,
        num_inference_steps=8,
        guidance_scale=4.0,
        strength=0.99 
    ).images[0]

    return result.resize(img.size)

# ==========================================
# 4. התוכנית הראשית (Main) - בדיקה
# ==========================================
if __name__ == "__main__":
    
    print("⚠️ Test run is temporarily disabled (Production Mode).") 

    """
    # --- בדיקת חיפוש (Search Test) ---
    search_model, db_emb, db_meta = initialize_search_engine()
    if search_model:
        recs = get_recommendations("sofa", "industrial", search_model, db_emb, db_meta)
        print(f"Found recommendations: {len(recs)}")

    # --- בדיקת עיצוב (Design Test) ---
    yolo, sd = initialize_generative_models()
    if yolo and sd:
        test_img = "test_room.jpeg"
        if os.path.exists(test_img):
            res = generate_new_furniture_design(
                test_img, 
                "Green velvet sofa", 
                yolo, sd
            )
            if res: res.save("final_test.png")
    """