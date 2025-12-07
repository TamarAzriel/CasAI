from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import base64

app = Flask(__name__)
CORS(app)  # מאפשר לאפליקציה (Frontend) לדבר עם השרת

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/api/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    style = request.form.get('style', 'modern')
    
    # שמירת התמונה
    filename = f"{int(time.time())}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    print(f"[SERVER] Processing image: {filepath} with style: {style}")

    # --- כאן תוכלי לחבר את המודל האמיתי שלך בעתיד ---
    # furniture = detect_furniture(filepath)
    # new_image = generate_new_design(filepath, style)

    # נתוני דמה (Mock Data) לתצוגה באפליקציה
    furniture_list = [
        {"name": "Velvet Chaise", "price": "$1,200", "img": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc"},
        {"name": "Marble Coffee Table", "price": "$850", "img": "https://images.unsplash.com/photo-1507473888900-52e1adad54cd"},
        {"name": "Artisan Floor Lamp", "price": "$420", "img": "https://images.unsplash.com/photo-1513506003011-3b03c80165bd"}
    ]

    # החזרת התמונה (כרגע המקורית) בפורמט שהאפליקציה מבינה
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    return jsonify({
        "status": "success",
        "result_image": f"data:image/jpeg;base64,{encoded_string}", 
        "products": furniture_list
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)