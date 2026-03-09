"""Embedding utilities and CLI support."""

from research_assistant_api.embeddings.service import (
    EMBEDDING_DIMENSIONS,
    EmbeddingGenerationSummary,
    SentenceTransformerEmbedder,
    build_embedding_text,
    cosine_similarity,
)

__all__ = [
    "EMBEDDING_DIMENSIONS",
    "EmbeddingGenerationSummary",
    "SentenceTransformerEmbedder",
    "build_embedding_text",
    "cosine_similarity",
]
