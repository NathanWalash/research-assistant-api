import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from research_assistant_api.citation_graph.service import (
    CitationGraphExportConfig,
    CitationGraphProgress,
    CitationGraphExportService,
)
from research_assistant_api.core.config import get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export Leeds-to-Leeds citation edges from OpenAlex using exact work ids."
        ),
    )
    parser.add_argument(
        "--csv-path",
        help="Path to the main Leeds/OpenAlex-derived CSV file.",
    )
    parser.add_argument(
        "--query-path",
        default=".tmp/leeds_citation_queries.csv",
        help="Path for the generated OpenAlexNet query CSV.",
    )
    parser.add_argument(
        "--works-jsonl-path",
        default=".tmp/leeds_citation_works.jsonl",
        help="Path for the fetched OpenAlex works JSONL audit file.",
    )
    parser.add_argument(
        "--output-path",
        default=".tmp/leeds_citation_edges.csv",
        help="Path for the final citing_paper_id/cited_paper_id CSV.",
    )
    parser.add_argument(
        "--progress-path",
        default=".tmp/leeds_citation_progress.json",
        help="Path for the resumable export progress JSON file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of Leeds work ids to include in each OpenAlex query row.",
    )
    parser.add_argument(
        "--rate-interval",
        type=float,
        default=0.2,
        help="Minimum interval in seconds between OpenAlex API calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for a smaller pilot export.",
    )
    parser.add_argument(
        "--email",
        default="",
        help="Optional email to pass through to OpenAlex requests.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-batch progress output.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard any existing JSONL, edge CSV, and progress state before exporting.",
    )
    return parser


def print_progress(progress: CitationGraphProgress) -> None:
    print(
        "Fetched batches "
        f"{progress.batches_completed}/{progress.batches_total}, "
        f"papers {progress.papers_fetched}/{progress.papers_total}, "
        f"edges {progress.edges_exported}",
        file=sys.stderr,
        flush=True,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()

    config = CitationGraphExportConfig(
        dataset_csv_path=Path(args.csv_path) if args.csv_path else settings.dataset_csv_path,
        query_csv_path=Path(args.query_path),
        works_jsonl_path=Path(args.works_jsonl_path),
        edge_pairs_csv_path=Path(args.output_path),
        progress_path=Path(args.progress_path),
        batch_size=args.batch_size,
        rate_interval=args.rate_interval,
        email=args.email,
        limit=args.limit,
        quiet=args.quiet,
        reset=args.reset,
    )
    summary = CitationGraphExportService().export(
        config,
        progress_callback=None if args.quiet else print_progress,
    )
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
