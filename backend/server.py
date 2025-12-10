from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from models import (
    load_yolo_model,
    load_similarity_model,
    load_ikea_dataframe,
    get_detected_photos
)

app = Flask(__name__)
CORS(app)   # מאפשר תקשורת מה-React

# טוענים מודלים פעם אחת לזיכרון
yolo = load_yolo_model()
similarity_model = load_similarity_model()
ikea_df = load_ikea_dataframe()


# -------------------------
# 1. בדיקה שהשרת פועל
# -------------------------
@app.get("/")
def home():
    return {"status": "Backend is running!"}


# -------------------------
# 2. קבלת טקסט → החזרת המלצות
# -------------------------
@app.post("/recommend/text")
def recommend_text():
    data = request.json
    query = data.get("query", "")

    if not query:
        return jsonify({"error": "query is required"}), 400

    from core.recommender import Recommender
    recommender = Recommender(similarity_model, ikea_df)
    results = recommender.recommend(query_text=query, top_k=10)

    return jsonify(results.to_dict(orient="records"))


# -------------------------
# 3. קבלת תמונה → זיהוי YOLO
# -------------------------
@app.post("/detect")
def detect():
    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    img = request.files["image"]
    save_path = os.path.join("uploads", img.filename)
    os.makedirs("uploads", exist_ok=True)
    img.save(save_path)

    detections = get_detected_photos(save_path, yolo)

    return jsonify(detections)


# -------------------------
# 4. שילוב תמונה + טקסט → המלצות
# -------------------------
@app.post("/recommend/image")
def recommend_image():
    from core.recommender import Recommender

    if "image" not in request.files:
        return jsonify({"error": "image file is required"}), 400

    img = request.files["image"]
    text = request.form.get("text", "")

    save_path = os.path.join("uploads", img.filename)
    img.save(save_path)

    # 1. detect objects
    detections = get_detected_photos(save_path, yolo)

    if not detections:
        return jsonify({"error": "no furniture detected"}), 400

    # לוקחים את הפריט הראשון
    selected = detections[0]["path"]

    recommender = Recommender(similarity_model, ikea_df)

    results = recommender.recommend(
        query_text=text if text.strip() else None,
        query_image_path=selected,
        top_k=10
    )

    return jsonify(results.to_dict(orient="records"))


# -------------------------
# הרצת השרת
# -------------------------
if __name__ == "__main__":
    app.run(port=5000, debug=True)
