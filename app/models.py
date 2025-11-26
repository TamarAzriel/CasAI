# models.py - Centralized ML Logic and Configuration

import os
import glob
import re
import numpy as np
import pandas as pd
import streamlit as st
import torch
import cv2
from PIL import Image
from ultralytics import YOLO
from tensorflow.keras.models import Model, load_model

# --- 1. PATH CONFIGURATION ---
# Get the directory of the current Python file (models.py)
MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
# Assumes project root is one level up from models.py
PROJECT_ROOT = os.path.join(MODELS_DIR, '..') 

YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, "yolo-train/best.pt")
SIMILARITY_MODEL_PATH = os.path.join(PROJECT_ROOT, "similarity-train/multilabel0")
IKEA_DF_PATH = os.path.join(PROJECT_ROOT, "data/ikea-data/ikea_final_model0.pkl")

# --- 2. CONSTANTS ---
TARGET_CLASSES = {'Bed', 'Dresser', 'Chair', 'Sofa', 'Lamp', 'Table'} # Use a set for faster lookup

YOLO_TO_APP_CLASS_MAP = {
    'bed': 'Bed',
    'cabinetry': 'Dresser',
    'chair': 'Chair',
    'sofa': 'Sofa',
    'lamp': 'Lamp',
    'table': 'Table'
}

# --- 3. HELPER FUNCTIONS ---

def map_yolo_class_to_app_class(yolo_class_name):
    """Maps YOLO class names to the standardized application class names."""
    return YOLO_TO_APP_CLASS_MAP.get(yolo_class_name, yolo_class_name)


# --- 4. MODEL LOADING (Streamlit Caching) ---

# Replaced @st.cache with modern @st.cache_resource for models
@st.cache_resource(show_spinner="Loading YOLO Detection Model...")
def load_yolo_model():
    if not os.path.exists(YOLO_MODEL_PATH):
        raise FileNotFoundError(f"YOLO model not found at {YOLO_MODEL_PATH}")
    
    model = YOLO(YOLO_MODEL_PATH)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)
    return model

@st.cache_resource(show_spinner="Loading Similarity Embedding Model...")
def load_similarity_model():
    """
    Load the similarity model and extract the embedding layer.
    """
        
    if not os.path.exists(SIMILARITY_MODEL_PATH):
        raise FileNotFoundError(f"Similarity model not found at {SIMILARITY_MODEL_PATH}")

    # Load the original model without the Optimizer
    base_model = load_model(SIMILARITY_MODEL_PATH, compile=False)
    
    # Assuming 'dense_4' is the correct embedding layer name
    # Ensure this layer name is correct in your Keras model
    try:
        embedding_model = Model(inputs=base_model.input, outputs=base_model.get_layer('dense_4').output)
    except ValueError:
        # Fallback if layer name is incorrect/unavailable
        st.error("Error: 'dense_4' layer not found in Similarity Model. Check your model architecture.")
        return base_model # Return base model as fallback or raise error
        
    return embedding_model
    
# Replaced @st.cache with modern @st.cache_data for dataframes
@st.cache_data(show_spinner="Loading IKEA Product Database...")
def load_ikea_dataframe():
    if not os.path.exists(IKEA_DF_PATH):
        raise FileNotFoundError(f"IKEA DataFrame not found at {IKEA_DF_PATH}")
    return pd.read_pickle(IKEA_DF_PATH)


# --- 5. CORE ML PROCESSING FUNCTIONS ---

def get_detected_photos(image_path, yolo_model, save_dir='appdata/detect/', conf_threshold=0.25):
    """
    Runs YOLO detection, saves detected crops with unique names, and returns their metadata.
    
    CRITICAL FIX: Removed the unsafe 'glob.glob' and 'os.remove' directory cleanup.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # Safely extract the base name of the input image to use in crop filenames
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    imagecv = cv2.imread(image_path)
    if imagecv is None:
        raise ValueError(f"Could not read image from {image_path}. Check file permissions or path.")
        
    # YOLO prediction
    # For source=numpy array (imagecv), results structure is slightly different, but the core 'boxes' access should be fine.
    # The image is processed in memory, so no 'save=True' is needed on the predict call itself.
    results = yolo_model.predict(source=imagecv, conf=conf_threshold, verbose=False)
    
    # Process results (only taking the first result object since source is a single image)
    result = results[0]
    boxes = result.boxes
    detected_photos = []
    
    if boxes is not None and len(boxes) > 0:
        img_rgb = cv2.cvtColor(imagecv, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(img_rgb)
        
        # Use a unique ID based on the input filename and counter for safety
        counter = 1
        
        for i in range(len(boxes)):
            box = boxes.xyxy[i].cpu().numpy().astype(int) # Ensure integer coordinates for cropping
            confidence = float(boxes.conf[i].cpu().numpy())
            class_id = int(boxes.cls[i].cpu().numpy())
            
            yolo_class_name = result.names.get(class_id)
            if yolo_class_name is None:
                 continue # Skip if class name is not found
                 
            app_class_name = map_yolo_class_to_app_class(yolo_class_name)
            
            if app_class_name not in TARGET_CLASSES:
                continue
            
            # --- UNIQUE FILE NAMING FIX ---
            # Creates a unique filename like 'uploaded_image_1_Bed.jpg'
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
    """Loads an image, preprocesses it, and gets the embedding vector."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image from {image_path}")
    
    # Preprocessing for similarity model
    img = cv2.resize(img, (100, 100)) # Ensure correct size
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Convert to RGB if needed by Keras model
    img_array = img.astype('float32') / 255.0 # Normalize
    img_array = img_array.reshape((1,) + img.shape) # Add batch dimension
    
    # Get prediction
    # Use the model passed in as argument to avoid global variable issues
    return _similarity_model.predict(img_array, verbose=0).flatten()


def calculate_similarities_vectorized(query_vector, product_vectors):
    """Calculates Cosine Similarity in a vectorized manner."""
    
    # Reshape query vector if needed (should already be flat)
    if query_vector.ndim > 1:
        query_vector = query_vector.flatten()
        
    # Ensure vectors are floating point
    query_vector = query_vector.astype(np.float32)
    product_vectors = product_vectors.astype(np.float32)
    
    # Calculate norms for normalization
    query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    # Norm along axis 1 (for each product vector)
    product_norms = product_vectors / (np.linalg.norm(product_vectors, axis=1, keepdims=True) + 1e-8)
    
    # Dot product calculation (Cosine Similarity)
    return np.dot(product_norms, query_norm)