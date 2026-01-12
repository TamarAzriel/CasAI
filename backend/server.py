"""Flask backend server for CasAI application."""

import sys
from typing import Union
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import base64
import traceback
import pandas as pd
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from google import genai
from google.genai import types

# טעינת משתני סביבה
load_dotenv()

# הגדרת ה-Client של ג'מיני החדש
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("AIChat_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

# מודל גלובלי לשימוש בפונקציות עזר
GEMINI_MODEL = 'gemini-2.5-flash'

from core.models import ModelLoader
from core.config import (
    DETECT_DIR,
    UPLOADS_DIR,
    IMAGES_DIR,
    GENERATED_DIR,
    ensure_directories,
    url_to_file_path,
    PROJECT_ROOT,
)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

ensure_directories()

# Load services
try:
    detection_service = ModelLoader.load_detection_service()
    recommendation_service = ModelLoader.load_recommendation_service()
    generation_service = ModelLoader.load_generation_service()
    print("Detection and recommendation services loaded successfully.")
except Exception as e:
    print(f"WARNING: Failed to load some services. Error: {e}")
    traceback.print_exc()
    detection_service = None
    recommendation_service = None
    generation_service = None


# ============================================================================
# Routes
# ============================================================================

@app.route('/appdata/detect/<path:filename>')
def serve_detected_files(filename: str) -> Response:
    return send_from_directory(str(DETECT_DIR), filename)

@app.route('/data/ikea_il_images/<path:filename>')
def serve_ikea_images(filename: str) -> Response:
    return send_from_directory(str(IMAGES_DIR), filename)

@app.route('/generated/<filename>')
def serve_generated_image(filename):
    return send_from_directory(GENERATED_DIR, filename)

@app.get("/")
def health_check() -> dict:
    return {
        "status": "Backend is running",
        "services": {
            "detection": detection_service is not None,
            "recommendation": recommendation_service is not None,
            "generation": generation_service is not None
        }
    }

@app.post("/detect")
def detect() -> Union[Response, tuple[Response, int]]:
    if detection_service is None:
        return jsonify({"error": "Detection service not available"}), 500

    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    try:
        img = request.files["image"]
        save_path = UPLOADS_DIR / img.filename
        img.save(str(save_path))

        detections = detection_service.detect_furniture(
            image_path=str(save_path),
            save_dir=str(DETECT_DIR)
        )

        return jsonify(detections)

    except FileNotFoundError as e:
        return jsonify({"error": f"Directory not found: {e}"}), 500
    except Exception as e:
        print(f"🚨 DETECTION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Detection failed"}), 500

@app.post("/api/chat")
def chat_endpoint():
    image_filename = request.form.get("image_filename")
    save_path = None

    if "image" in request.files:
        img = request.files["image"]
        image_filename = f"chat_{img.filename}"
        save_path = str(UPLOADS_DIR / image_filename)
        img.save(save_path)
    elif image_filename:
        save_path = str(UPLOADS_DIR / image_filename)
    
    # עכשיו אנחנו לא מחזירים 400 אם אין תמונה - פשוט שולחים None
    messages_str = request.form.get("messages", "[]")
    try:
        messages = json.loads(messages_str)
    except:
        messages = []

    if recommendation_service is None:
        return jsonify({"error": "Service unavailable"}), 500

    # קריאה לצ'אט - נסמכת על כך שיש מספיק מכסה פנויה
    chat_data = recommendation_service.chat_with_designer(
        image_path=save_path,
        messages=messages
    )

    return jsonify({
        "response": chat_data["text"],
        "recommendations": chat_data["recommendations"],
        "image_filename": image_filename
    })

@app.post("/generate_new_design")
def generate_new_design() -> Union[Response, tuple[Response, int]]:
    """Generate new furniture design and save it as a file on the server."""
    global generation_service
    if generation_service is None:
        return jsonify({"error": "Generation service not available"}), 500

    raw_original_path = request.form.get("original_image_path", "")
    selected_crop_url = request.form.get("selected_crop_url", "")
    recommendation_image_url = request.form.get("recommendation_image_url", "")
    prompt = request.form.get("prompt", "")

    if not raw_original_path or not prompt or not selected_crop_url or not recommendation_image_url:
        print(f"⚠️ Missing fields. Orig: {raw_original_path}, Crop: {selected_crop_url}")
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # לקיחת שם הקובץ בלבד
        filename = os.path.basename(raw_original_path)
        original_image_path = UPLOADS_DIR / filename

        if not original_image_path.exists():
            print(f"❌ Error: File not found at {original_image_path}")
            return jsonify({"error": f"Original file not found: {filename}"}), 404

        crop_path = url_to_file_path(selected_crop_url)
        
        # טיפול בתמונה של ההמלצה: יכולה להיות נתיב מקומי או URL חיצוני
        rec_path = None
        if recommendation_image_url.startswith("http"):
            # הורדת תמונה חיצונית לתיקייה זמנית
            import requests
            from pathlib import Path
            temp_dir = UPLOADS_DIR / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / f"temp_rec_{int(time.time())}.jpg"
            
            response = requests.get(recommendation_image_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                rec_path = temp_path
            else:
                return jsonify({"error": "Failed to download recommendation image"}), 400
        else:
            rec_path = url_to_file_path(recommendation_image_url)

        save_path = os.path.join(GENERATED_DIR, "generated.png")

        print(f"🎨 Generating design using base image: {original_image_path}")

        generation_service.generate_design(
            str(original_image_path),
            str(crop_path),
            str(rec_path),
            prompt,
            item_name="furniture",
            save_path=save_path
        )

        with open(save_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        return jsonify({"generated_image": encoded_string})

    except Exception as e:
        print(f"🚨 GENERATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Image generation failed"}), 500

def get_exact_category(user_query):
    # רשימת הקטגוריות
    categories = [
        'Sofa 3-seat', 'Sofa bed', 'Armchair', 'Chair dining', 'Chair office',
        'Bar chair', 'Bed double', 'Bed single', 'Bed frame', 'Table dining',
        'Table coffee', 'Desk', 'Bedside table', 'Lamp floor', 'Lamp table',
        'Chest of drawers', 'TV bench', 'Wardrobe', 'Bookcase', 'Sideboard', 'Outdoor table'
    ]

    prompt = f"""
    You are a furniture expert for the CasAI app. 
    Analyze the user's request: "{user_query}"
    Choose the MOST relevant category from this exact list: {categories}
    Return ONLY the category name. If no category fits, return 'None'.
    """

    if not client:
        return "None"

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini category error: {e}")
        return "None"


@app.route("/recommend", methods=["POST"])
def recommend():
    """Get recommendations based on image and text with Gemini category filtering."""
    if recommendation_service is None:
        return jsonify({"error": "Recommendation service not available"}), 500

    try:
        selected_crop_url = request.form.get("crop_url", "")
        text = request.form.get("text", "")
        query_image_path = None

        print(f"🚀 שרת CasAI: מתחיל תהליך עבור: '{text}'")

        if selected_crop_url:
            query_image_path = str(url_to_file_path(selected_crop_url))
        elif "image" in request.files:
            img = request.files["image"]
            save_path = UPLOADS_DIR / img.filename
            img.save(str(save_path))
            detections = detection_service.detect_furniture(str(save_path), str(DETECT_DIR))
            if detections:
                query_image_path = detections[0]["path"]

        # ניתוח משולב של קטגוריה ומידות בקריאה אחת ל-AI (חוסך זמן יקר!)
        target_cat, est_w, est_l = "None", None, None
        if text.strip() or query_image_path:
            target_cat, est_w, est_l = recommendation_service.analyze_query(text.strip(), query_image_path)
            print(f"🔍 AI Analysis: Category={target_cat}, Dims={est_w}x{est_l}")

        # קבלת המלצות (משתמש בנתונים שכבר חושבו)
        results = recommendation_service.recommend(
            query_text=text.strip(),
            query_image_path=query_image_path,
            top_k=10,
            alpha=0.9,
            category_filter=target_cat,
            precomputed_dims=(est_w, est_l)
        )

        if 'vector' in results.columns:
            results = results.drop(columns=['vector'])

        # --- כאן היו קודם 3 קריאות מיותרות לחישוב מידות - נמחקו! ---

        response_data = []
        for _, row in results.iterrows():
            item_data = {
                'item_name': row.get('item_name', ''),
                'item_price': row.get('item_price', ''),
                'item_url': row.get('product_link', ''),
                'similarity': row.get('similarity', 0.0),
                'item_img': f"/data/ikea_il_images/{row['image_file']}" if pd.notna(row.get('image_file')) else row.get('image_url', '')
            }
            response_data.append(item_data)

        return jsonify(response_data)

    except Exception as e:
        print(f"🚨 RECOMMENDATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.post("/google_search")
def google_search_endpoint() -> Union[Response, tuple[Response, int]]:
    global recommendation_service
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "query field is required"}), 400

        results = recommendation_service.search_google_shopping(query)
        for idx, item in enumerate(results):
            if "id" not in item:
                item["id"] = idx
        return jsonify(results)
    except Exception as e:
        print(f"🚨 GOOGLE SEARCH ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Google search failed"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)