import os
import glob
import numpy as np
import pickle
import matplotlib.pyplot as plt
from PIL import Image
from sentence_transformers import SentenceTransformer

# --- חלק 1: הגדרות והתקנות (Settings) ---
STYLE_DEFINITIONS = {
    "asian": "black wood structure, bamboo texture, red accents, paper texture, dark brown timber, minimalist square shapes",
    "beach": "light birch wood, rattan and wicker material, white painted wood, beige linen fabric, sand colors, light oak",
    "contemporary": "curved furniture lines, smooth grey fabric, white and beige, round shapes, matte finish, soft texture",
    "craftsman": "solid oak wood, thick vertical slats, dark brown timber, sturdy rectangular structure, natural wood grain",
    "eclectic": "colorful fabric, velvet texture, mixed patterns, bright yellow or red or blue, unique asymmetric shape",
    "farmhouse": "white painted wood, solid pine top, black metal cup handles, beige fabric, shaker style doors, rustic white",
    "industrial": "black metal frame, dark rustic wood, vintage leather, concrete texture, wire mesh, rivets, dark grey",
    "mediterranean": "warm terracotta and orange colors, black wrought iron, dark rustic wood, heavy solid structure",
    "midcentury": "walnut wood texture, tapered wooden legs, mustard yellow or olive green fabric, curved plywood, teak veneer",
    "modern": "high gloss white finish, clear glass, chrome metal, sharp geometric lines, black and white monochrome, plastic",
    "rustic": "solid pine wood, natural wood grain with knots, brown wood stain, rough timber surface, heavy wood construction",
    "scandinavian": "light blonde wood, birch or pine, white color, light grey fabric, simple clean lines, plywood texture",
    "classic": "dark brown wood veneer, panel doors with glass, classic metal handles, beige upholstery, formal shape",
    "transitional": "grey fabric, dark wood legs, simple classic shape, neutral beige tones, clean finish",
    "tropical": "natural rattan structure, cane webbing, green leaf patterns, bamboo, dark exotic wood"
}

# --- חלק 2: פונקציה ראשונה - אתחול וטעינת זיכרון (Embedding) ---
def initialize_search_engine():
    """
    בודקת התקנות, מורידה דאטה, טוענת מודל ויוצרת/טוענת embeddings.
    מחזירה: (model, embeddings, metadata)
    """
    # 1. התקנות רק אם צריך
    try:
        import sentence_transformers
    except ImportError:
        print("🛠️ Installing libraries...")
        os.system('pip install sentence-transformers pillow numpy -q')

    # 2. הורדת הדאטה
    if not os.path.exists('ObjectDetectionProject-IKEAFurnituresRecommender'):
        print("📦 Cloning IKEA dataset...")
        os.system('git clone https://github.com/sophiachann/ObjectDetectionProject-IKEAFurnituresRecommender.git')

    # 3. נתיבים
    REPO_DIR = 'ObjectDetectionProject-IKEAFurnituresRecommender'
    IMAGES_ROOT_PATH = os.path.join(REPO_DIR, 'ikea', 'ikea-data')
    EMBEDDINGS_FILE = 'furniture_embeddings.npy'
    METADATA_FILE = 'furniture_metadata.pkl'

    print("🤖 Loading CLIP model...")
    model = SentenceTransformer('clip-ViT-B-32')

    # 4. בדיקת זיכרון (Cache)
    if os.path.exists(EMBEDDINGS_FILE) and os.path.exists(METADATA_FILE):
        print("✅ Found saved index! Loading...")
        embeddings = np.load(EMBEDDINGS_FILE)
        with open(METADATA_FILE, 'rb') as f:
            metadata = pickle.load(f)
    else:
        print("⚠️ Building Index (First run only)...")
        image_paths = glob.glob(os.path.join(IMAGES_ROOT_PATH, '**', '*.jpg'), recursive=True) + \
                      glob.glob(os.path.join(IMAGES_ROOT_PATH, '**', '*.jpeg'), recursive=True)
        
        new_embeddings = []
        new_metadata = []

        for i, img_path in enumerate(image_paths):
            try:
                img = Image.open(img_path).convert('RGB')
                new_embeddings.append(model.encode(img))
                new_metadata.append(img_path)
            except Exception as e:
                pass
            
            if i > 0 and i % 100 == 0:
                print(f"Processed {i}/{len(image_paths)}...")

        embeddings = np.array(new_embeddings)
        metadata = new_metadata

        # שמירה
        np.save(EMBEDDINGS_FILE, embeddings)
        with open(METADATA_FILE, 'wb') as f:
            pickle.dump(metadata, f)
        print("✅ Indexing Complete!")

    return model, embeddings, metadata