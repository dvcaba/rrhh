# src/embedder/embed.py

import os
from functools import lru_cache
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from smart_filtering.config import load_config

CONFIG = load_config()
DEFAULT_MODEL_NAME = CONFIG.get("models", {}).get("embedding", "paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDER_MODE = os.getenv("SMART_FILTERING_EMBEDDER_MODE", "").lower()  # "offline" forces dummy model


class Embedder:
    """Wrapper around SentenceTransformer to keep the model cached."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        if EMBEDDER_MODE == "offline":
            # Dummy model that returns zero vectors, useful when offline
            self.model = None
        else:
            self.model = SentenceTransformer(model_name)

    def embed_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings for a string or list of strings."""
        if isinstance(texts, str):
            texts = [texts]
        if self.model is None:
            return np.zeros((len(texts), 5))
        return self.model.encode(texts, convert_to_numpy=True)


@lru_cache(maxsize=1)
def get_embedder(model_name: str = DEFAULT_MODEL_NAME) -> Embedder:
    """Return a cached embedder instance to avoid re-loading the model per request."""
    return Embedder(model_name=model_name)


if __name__ == "__main__":
    embedder = get_embedder()

    sentence = "This is a test sentence for embedding."
    embedding = embedder.embed_text(sentence)
    print(f"\nEmbedding for '{sentence}':")
    print(embedding.shape)
    print(embedding[0][:5])

    sentences = [
        "Data Engineer with Python and PySpark skills.",
        "Project Manager with Agile experience.",
        "Ingeniero de Datos con habilidades en Python y PySpark.",
        "Gerente de Proyecto con experiencia en Agile.",
    ]
    embeddings = embedder.embed_text(sentences)
    print(f"\nEmbeddings for multiple sentences (shape: {embeddings.shape}):")
    print(embeddings[0][:5])
    print(embeddings[1][:5])
    print(embeddings[2][:5])
    print(embeddings[3][:5])
