import os
import cv2
import numpy as np
import pandas as pd

# הגדרת סביבה למודל
os.environ["TF_USE_LEGACY_KERAS"] = "1"
from tf_keras.models import Model, load_model

# --- נתיבים ---
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR) # התיקייה הראשית (CasAI)

# מקור הנתונים (מה שהסקרייפר יצר)
CSV_PATH = os.path.join(THIS_DIR, "data", "ikea_il.csv")
IMAGE_DIR = os.path.join(THIS_DIR, "data", "ikea_il_images")

# יעד השמירה (תיקיית הנתונים של האפליקציה)
IKEADATA_DIR = os.path.join(PROJECT_ROOT, "data", "ikea-data")
OUTPUT_PKL = os.path.join(IKEADATA_DIR, "ikea_final_model0.pkl")

# מודל האימון
SIM_MODEL_PATH = os.path.join(THIS_DIR, "multilabel0")
EMBED_LAYER_NAME = "dense_4"

# יצירת תיקיית יעד אם לא קיימת
os.makedirs(IKEADATA_DIR, exist_ok=True)

# --- פונקציות ---

def load_similarity_model():
    print(f"🔁 Loading model from: {SIM_MODEL_PATH}")
    if not os.path.exists(SIM_MODEL_PATH):
        raise FileNotFoundError(f"Model path not found: {SIM_MODEL_PATH}")
        
    base_model = load_model(SIM_MODEL_PATH, compile=False)
    
    try:
        # חילוץ שכבת ה-Embedding
        embed_model = Model(
            inputs=base_model.input,
            outputs=base_model.get_layer(EMBED_LAYER_NAME).output,
        )
    except ValueError:
        print(f"Warning: Layer {EMBED_LAYER_NAME} not found. Using output.")
        embed_model = base_model

    return embed_model

def preprocess_for_predict(path):
    img = cv2.imread(path)
    if img is None:
        return None
    img = cv2.resize(img, (100, 100))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype("float32") / 255.0
    return np.expand_dims(img, axis=0)

def build_vectors():
    print(f"📄 Loading CSV: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found! Run ikea_scrape.py first.")

    df = pd.read_csv(CSV_PATH)
    model = load_similarity_model()
    
    vectors = []
    valid_rows = [] # נשמור רק שורות שהצלחנו לעבד

    print("⚙️  Generating vectors...")
    for idx, row in df.iterrows():
        img_file = row.get("image_file")
        img_path = os.path.join(IMAGE_DIR, str(img_file))

        if os.path.exists(img_path):
            img_array = preprocess_for_predict(img_path)
            if img_array is not None:
                vec = model.predict(img_array, verbose=0).flatten()
                vectors.append(vec)
                valid_rows.append(idx)
            else:
                # תמונה פגומה
                pass
        
        if idx % 100 == 0:
            print(f"   Processed {idx}/{len(df)}")

    # יצירת DataFrame חדש רק עם הצלחות
    final_df = df.loc[valid_rows].copy()
    final_df["vector"] = vectors
    
    # שמירה כ-pickle עבור האפליקציה
    final_df.to_pickle(OUTPUT_PKL)
    print(f"\n✅ Saved final data to: {OUTPUT_PKL}")

if __name__ == "__main__":
    build_vectors()