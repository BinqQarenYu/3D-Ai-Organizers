from abc import ABC, abstractmethod
import numpy as np

class ImageEmbedder(ABC):
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the embedding engine (e.g., 'imgbeddings-onnx-int8')"""
        pass
        
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensionality of the produced embeddings"""
        pass

    @abstractmethod
    def embed_image_path(self, path: str) -> np.ndarray:
        """Accepts an image path and returns an embedding normalized"""
        pass

class StubEmbedder(ImageEmbedder):
    """Stub embedder returning random vectors for development testing."""
    @property
    def engine_name(self) -> str:
        return "stub-uuid"
        
    @property
    def dimensions(self) -> int:
        return 768

    def embed_image_path(self, path: str) -> np.ndarray:
        # TODO: integrate ONNX/CLI imgbeddings model logic here
        return np.random.rand(768).astype(np.float32)
