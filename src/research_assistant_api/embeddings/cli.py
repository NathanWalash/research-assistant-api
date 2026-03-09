import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from research_assistant_api.core.config import get_settings
from research_assistant_api.db.session import get_session_factory
from research_assistant_api.embeddings import (
    EmbeddingProgress,
    PaperEmbeddingService,
    SentenceTransformerEmbedder,
)
from research_assistant_api.repositories.embedding_repository import EmbeddingRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and store paper embeddings.",
    )
    parser.add_argument("--paper-id", help="Embed a single paper by id.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of papers to embed.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recompute embeddings even if a paper already has one.",
    )
    return parser


def print_progress(progress: EmbeddingProgress) -> None:
    print(
        f"Embedded {progress.papers_processed}/{progress.papers_total} papers",
        file=sys.stderr,
        flush=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()

    embedder = SentenceTransformerEmbedder(
        model_name=settings.embedding_model_name,
        batch_size=settings.embedding_batch_size,
    )
    session_factory = get_session_factory()

    with session_factory() as session:
        service = PaperEmbeddingService(
            repository=EmbeddingRepository(session),
            embedder=embedder,
        )
        summary = service.generate_embeddings(
            limit=args.limit,
            paper_id=args.paper_id,
            force=args.force,
            batch_size=settings.embedding_batch_size,
            progress_callback=print_progress,
        )

    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
