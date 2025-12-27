"""CLIP model handling for image and text embeddings."""

from sentence_transformers import SentenceTransformer
from .config import CLIP_MODEL_NAME


class CLIPModel:
    """Wrapper for CLIP model operations."""
    
    def __init__(self):
        """
        Initialize CLIP model wrapper.
        
        Args:
            model: Optional pre-loaded SentenceTransformer CLIP model
            model_name: Optional model name to load. If model is None, will load using model_name or default.
        """
        self.model = self.load_model()
    
    @staticmethod
    def load_model() -> SentenceTransformer:
        """
        Load CLIP model for image similarity.
        
        Args:
        Returns:
            Loaded SentenceTransformer CLIP model
            
        Raises:
            ImportError: If sentence-transformers is not installed
        """
        try:
            model = SentenceTransformer(CLIP_MODEL_NAME)
            print("✅ CLIP model loaded successfully!")
            return model
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Please run: pip install sentence-transformers"
            )
    
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