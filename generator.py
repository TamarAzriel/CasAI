import os
import glob
import numpy as np
import pickle
import torch
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO
from diffusers import StableDiffusionInpaintPipeline

# ==========================================
# 1. הגדרות מערכת (Configuration)
# ==========================================
CONFIG = {
    "DEVICE": "cuda" if torch.cuda.is_available() else "cpu",
    "YOLO_PATH": "yolo-train/best.onnx", # וודאי שהנתיב נכון!
    "REPO_DIR": 'ObjectDetectionProject-IKEAFurnituresRecommender',
    "EMBEDDINGS_FILE": 'furniture_embeddings.npy',
    "METADATA_FILE": 'furniture_metadata.pkl'
}

STYLE_DEFINITIONS = {
    "asian": "black wood structure, bamboo texture, red accents, minimalist",
    "industrial": "black metal frame, dark rustic wood, vintage leather, concrete",
    "scandinavian": "light blonde wood, white color, light grey fabric, clean lines",
    "modern": "high gloss white finish, glass, chrome metal, geometric lines",
    "boho": "rattan, colorful textiles, plants, eclectic patterns"
}

# ==========================================
# 2. מודול חיפוש והמלצות (Recommender Module)
# ==========================================
def initialize_search_engine():
    """
    טוען את מודל החיפוש (CLIP) ואת בסיס הנתונים של איקאה.
    """
    print("📚 [Search] Loading CLIP model and Data...")
    
    # בדיקת התקנות והורדת דאטה (כמו בקוד הקודם)
    if not os.path.exists(CONFIG['REPO_DIR']):
        print("📦 Cloning IKEA dataset...")
        os.system(f"git clone https://github.com/sophiachann/{CONFIG['REPO_DIR']}.git")

    model = SentenceTransformer('clip-ViT-B-32')
    
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
    if embeddings is None: return []
    
    style_desc = STYLE_DEFINITIONS.get(chosen_style.lower(), "")
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
# 3. מודול גנרטיבי (Generative Module: YOLO + SD)
# ==========================================
def initialize_generative_models():
    """
    טוען את YOLO ו-Stable Diffusion פעם אחת לזיכרון.
    """
    print("🎨 [GenAI] Loading Generative Models (This may take time)...")
    
    # 1. טעינת YOLO
    yolo_model = None
    try:
        yolo_model = YOLO(CONFIG['YOLO_PATH'])
        print("✅ YOLO Loaded.")
    except Exception as e:
        print(f"❌ Failed to load YOLO: {e}")

    # 2. טעינת Stable Diffusion
    sd_pipe = None
    try:
        sd_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            torch_dtype=torch.float32, # לשיפור ביצועים ב-GPU אפשר float16
            safety_checker=None
        ).to(CONFIG['DEVICE'])
        print("✅ Stable Diffusion Loaded.")
    except Exception as e:
        print(f"❌ Failed to load Stable Diffusion: {e}")

    return yolo_model, sd_pipe

def generate_new_furniture_design(image_path, prompt, yolo_model, sd_pipe):
    """
    מקבל תמונה, מוצא רהיט, ומצייר עליו מחדש לפי הפרומפט.
    """
    if not yolo_model or not sd_pipe:
        print("❌ Models not loaded correctly.")
        return None

    # --- שלב א: זיהוי ומסיכה (YOLO) ---
    print(f"🕵️ [GenAI] Detecting furniture in {image_path}...")
    results = yolo_model(image_path)
    
    if not results or len(results[0].boxes) == 0:
        print("❌ No objects detected.")
        return None

    target_furniture = ['sofa', 'couch', 'bed', 'chair', 'table']
    best_box = None
    max_area = 0

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        name = yolo_model.names[cls_id].lower()
        x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0]
        area = (x2 - x1) * (y2 - y1)
        
        if name in target_furniture and area > max_area:
            max_area = area
            best_box = (x1, y1, x2, y2)

    if not best_box:
        print("⚠️ Found objects but not target furniture.")
        return None

    # יצירת המסכה
    img = Image.open(image_path).convert("RGB")
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    bx1, by1, bx2, by2 = best_box
    draw.rectangle((bx1-10, by1-10, bx2+10, by2+10), fill=255)

    # --- שלב ב: יצירה (Stable Diffusion) ---
    full_prompt = f"a high quality {prompt}, interior design, realistic, 4k"
    neg_prompt = "low quality, messy, bad anatomy, text, watermark"
    print(f"🖌️ [GenAI] Inpainting: '{full_prompt}'...")

    # Resize ל-512x512 לעבודה תקינה של המודל
    w, h = 512, 512
    img_resized = img.resize((w, h))
    mask_resized = mask.resize((w, h))

    result = sd_pipe(
        prompt=full_prompt,
        negative_prompt=neg_prompt,
        image=img_resized,
        mask_image=mask_resized,
        num_inference_steps=25,
        strength=0.9,
        guidance_scale=7.5
    ).images[0]

    return result.resize(img.size)

# ==========================================
# 4. התוכנית הראשית (Main)
# ==========================================
if __name__ == "__main__":
    # --- חלק 1: אתחול המערכות ---
    # נטען את מנוע החיפוש
    search_model, db_emb, db_meta = initialize_search_engine()
    
    # נטען את מנוע הגנרציה (רק אם צריך לעצב מחדש)
    # yolo, sd_pipe = initialize_generative_models() 

    # --- חלק 2: דוגמה לחיפוש רהיט ---
    print("\n--- 1. Recommending Furniture ---")
    recs = get_recommendations("sofa", "industrial", search_model, db_emb, db_meta)
    if recs:
        print(f"Found {len(recs)} recommendations. Best match: {recs[0][0]}")
    
    # --- חלק 3: דוגמה לעיצוב חדר מחדש ---
    # הערה: בטל את ההערה למטה רק אם יש לך את הקובץ 'test_room.jpg' ואת מודל ה-YOLO מאומן
    """
    print("\n--- 2. Redesigning Room ---")
    yolo, sd_pipe = initialize_generative_models() # טעינה כבדה
    
    new_room = generate_new_furniture_design(
        image_path="test_room.jpg",
        prompt="modern yellow velvet sofa",
        yolo_model=yolo,
        sd_pipe=sd_pipe
    )
    
    if new_room:
        new_room.save("redesigned_room.png")
        new_room.show()
    """