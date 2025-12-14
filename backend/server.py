from fileinput import filename
from typing import List, Dict, Any, Union
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import base64
import traceback 
import pandas as pd
from PIL import Image
from io import BytesIO # הועבר לכאן לצורך שימוש ב-generate_new_design
from flask import Flask, send_from_directory


# נתיבים: הוספת התיקייה הראשית לנתיב כדי לאפשר ייבוא מ-core, generator.py, וכו'.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- ייבוא מודלים ושירותים ---
from backend.models import ( 
    load_yolo_model,
    load_similarity_model,
    load_ikea_dataframe,
    get_detected_photos,
)
from core.recommender import Recommender 
import generator 


app = Flask(__name__)
# הגדרות CORS קריטיות לתקשורת עם React
CORS(app) 

# --- טעינת מודלים פעם אחת לזיכרון ---
yolo: Any
similarity_model: Any
ikea_df: Any

try:
    print("✨ Loading all models and database...")
    yolo = load_yolo_model()
    similarity_model = load_similarity_model()
    ikea_df = load_ikea_dataframe()
    
    # --- קריטי ליציבות: השעיית טעינת המודל הגנרטיבי הכבד! ---
    generator.yolo_model_gen, generator.sd_pipe_gen = generator.initialize_generative_models()
    
    # --- תיקון 404: יצירת התיקייה הציבורית ---
    os.makedirs('appdata/detect', exist_ok=True)
    
    print("✅ Models loaded successfully. (Generative AI suspended for stability)")
except Exception as e:
    print(f"🚨 CRITICAL ERROR: Failed to load models. Check your models.py and file paths. Error: {e}")
    yolo, similarity_model, ikea_df = None, None, None
    
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETECT_FOLDER = os.path.join(BASE_DIR, 'appdata', 'detect') 

# ודא שהתיקייה נוצרה
os.makedirs(DETECT_FOLDER, exist_ok=True)

# -------------------------------------------------------------
# 0. הגשת קבצים סטטיים - תיקון קריטי לבעיית התמונות הריקות ב-Frontend
# -------------------------------------------------------------
@app.route('/appdata/detect/<path:filename>')
def serve_detected_files(filename: str) -> Response:
    return send_from_directory(DETECT_FOLDER, filename)


# === פונקציה 2: מגישה את תמונות איקאה (החדשה) ===
# כאן אנחנו משתמשים בנתיב הזה
@app.route('/data/ikea_il_images/<path:filename>')
def serve_ikea_images(filename: str) -> Response:
    # מגדירים איפה התמונות נמצאות (על בסיס BASE_DIR שכבר יש לך למעלה)
    images_dir = os.path.join(BASE_DIR, 'data', 'ikea_il_images')
    
    return send_from_directory(images_dir, filename)

# -------------------------
# 1. בדיקה שהשרת פועל
# -------------------------
@app.get("/")
def home() -> Dict[str, str]:
    return {"status": "Backend is running!"}


# -------------------------
# 2. קבלת תמונה → זיהוי YOLO (Endpoint /detect)
# -------------------------
@app.post("/detect")
def detect() -> Union[Response, tuple[Response, int]]:
    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400
    if yolo is None:
        return jsonify({"error": "YOLO model not loaded"}), 500

    img = request.files["image"]
    
    os.makedirs("uploads", exist_ok=True)
    save_path = os.path.join("uploads", img.filename)
    img.save(save_path)

    try:
        # הפונקציה מחזירה רשימת אובייקטי זיהוי עם המפתח 'crop_url'
        detections: List[Dict[str, Union[str, float, List[int]]]] = get_detected_photos(save_path, yolo, save_dir='appdata/detect')
        
        print(f"DEBUG: Detections count: {len(detections)}")
        
        return jsonify(detections)
        
    except Exception as e:
        print(f"🚨 DETECTION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Detection failed internally: {e}"}), 500


# ------------------------------------------------------------------
# 3. יצירת הדמיה חדשה (Endpoint /generate_design)
# ------------------------------------------------------------------
@app.post("/generate_design")
def generate_new_design() -> Union[Response, tuple[Response, int]]:
    # הקלט מגיע מ-request.form (FormData)
    original_image_path: str = request.form.get("original_image_path", "")
    selected_crop_url: str = request.form.get("selected_crop_url", "")
    prompt: str = request.form.get("prompt", "")
    
    if not original_image_path or not prompt or not selected_crop_url:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # --- התיקון החדש: המרת URL לנתיב קובץ אמיתי ---
        
        # 1. חילוץ שם הקובץ בלבד (למשל 'crop_0.jpg') מתוך ה-URL הארוך
        crop_filename = os.path.basename(selected_crop_url)
        
        # 2. בניית הנתיב המלא באמצעות התיקייה שהגדרנו למעלה (DETECT_FOLDER)
        cleaned_crop_path = os.path.join(DETECT_FOLDER, crop_filename)

        # הדפסות בדיקה (כדי שתראה בטרמינל מה קורה)
        print(f"DEBUG: Original Path: {original_image_path}")
        print(f"DEBUG: Crop Path Target: {cleaned_crop_path}")

        # בדיקה שהקבצים באמת קיימים לפני ששולחים למודל
        if not os.path.exists(original_image_path):
             return jsonify({"error": f"Original image not found at: {original_image_path}"}), 500
             
        if not os.path.exists(cleaned_crop_path):
             return jsonify({"error": f"Crop image not found at: {cleaned_crop_path}"}), 500
        
        # --- מכאן ממשיך הקוד הרגיל שלך... ---
        generated_image_pil: Image.Image = generator.generate_design(
             original_image_path,
             cleaned_crop_path,
             prompt,
        )
        # ------------------------------------
        
        if generated_image_pil is None:
             raise Exception("Generative model failed to produce an image.")

        # המרת התמונה שנוצרה ל-Base64
        buffered = BytesIO()
        generated_image_pil.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return jsonify({"generated_image": img_str})

    except Exception as e:
        print(f"🚨 GENERATION ERROR: {e}")
        traceback.print_exc()
        # החזרת הודעת שגיאה מפורטת יותר
        return jsonify({"error": f"Image generation failed internally. Details: {e}"}), 500


# -------------------------
# 4. המלצות לאחר בחירת פריט (Endpoint /recommend/image)
# -------------------------

@app.post("/recommend/image")
def recommend_image() -> Union[Response, tuple[Response, int]]:
    if similarity_model is None or ikea_df is None:
        return jsonify({"error": "Model initialization failed"}), 500
        
    # --- חלק 1: לוגיקת זיהוי תמונה (ללא שינוי) ---
    selected_crop_url: str = request.form.get("crop_url", "")
    text: str = request.form.get("text", "")
    final_image_path: Union[str, None] = None
    
    if selected_crop_url:
        cleaned_path = selected_crop_url.replace("/", os.sep)
        if cleaned_path.startswith(os.sep): cleaned_path = cleaned_path[1:]
        if os.path.exists(cleaned_path):
            final_image_path = cleaned_path
        else:
            return jsonify({"error": "Selected crop file not found"}), 404
    elif "image" in request.files:
        if yolo is None: return jsonify({"error": "YOLO model not loaded"}), 500
        img = request.files["image"]
        os.makedirs("uploads", exist_ok=True)
        save_path = os.path.join("uploads", img.filename)
        img.save(save_path)
        detections = get_detected_photos(save_path, yolo, save_dir=DETECT_FOLDER)
        if detections: final_image_path = detections[0]["path"] 
        else: return jsonify({"error": "No furniture detected"}), 400
            
    # --- חלק 2: הפעלת המודל והכנת התשובה (התיקון כאן!) ---
    recommender = Recommender(similarity_model, ikea_df)
    results = recommender.recommend(
        query_text=text if text.strip() else None,
        query_image_path=final_image_path,
        top_k=10
    )

    # יצירת DataFrame חדש ונקי לשליחה
    final_df = pd.DataFrame()
    
    # העתקת שמות ומחירים
    final_df['item_name'] = results['item_name']
    final_df['item_price'] = results['item_price']
    
    # --- התיקון הקריטי: בניית נתיב התמונה ---
    # אנו בונים את הנתיב ידנית כדי לוודא שהוא נכון
    if 'image_file' in results.columns:
        final_df['item_img'] = results['image_file'].apply(lambda x: f"data/ikea_il_images/{x}")
    else:
        final_df['item_img'] = "" # שלא יקרוס

    # העתקת הקישור למוצר
    if 'product_link' in results.columns:
        final_df['item_url'] = results['product_link']
    else:
        final_df['item_url'] = ""

    # מילוי ערכים חסרים למניעת תקלות ב-JSON
    final_df = final_df.fillna("")
    
    print(f"DEBUG: Sending {len(final_df)} items. First image path: {final_df.iloc[0]['item_img']}")
    return jsonify(final_df.to_dict(orient="records"))


# -------------------------
# 5. קבלת טקסט → החזרת המלצות (/recommend/text)
# -------------------------
@app.post("/recommend/text")
def recommend_text() -> Union[Response, tuple[Response, int]]:
    data: Dict[str, str] = request.json # סביר להניח ש-React שולח JSON כאן
    query: str = data.get("query", "")

    if not query:
        return jsonify({"error": "query is required"}), 400
    if similarity_model is None or ikea_df is None:
        return jsonify({"error": "Model initialization failed"}), 500

    recommender = Recommender(similarity_model, ikea_df)
    results = recommender.recommend(query_text=query, top_k=10)

    # מחיקת עמודת הוקטורים לפני השליחה ל-Frontend
    if 'vector' in results.columns: 
        results = results.drop(columns=['vector'])

    return jsonify(results.to_dict(orient="records"))


# -------------------------
# הרצת השרת
# -------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)