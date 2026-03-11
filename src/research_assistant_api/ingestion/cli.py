import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from research_assistant_api.db.session import get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService, IngestionProgress


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import Leeds/OpenAlex-derived CSV data into the database.",
    )
    parser.add_argument(
        "--csv-path",
        help="Path to the main paper metadata CSV. Defaults to the configured setting.",
    )
    parser.add_argument(
        "--citation-csv-path",
        help="Optional path to a citation edge CSV with citing_paper_id and cited_paper_id columns.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of source rows to buffer before each database flush.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional limit for dry-run style validation against a subset of rows.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-batch ingestion progress output.",
    )
    return parser


def _format_eta(estimated_remaining_seconds: int | None) -> str:
    if estimated_remaining_seconds is None:
        return ""
    return f", eta {estimated_remaining_seconds}s"


def _format_ratio(processed: int, total: int | None) -> str:
    if total is None:
        return f"{processed}/?"
    return f"{processed}/{total}"


def print_progress(progress: IngestionProgress) -> None:
    if progress.phase == "citations":
        print(
            "Ingestion citations: rows "
            f"{_format_ratio(progress.citation_rows_processed, progress.citation_rows_total)}, "
            f"citations upserted {progress.citations_upserted}, "
            f"skipped missing papers {progress.citations_skipped_missing_papers}, "
            f"elapsed {progress.elapsed_seconds}s"
            f"{_format_eta(progress.estimated_remaining_seconds)}",
            file=sys.stderr,
            flush=True,
        )
        return

    print(
        "Ingestion metadata: rows "
        f"{_format_ratio(progress.metadata_rows_processed, progress.metadata_rows_total)}, "
        f"valid {progress.metadata_rows_processed - progress.source_rows_skipped}, "
        f"skipped {progress.source_rows_skipped}, "
        f"papers upserted {progress.papers_upserted}, "
        f"elapsed {progress.elapsed_seconds}s"
        f"{_format_eta(progress.estimated_remaining_seconds)}",
        file=sys.stderr,
        flush=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = IngestionConfig.from_settings(
        csv_path=args.csv_path,
        citation_csv_path=args.citation_csv_path,
        batch_size=args.batch_size,
        limit=args.limit,
    )

    session_factory = get_session_factory()
    with session_factory() as session:
        summary = CsvIngestionService(session).ingest(
            config,
            progress_callback=None if args.quiet else print_progress,
        )

    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
