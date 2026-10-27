from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import math
from typing import Sequence


class EmbeddingProvider(ABC):
    """Backend-independent interface for generating embeddings."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for one piece of text."""
        raise NotImplementedError

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple pieces of text."""
        return [self.embed(text) for text in texts]


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """Deterministic embedding implementation for tests and local development."""

    def __init__(self, dimensions: int = 32) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")

        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        values: list[float] = []

        for index in range(self.dimensions):
            digest = hashlib.sha256(
                f"{index}:{text}".encode("utf-8")
            ).digest()

            integer = int.from_bytes(digest[:8], "big")
            values.append((integer / 2**64) * 2.0 - 1.0)

        norm = math.sqrt(sum(value * value for value in values))

        if norm == 0:
            return [0.0] * self.dimensions

        return [value / norm for value in values]


class ConfigurableEmbeddingProvider(EmbeddingProvider):
    """
    Production-facing embedding provider.

    The actual embedding function is injected so credentials and external
    provider configuration remain outside this module.
    """

    def __init__(self, embed_function) -> None:
        if not callable(embed_function):
            raise TypeError("embed_function must be callable")

        self._embed_function = embed_function

    def embed(self, text: str) -> list[float]:
        result = self._embed_function(text)
        return [float(value) for value in result]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [
            [float(value) for value in result]
            for result in self._embed_function(list(texts))
        ]

class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """Generate semantic embeddings using a Sentence Transformers model."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        kwargs = {"device": device} if device else {}
        self.model = SentenceTransformer(model_name, **kwargs)
        self.dimensions = self.model.get_sentence_embedding_dimension()

        if self.dimensions is None:
            raise RuntimeError("Could not determine embedding dimensions")

    def embed(self, text: str) -> list[float]:
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        vectors = self.model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vectors[0].astype(float).tolist()

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vectors.astype(float).tolist()
