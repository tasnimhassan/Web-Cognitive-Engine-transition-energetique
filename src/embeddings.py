"""Etape 3 - Embeddings locaux (sentence-transformers)."""
from functools import lru_cache

import numpy as np

from src.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def embed(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Retourne un tableau (n, 384), vecteurs normalises (cosinus = produit scalaire)."""
    return get_model().encode(texts, batch_size=batch_size, normalize_embeddings=True,
                              show_progress_bar=len(texts) > 64)
