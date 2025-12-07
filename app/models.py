import os
import glob
import re
import numpy as np
import pandas as pd
import streamlit as st
import cv2
from PIL import Image
from ultralytics import YOLO

# הגדרת סביבה למניעת התנגשויות (חשוב ל-TF)
os.environ['TF_USE_LEGACY_KERAS'] = '1'

try:
    from tf_keras.models import Model, load_model
except ImportError:
    st.error("Please run: pip install tf-keras")
    from tensorflow.keras.models import Model, load_model

# --- 1. PATH CONFIGURATION ---
MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(MODELS_DIR, '..')

# שינוי 1: הנתיב לקובץ ONNX
YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, "yolo-train/best.onnx")
SIMILARITY_MODEL_PATH = os.path.join(PROJECT_ROOT, "similarity-train/multilabel0")
IKEA_DF_PATH = os.path.join(PROJECT_ROOT, "data/ikea-data/ikea_final_model0.pkl")

TARGET_CLASSES = {'Bed', 'Dresser', 'Chair', 'Sofa', 'Lamp', 'Table'}

YOLO_TO_APP_CLASS_MAP = {
    'bed': 'Bed',
    'wardrobe': 'Dresser',
    'chair': 'Chair',
    'sofa': 'Sofa',
    'lamp': 'Lamp',
    'table': 'Table'
}


# --- 3. HELPER FUNCTIONS ---
def map_yolo_class_to_app_class(yolo_class_name):
    return YOLO_TO_APP_CLASS_MAP.get(yolo_class_name, yolo_class_name)


# --- 4. MODEL LOADING ---

@st.cache_resource(show_spinner="Loading YOLO Detection Model...")
def load_yolo_model():
    if not os.path.exists(YOLO_MODEL_PATH):
        # אם לא מוצא ONNX, מנסה לחזור ל-PT
        pt_path = YOLO_MODEL_PATH.replace(".onnx", ".pt")
        if os.path.exists(pt_path):
            return YOLO(pt_path)
        raise FileNotFoundError(f"YOLO model not found at {YOLO_MODEL_PATH}")

    # שינוי 2: טעינת ONNX בלי להעביר ל-GPU ידנית
    model = YOLO(YOLO_MODEL_PATH, task='detect')
    return model


@st.cache_resource(show_spinner="Loading Similarity Embedding Model...")
def load_similarity_model():
    if not os.path.exists(SIMILARITY_MODEL_PATH):
        raise FileNotFoundError(f"Similarity model not found at {SIMILARITY_MODEL_PATH}")

    base_model = load_model(SIMILARITY_MODEL_PATH, compile=False)
    try:
        embedding_model = Model(inputs=base_model.input, outputs=base_model.get_layer('dense_4').output)
    except ValueError:
        st.error("Error: 'dense_4' layer not found in Similarity Model.")
        return base_model
    return embedding_model


@st.cache_data(show_spinner="Loading IKEA Product Database...")
def load_ikea_dataframe():
    if not os.path.exists(IKEA_DF_PATH):
        raise FileNotFoundError(f"IKEA DataFrame not found at {IKEA_DF_PATH}")
    return pd.read_pickle(IKEA_DF_PATH)


# --- 5. CORE ML PROCESSING FUNCTIONS ---

def get_detected_photos(image_path, yolo_model, save_dir='appdata/detect/', conf_threshold=0.25):
    os.makedirs(save_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    imagecv = cv2.imread(image_path)
    if imagecv is None:
        raise ValueError(f"Could not read image from {image_path}")

    # YOLO prediction
    # שינוי 3: פשוט מריצים predict (ONNX יודע להסתדר לבד)
    results = yolo_model.predict(source=imagecv, conf=conf_threshold, verbose=False)

    result = results[0]
    boxes = result.boxes
    detected_photos = []

    if boxes is not None and len(boxes) > 0:
        img_rgb = cv2.cvtColor(imagecv, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_rgb)
        counter = 1

        for i in range(len(boxes)):
            # המרת הקואורדינטות בצורה בטוחה יותר
            box = boxes.xyxy[i].cpu().numpy().astype(int)

            # ב-ONNX לפעמים אין conf/cls בצורה ישירה כמו ב-PT, אבל Ultralytics מסדר את זה
            confidence = float(boxes.conf[i].cpu().numpy())
            class_id = int(boxes.cls[i].cpu().numpy())

            yolo_class_name = result.names.get(class_id)
            if yolo_class_name is None:
                continue

            app_class_name = map_yolo_class_to_app_class(yolo_class_name)

            if app_class_name not in TARGET_CLASSES:
                continue

            file_name = f"{base_name}_{counter}_{app_class_name}.jpg"
            save_path = os.path.join(save_dir, file_name)

            crop_img = pil_image.crop(tuple(box.tolist()))
            crop_img.save(save_path)

            detected_photos.append({
                'File_name': file_name,
                'class': app_class_name,
                'path': save_path,
                'bbox': box.tolist(),
                'confidence': confidence
            })
            counter += 1

    return detected_photos


@st.cache_data(show_spinner=False)
def get_image_vector(image_path, _similarity_model):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")

    img = cv2.resize(img, (100, 100))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_array = img.astype('float32') / 255.0
    img_array = img_array.reshape((1,) + img.shape)

    return _similarity_model.predict(img_array, verbose=0).flatten()


def calculate_similarities_vectorized(query_vector, product_vectors):
    if query_vector.ndim > 1:
        query_vector = query_vector.flatten()

    query_vector = query_vector.astype(np.float32)
    product_vectors = product_vectors.astype(np.float32)

    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    product_norms = product_vectors / (np.linalg.norm(product_vectors, axis=1, keepdims=True) + 1e-8)

    return np.dot(product_norms, query_norm)