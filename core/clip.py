"""CLIP model handling for image and text embeddings."""

from sentence_transformers import SentenceTransformer
from .config import CLIP_MODEL_NAME


class CLIPModel:
    """Wrapper for CLIP model operations."""
    
    def __init__(self, model: SentenceTransformer):
        """
        Initialize CLIP model wrapper.
        
        Args:
            model: Loaded SentenceTransformer CLIP model
        """
        self.model = model
    
    def encode_text(self, text: str) -> list:
        """
        Encode text into embedding vector.
        
        Args:
            text: Text string to encode
            
        Returns:
            Embedding vector as list
        """
        return self.model.encode(text).tolist()
    
    def encode_image(self, image_path: str) -> list:
        """
        Encode image into embedding vector.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Embedding vector as list
        """
        from PIL import Image
        img = Image.open(image_path).convert('RGB')
        return self.model.encode(img).tolist()
    
    def encode(self, input_data) -> list:
        """
        Encode input (text string or PIL Image) into embedding vector.
        
        Args:
            input_data: Text string or PIL Image
            
        Returns:
            Embedding vector as list
        """
        return self.model.encode(input_data).tolist()


def load_clip_model(model_name: str = CLIP_MODEL_NAME) -> SentenceTransformer:
    """
    Load CLIP model for image similarity.
    
    Args:
        model_name: Name of the CLIP model to load
        
    Returns:
        Loaded SentenceTransformer CLIP model
        
    Raises:
        ImportError: If sentence-transformers is not installed
    """
    try:
        model = SentenceTransformer(model_name)
        return model
    except ImportError:
        raise ImportError(
            "sentence-transformers not installed. "
            "Please run: pip install sentence-transformers"
        )

