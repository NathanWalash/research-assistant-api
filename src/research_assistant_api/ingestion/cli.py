import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict

from research_assistant_api.db.session import get_session_factory
from research_assistant_api.ingestion.config import IngestionConfig
from research_assistant_api.ingestion.service import CsvIngestionService


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
    return parser


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
        summary = CsvIngestionService(session).ingest(config)

    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
