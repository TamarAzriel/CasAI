"""Centralized configuration for CasAI application."""

import os
from pathlib import Path
from typing import Dict

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
IMAGES_DIR = DATA_DIR / "ikea_il_images"
EMBEDDINGS_FILE = DATA_DIR / "ikea_embeddings.pkl"
CSV_FILE = DATA_DIR / "ikea_il.csv"

# App directories
APPDATA_DIR = PROJECT_ROOT / "appdata"
DETECT_DIR = APPDATA_DIR / "detect"
UPLOADS_DIR = APPDATA_DIR / "uploads"
GENERATED_DIR = APPDATA_DIR / "generated"

# Model configuration
CLIP_MODEL_NAME = 'clip-ViT-B-32'
YOLO_CONF_THRESHOLD = 0.25
YOLO_MODEL_NAME = 'yolo11s.pt'  # Raw YOLO11s model

# Target furniture classes
TARGET_CLASSES = {'bed', 'dresser', 'chair', 'sofa', 'lamp', 'table'}

# Style definitions for furniture recommendations
STYLE_DEFINITIONS: Dict[str, str] = {
    "asian": "black wood structure, bamboo texture, red accents, paper texture, dark brown timber, minimalist square shapes",
    "beach": "light birch wood, rattan and wicker material, white painted wood, beige linen fabric, sand colors, light oak",
    "contemporary": "curved furniture lines, smooth grey fabric, white and beige, round shapes, matte finish, soft texture",
    "craftsman": "solid oak wood, thick vertical slats, dark brown timber, sturdy rectangular structure, natural wood grain",
    "eclectic": "colorful fabric, velvet texture, mixed patterns, bright yellow or red or blue, unique asymmetric shape",
    "farmhouse": "white painted wood, solid pine top, black metal cup handles, beige fabric, shaker style doors, rustic white",
    "industrial": "black metal frame, dark rustic wood, vintage leather, concrete texture, wire mesh, rivets, dark grey",
    "mediterranean": "warm terracotta and orange colors, black wrought iron, dark rustic wood, heavy solid structure",
    "midcentury": "walnut wood texture, tapered wooden legs, mustard yellow or olive green fabric, curved plywood, teak veneer",
    "modern": "high gloss white finish, clear glass, chrome metal, sharp geometric lines, black and white monochrome, plastic",
    "rustic": "solid pine wood, natural wood grain with knots, brown wood stain, rough timber surface, heavy wood construction",
    "scandinavian": "light blonde wood, birch or pine, white color, light grey fabric, simple clean lines, plywood texture",
    "classic": "dark brown wood veneer, panel doors with glass, classic metal handles, beige upholstery, formal shape",
    "transitional": "grey fabric, dark wood legs, simple classic shape, neutral beige tones, clean finish",
    "tropical": "natural rattan structure, cane webbing, green leaf patterns, bamboo, dark exotic wood",
    "boho": "rattan, colorful textiles, plants, eclectic patterns"
}


def get_style_description(style_name: str) -> str:
    """Get style description by name, or return the input if not found."""
    return STYLE_DEFINITIONS.get(style_name.lower(), style_name)


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [DATA_DIR, IMAGES_DIR, APPDATA_DIR, DETECT_DIR, UPLOADS_DIR, GENERATED_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Path utility functions
def url_to_file_path(url_path: str, base_dir: Path = None) -> Path:
    """
    Convert URL path to file system path.
    
    Args:
        url_path: URL path (e.g., "/appdata/detect/crop_0.jpg")
        base_dir: Base directory to resolve relative paths (default: PROJECT_ROOT)
        
    Returns:
        Path object
    """
    if base_dir is None:
        base_dir = PROJECT_ROOT
    
    # Remove leading slash and normalize
    clean_path = url_path.lstrip('/').replace('/', os.sep)
    return base_dir / clean_path