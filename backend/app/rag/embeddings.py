"""Stage 7.2 Embeddings interface and implementations.

Production Default: SentenceTransformerEmbeddingModel (uses real local SentenceTransformers models).
Testing Only: DeterministicLocalEmbeddingModel (FOR UNIT TESTS ONLY, never in production).
"""

from abc import ABC, abstractmethod
import hashlib
import math
from typing import List, Optional


class BaseEmbeddingModel(ABC):
    """Abstract base class for RAG embedding models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the embedding model."""
        pass

    @property
    @abstractmethod
    def vector_dimension(self) -> int:
        """Return the dimension of output embedding vectors."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document texts into vector representations."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text into a vector representation."""
        pass


class SentenceTransformerEmbeddingModel(BaseEmbeddingModel):
    """Production local embedding model using SentenceTransformers.

    Default model: 'all-MiniLM-L6-v2' (384 dimensions).
    Raises RuntimeError or ImportError if sentence-transformers is missing or fails to load.
    Will NEVER fall back to fake/dummy vectors.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dimension = 384

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            # Fetch actual dimension from model
            sample_emb = self._model.encode(["test"], convert_to_numpy=True)
            self._dimension = int(sample_emb.shape[1])
        except Exception as e:
            raise RuntimeError(
                f"Failed to load production embedding model '{model_name}'. "
                f"Ensure sentence-transformers is installed and the model is accessible. Error: {e}"
            ) from e

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def vector_dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dimension
        embedding = self._model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
        return embedding.tolist()


class DeterministicLocalEmbeddingModel(BaseEmbeddingModel):
    """TEST-ONLY embedding model for unit testing and offline test fixtures.

    WARNING: Must NEVER be used as the production embedding model.
    Generates deterministic normalized 384-dimensional vectors based on content hashes.
    """

    def __init__(self, model_name: str = "test-deterministic-384d", vector_dimension: int = 384):
        self._model_name = model_name
        self._dimension = vector_dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def vector_dimension(self) -> int:
        return self._dimension

    def _hash_to_vector(self, text: str) -> List[float]:
        """Generate a deterministic 384-dimensional unit vector from text content."""
        if not text:
            vec = [0.0] * self._dimension
            vec[0] = 1.0
            return vec

        raw_vec: List[float] = []
        # Create deterministic pseudo-features using salted MD5/SHA256 hashes
        for i in range(self._dimension):
            seed_str = f"{text}_dim_{i}"
            h = hashlib.md5(seed_str.encode("utf-8")).hexdigest()
            # Map hex to range [-1.0, 1.0]
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            raw_vec.append(val)

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in raw_vec))
        if norm == 0:
            norm = 1.0
        return [v / norm for v in raw_vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._hash_to_vector(text)


def get_default_embedding_model(is_testing: bool = False) -> BaseEmbeddingModel:
    """Factory for obtaining the embedding model.

    Args:
        is_testing: If True, returns DeterministicLocalEmbeddingModel for fast test runs.
                   If False (default), returns SentenceTransformerEmbeddingModel for production.
    """
    if is_testing:
        return DeterministicLocalEmbeddingModel()
    return SentenceTransformerEmbeddingModel()
