"""Model loading functions for Streamlit app with caching."""

import streamlit as st
from core.models import ModelLoader
from utils.detection import DetectionService

# Create model loader instance
_model_loader = ModelLoader()

# --- MODEL LOADING FUNCTIONS (with Streamlit caching) ---

@st.cache_resource(show_spinner="Loading YOLO Detection Model...")
def load_yolo_model():
    """Load YOLO model for furniture detection."""
    return _model_loader.load_yolo_model()


@st.cache_resource(show_spinner="Loading CLIP Embedding Model...")
def load_similarity_model():
    """Load CLIP model for image similarity."""
    try:
        return _model_loader.load_clip_model()
    except ImportError as e:
        st.error("sentence-transformers not installed. Please run: pip install sentence-transformers")
        raise


@st.cache_data(show_spinner="Loading IKEA Product Database...")
def load_ikea_dataframe():
    """Load IKEA product DataFrame with embeddings."""
    try:
        return _model_loader.load_ikea_dataframe()
    except FileNotFoundError as e:
        error_msg = str(e) + "\n\nPlease run the embedding script first:\n  python embedding/embed-ds.py"
        st.error(error_msg)
        raise


# --- DETECTION FUNCTIONS ---

def get_detected_photos(image_path, yolo_model, save_dir='appdata/detect/', conf_threshold=0.25):
    """
    Detect furniture in image using YOLO and save cropped images.
    
    This is a wrapper function that maintains backward compatibility
    with the existing app.py code.
    """
    detection_service = DetectionService(yolo_model)
    return detection_service.detect_furniture(
        image_path=image_path,
        save_dir=save_dir,
        conf_threshold=conf_threshold
    )