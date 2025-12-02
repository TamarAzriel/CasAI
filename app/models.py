import os
import numpy as np
import pandas as pd
import streamlit as st
import torch
import cv2
from PIL import Image
from ultralytics import YOLO
import tensorflow as tf
from tensorflow import keras   # <--- שימוש נכון ומאובטח!

# ----------------- MODEL LOADER -----------------

def load_model(path):
    # חשוב! אין compile כאן, למניעת שגיאות
    return keras.models.load_model(path, compile=False)

# ----------------- PATH CONFIG -----------------

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(MODELS_DIR, '..')

YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, "yolo-train/best.pt")
SIMILARITY_MODEL_PATH = os.path.join(PROJECT_ROOT, "similarity-train/multilabel0")
IKEA_DF_PATH = os.path.join(PROJECT_ROOT, "data/ikea-data/ikea_final_model0.pkl")

# ----------------- CONSTANTS -----------------

TARGET_CLASSES = {'Bed', 'Dresser', 'Chair', 'Sofa', 'Lamp', 'Table'}

YOLO_TO_APP_CLASS_MAP = {
    'bed': 'Bed',
    'cabinetry': 'Dresser',
    'chair': 'Chair',
    'sofa': 'Sofa',
    'lamp': 'Lamp',
    'table': 'Table'
}

def map_yolo_class_to_app_class(yolo_class_name):
    return YOLO_TO_APP_CLASS_MAP.get(yolo_class_name, yolo_class_name)

# ----------------- MODEL LOADING -----------------

@st.cache_resource(show_spinner="Loading YOLO Model...")
def load_yolo_model():
    if not os.path.exists(YOLO_MODEL_PATH):
        raise FileNotFoundError(f"YOLO model not found at {YOLO_MODEL_PATH}")

    model = YOLO(YOLO_MODEL_PATH)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    return model


@st.cache_resource(show_spinner="Loading Similarity Model...")
def load_similarity_model():

    if not os.path.exists(SIMILARITY_MODEL_PATH):
        raise FileNotFoundError(f"Similarity model not found at {SIMILARITY_MODEL_PATH}")

    # Load base model
    base_model = load_model(SIMILARITY_MODEL_PATH)

    # Try to extract embedding layer
    try:
        embedding_layer = base_model.get_layer('dense_4').output
        embedding_model = keras.Model(inputs=base_model.input, outputs=embedding_layer)
    except Exception as e:
        st.error("❌ Error: embedding layer 'dense_4' not found. Using full model.")
        return base_model

    return embedding_model


@st.cache_data(show_spinner="Loading IKEA Product Database...")
def load_ikea_dataframe():
    if not os.path.exists(IKEA_DF_PATH):
        raise FileNotFoundError(f"IKEA DataFrame not found at {IKEA_DF_PATH}")

    return pd.read_pickle(IKEA_DF_PATH)


# ----------------- YOLO DETECTION -----------------

def get_detected_photos(image_path, yolo_model, save_dir='appdata/detect/', conf_threshold=0.25):

    os.makedirs(save_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]

    imagecv = cv2.imread(image_path)
    if imagecv is None:
        raise ValueError(f"Could not read image: {image_path}")

    results = yolo_model.predict(source=imagecv, conf=conf_threshold, verbose=False)
    result = results[0]

    detected_photos = []
    boxes = result.boxes

    if boxes is not None and len(boxes) > 0:
        pil_image = Image.fromarray(cv2.cvtColor(imagecv, cv2.COLOR_BGR2RGB))

        counter = 1
        for i in range(len(boxes)):
            box = boxes.xyxy[i].cpu().numpy().astype(int)
            confidence = float(boxes.conf[i].cpu().numpy())
            class_id = int(boxes.cls[i].cpu().numpy())

            yolo_class = result.names.get(class_id)
            if yolo_class is None:
                continue

            app_class = map_yolo_class_to_app_class(yolo_class)

            if app_class not in TARGET_CLASSES:
                continue

            filename = f"{base_name}_{counter}_{app_class}.jpg"
            save_path = os.path.join(save_dir, filename)

            crop = pil_image.crop(tuple(box.tolist()))
            crop.save(save_path)

            detected_photos.append({
                'File_name': filename,
                'class': app_class,
                'path': save_path,
                'bbox': box.tolist(),
                'confidence': confidence
            })

            counter += 1

    return detected_photos


# ----------------- IMAGE EMBEDDING -----------------

@st.cache_data(show_spinner=False)
def get_image_vector(image_path, model):

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read {image_path}")

    img = cv2.resize(img, (100, 100))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype('float32') / 255.0
    img = img.reshape((1,) + img.shape)

    return model.predict(img, verbose=0).flatten()


# ----------------- SIMILARITY -----------------

def calculate_similarities_vectorized(query_vec, product_vecs):

    if query_vec.ndim > 1:
        query_vec = query_vec.flatten()

    query_vec = query_vec.astype(np.float32)
    product_vecs = product_vecs.astype(np.float32)

    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    product_norms = product_vecs / (np.linalg.norm(product_vecs, axis=1, keepdims=True) + 1e-8)

    return np.dot(product_norms, query_norm)
