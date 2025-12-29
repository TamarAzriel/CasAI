"""Flask backend server for CasAI application.

This server provides REST API endpoints for:
- Furniture detection (YOLO)
- Recommendations (CLIP-based similarity)
- Design generation (Diffusion inpainting)
"""

# Fix SSL certificate verification issues
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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

# Only import from core.models - this is the single entry point
from core.models import ModelLoader
from core.config import (
    DETECT_DIR,
    UPLOADS_DIR,
    IMAGES_DIR,
    GENERATED_DIR,
    ensure_directories,
    url_to_file_path,
)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS properly - allow all origins for development
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Ensure required directories exist
ensure_directories()

# Load all services once at startup
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
# Static file serving endpoints
# ============================================================================
@app.route('/appdata/detect/<path:filename>')
def serve_detected_files(filename: str) -> Response:
    """Serve detected crop images."""
    return send_from_directory(str(DETECT_DIR), filename)


@app.route('/data/ikea_il_images/<path:filename>')
def serve_ikea_images(filename: str) -> Response:
    """Serve IKEA product images."""
    return send_from_directory(str(IMAGES_DIR), filename)

@app.route('/generated/<filename>')
def serve_generated_image(filename):
    return send_from_directory(GENERATED_DIR, filename)

# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/")
def health_check() -> dict:
    """Health check endpoint."""
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
    """Detect furniture in uploaded image."""
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
    
#TODO: need to test and validate correctly
@app.post("/api/chat")
def chat_endpoint():
    """Endpoint לצ'אט עם Gemini"""
    
    # 1. טיפול בתמונה
    image_filename = request.form.get("image_filename")
    save_path = None
    
    if "image" in request.files:
        img = request.files["image"]
        image_filename = f"chat_{img.filename}" 
        save_path = UPLOADS_DIR / image_filename
        img.save(str(save_path))
    elif image_filename:
        save_path = UPLOADS_DIR / image_filename
    else:
        return jsonify({"error": "No image provided"}), 400

    # 2. קבלת ההודעות
    messages_str = request.form.get("messages", "[]")
    try:
        messages = json.loads(messages_str)
    except:
        messages = []

    if recommendation_service is None:
        return jsonify({"error": "Service unavailable"}), 500

    # 3. שליחה ל-Gemini
    ai_response = recommendation_service.chat_with_designer(
        image_path=str(save_path),
        messages=messages
    )
    
    return jsonify({
        "response": ai_response,
        "image_filename": image_filename 
    })


@app.post("/generate_new_design")
def generate_new_design() -> Union[Response, tuple[Response, int]]:
    """Generate new furniture design and save it as a file on the server."""
    global generation_service
    if generation_service is None:
        return jsonify({"error": "Generation service not available"}), 500
    
    original_image_path = request.form.get("original_image_path", "")
    selected_crop_url = request.form.get("selected_crop_url", "")
    recommendation_image_url = request.form.get("recommendation_image_url", "")
    prompt = request.form.get("prompt", "")
    
    if not original_image_path or not prompt or not selected_crop_url or not recommendation_image_url:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        crop_path = url_to_file_path(selected_crop_url)
        rec_path = url_to_file_path(recommendation_image_url)
        save_path = os.path.join(GENERATED_DIR, "generated.png")

        # 1. קריאה לשירות היצירה (גמני)
        generation_service.generate_design(
            original_image_path,       # 1. original_image_path
            str(crop_path),            # 2. crop_image_path
            str(rec_path),             # 3. recommendation_image_path (התמונה מאיקאה)
            prompt,                    # 4. prompt (הטקסט מהמשתמש)
            item_name="furniture",     # 5. item_name (אופציונלי)
            save_path=save_path        # 6. save_path
            )
        timestamp = int(time.time())
        image_url = f"http://127.0.0.1:5000/generated/generated.png?t={timestamp}"

        with open(save_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # אנחנו מחזירים את התמונה עצמה כטקסט, לא את הנתיב שלה
        return jsonify({"generated_image": encoded_string})
        
    except Exception as e:
        print(f"🚨 GENERATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Image generation failed"}), 500

# TODO: need to know if it work correctly with the function
# @app.post("/generate_from_recommendation")
# def generate_from_recommendation() -> Union[Response, tuple[Response, int]]:
#     global generation_service
#     """Generate furniture design based on recommended product image."""
#     if generation_service is None:
#         return jsonify({"error": "Generation service not available"}), 500
    
#     original_image_path = request.form.get("original_image_path", "")
#     selected_crop_url = request.form.get("selected_crop_url", "")
#     recommendation_image_url = request.form.get("recommendation_image_url", "")
#     item_name = request.form.get("item_name", "furniture")
    
#     try:
#         crop_path = url_to_file_path(selected_crop_url)
#         rec_path = url_to_file_path(recommendation_image_url)
        
#         # יצירת העיצוב
#         raw_generated_image = generation_service(
#             original_image_path,
#             str(crop_path),
#             str(rec_path),
#             item_name=item_name
#         )
        
#         if raw_generated_image is None:
#             return jsonify({"error": "Generation failed to produce an image"}), 500
        
#         # --- התיקון כאן: שימוש בשם משתנה שונה מ-'Image' כדי למנוע התנגשות ---
#         if hasattr(raw_generated_image, 'convert'):
#             final_img = raw_generated_image.convert("RGB")
#         else:
#             final_img = Image.fromarray(raw_generated_image).convert("RGB")
        
#         buffered = BytesIO()
#         # עכשיו ה-format="JPEG" יעבוד כי final_img הוא בוודאות אובייקט Pillow
#         final_img.save(buffered, format="JPEG", quality=90)
#         img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
#         return jsonify({"generated_image": img_str})
        
#     except Exception as e:
#         print(f"🚨 GENERATION FROM RECOMMENDATION ERROR: {e}")
#         traceback.print_exc()
#         return jsonify({"error": "Image generation failed"}), 500


@app.post("/recommend")
def recommend() -> Union[Response, tuple[Response, int]]:
    """Get recommendations based on image and optional text."""
    if recommendation_service is None:
        return jsonify({"error": "Recommendation service not available"}), 500
    
    try:
        selected_crop_url = request.form.get("crop_url", "")
        text = request.form.get("text", "")
        query_image_path = None
        if not text and not selected_crop_url and not "image" in request.files:
            return jsonify({"error": "Either crop_url/image or text query is required"}), 400
        
        # Handle crop URL
        if selected_crop_url:
            query_image_path = url_to_file_path(selected_crop_url)
            if not query_image_path.exists():
                return jsonify({"error": "Selected crop file not found"}), 404
            query_image_path = str(query_image_path)
        
        # Handle uploaded image
        elif "image" in request.files:
            if detection_service is None:
                return jsonify({"error": "Detection service not available"}), 500
            
            img = request.files["image"]
            save_path = UPLOADS_DIR / img.filename
            img.save(str(save_path))
            
            detections = detection_service.detect_furniture(
                image_path=str(save_path),
                save_dir=str(DETECT_DIR)
            )
            
            if not detections:
                return jsonify({"error": "No furniture detected"}), 400
            
            query_image_path = detections[0]["path"]
        
        if not query_image_path and not text.strip():
            return jsonify({"error": "Either crop_url/image or text query is required"}), 400
        
        # Get recommendations
        results = recommendation_service.recommend(
            query_text=text.strip(),
            query_image_path=query_image_path,
            top_k=10,
            alpha=0.5
        )
        
        # Format response (remove vector column, format image paths)
        if 'vector' in results.columns:
            results = results.drop(columns=['vector'])
        
        # Build response with proper image URLs
        response_data = []
        for _, row in results.iterrows():
            item_data = {
                'item_name': row.get('item_name', ''),
                'item_price': row.get('item_price', ''),
                'item_url': row.get('product_link', ''),
                'similarity': row.get('similarity', 0.0)
            }
            
            # Handle image path
            if 'image_file' in row and pd.notna(row['image_file']):
                item_data['item_img'] = f"/data/ikea_il_images/{row['image_file']}"
            elif 'image_url' in row and pd.notna(row['image_url']):
                item_data['item_img'] = row['image_url']
            else:
                item_data['item_img'] = ""
            
            response_data.append(item_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"🚨 RECOMMENDATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Recommendation failed"}), 500



@app.post("/google_search")
def google_search_endpoint() -> Union[Response, tuple[Response, int]]:
    """Proxy endpoint to fetch Google Shopping links using Serper.dev."""
    global recommendation_service
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "query field is required"}), 400

        results = recommendation_service.search_google_shopping(query)
        # ensure each result has an id for the frontend
        for idx, item in enumerate(results):
            if "id" not in item:
                item["id"] = idx
        return jsonify(results)
    except Exception as e:
        print(f"🚨 GOOGLE SEARCH ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Google search failed"}), 500


# ============================================================================
# Server startup
# ============================================================================

if __name__ == "__main__":
    app.run(port=5000, debug=True)
