from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import sqrt
from typing import Protocol

EMBEDDING_DIMENSIONS = 384


class TextEmbedder(Protocol):
    def encode_texts(self, texts: Sequence[str]) -> list[list[float]]: ...


class EmbeddingSource(Protocol):
    title: str
    abstract: str | None


class EmbeddingRepositoryProtocol(Protocol):
    def list_papers_for_embedding(
        self,
        *,
        limit: int | None,
        paper_id: str | None,
        missing_only: bool,
    ) -> list[EmbeddingSource]: ...

    def save_embeddings(
        self,
        papers: list[EmbeddingSource],
        embeddings: list[list[float]],
    ) -> None: ...


def build_embedding_text(paper: EmbeddingSource) -> str:
    title = paper.title.strip()
    abstract = (paper.abstract or "").strip()
    if abstract:
        return f"{title}\n\n{abstract}"
    return title


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, batch_size: int):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size

    def encode_texts(self, texts: Sequence[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


@dataclass(slots=True)
class EmbeddingGenerationSummary:
    papers_selected: int = 0
    papers_embedded: int = 0


@dataclass(slots=True)
class EmbeddingProgress:
    papers_processed: int
    papers_total: int


class PaperEmbeddingService:
    def __init__(
        self,
        repository: EmbeddingRepositoryProtocol,
        embedder: TextEmbedder,
    ):
        self.repository = repository
        self.embedder = embedder

    def generate_embeddings(
        self,
        *,
        limit: int | None,
        paper_id: str | None,
        force: bool,
        batch_size: int | None = None,
        progress_callback: Callable[[EmbeddingProgress], None] | None = None,
    ) -> EmbeddingGenerationSummary:
        papers = self.repository.list_papers_for_embedding(
            limit=limit,
            paper_id=paper_id,
            missing_only=not force,
        )
        summary = EmbeddingGenerationSummary(papers_selected=len(papers))
        if not papers:
            return summary

        effective_batch_size = max(1, batch_size or len(papers))
        for start in range(0, len(papers), effective_batch_size):
            batch = papers[start : start + effective_batch_size]
            texts = [build_embedding_text(paper) for paper in batch]
            embeddings = self.embedder.encode_texts(texts)
            self.repository.save_embeddings(batch, embeddings)
            summary.papers_embedded += len(embeddings)

            if progress_callback is not None:
                progress_callback(
                    EmbeddingProgress(
                        papers_processed=summary.papers_embedded,
                        papers_total=summary.papers_selected,
                    )
                )

        return summary
