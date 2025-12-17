"""Flask backend server for CasAI application.

This server provides REST API endpoints for:
- Furniture detection (YOLO)
- Recommendations (CLIP-based similarity)
- Design generation (Diffusion inpainting)
"""

from typing import Union
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import sys
import base64
import traceback
import pandas as pd
from io import BytesIO

# Add parent directory to path for imports (project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Google Shopping helper (now importable because PROJECT_ROOT is on sys.path)
from google_search import search_google_shopping

# Only import from core.models - this is the single entry point
from core.models import ModelLoader
from core.config import (
    DETECT_DIR,
    UPLOADS_DIR,
    IMAGES_DIR,
    ensure_directories,
    url_to_file_path,
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Ensure required directories exist
ensure_directories()

# Load all services once at startup
try:
    detection_service = ModelLoader.load_detection_service()
    recommendation_service = ModelLoader.load_recommendation_service()
    generation_service = ModelLoader.load_generation_service()
    print("All services loaded successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load services. Error: {e}")
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


@app.post("/generate_design")
def generate_new_design() -> Union[Response, tuple[Response, int]]:
    """Generate new furniture design using diffusion inpainting."""
    if generation_service is None:
        return jsonify({"error": "Generation service not available"}), 500
    
    original_image_path = request.form.get("original_image_path", "")
    selected_crop_url = request.form.get("selected_crop_url", "")
    prompt = request.form.get("prompt", "")
    
    if not original_image_path or not prompt or not selected_crop_url:
        return jsonify({"error": "Missing required fields: original_image_path, selected_crop_url, prompt"}), 400
    
    try:
        # Convert URL to file path
        crop_path = url_to_file_path(selected_crop_url)
        
        # Verify files exist
        if not os.path.exists(original_image_path):
            return jsonify({"error": f"Original image not found: {original_image_path}"}), 404
        
        if not crop_path.exists():
            return jsonify({"error": f"Crop image not found: {crop_path}"}), 404
        
        # Generate design
        generated_image = generation_service(
            original_image_path,
            str(crop_path),
            prompt
        )
        
        if generated_image is None:
            return jsonify({"error": "Generation failed to produce an image"}), 500
        
        # Convert to base64
        buffered = BytesIO()
        generated_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return jsonify({"generated_image": img_str})
        
    except Exception as e:
        print(f"🚨 GENERATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Image generation failed"}), 500


@app.post("/recommend/image")
def recommend_image() -> Union[Response, tuple[Response, int]]:
    """Get recommendations based on image and optional text."""
    if recommendation_service is None:
        return jsonify({"error": "Recommendation service not available"}), 500
    
    try:
        selected_crop_url = request.form.get("crop_url", "")
        text = request.form.get("text", "")
        query_image_path = None
        
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
            query_text=text.strip() if text.strip() else None,
            query_image_path=query_image_path,
            top_k=10
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


@app.post("/recommend/text")
def recommend_text() -> Union[Response, tuple[Response, int]]:
    """Get recommendations based on text query."""
    if recommendation_service is None:
        return jsonify({"error": "Recommendation service not available"}), 500
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "JSON body is required"}), 400
        
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "query field is required"}), 400
        
        # Get recommendations
        results = recommendation_service.recommend(query_text=query, top_k=10)
        
        # Remove vector column before sending
        if 'vector' in results.columns:
            results = results.drop(columns=['vector'])
        
        return jsonify(results.to_dict(orient="records"))
        
    except Exception as e:
        print(f"🚨 RECOMMENDATION ERROR: {e}")
        traceback.print_exc()
        return jsonify({"error": "Recommendation failed"}), 500


@app.post("/google_search")
def google_search_endpoint() -> Union[Response, tuple[Response, int]]:
    """Proxy endpoint to fetch Google Shopping links using Serper.dev."""
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "query field is required"}), 400

        results = search_google_shopping(query)
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
