import json

from research_assistant_api.ingestion import cli
from research_assistant_api.ingestion.service import IngestionProgress
from research_assistant_api.ingestion.service import IngestionSummary


def test_ingestion_cli_prints_summary_and_forwards_args(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}
    expected_config = object()
    session_sentinel = object()

    class DummyConfig:
        @classmethod
        def from_settings(cls, **kwargs):
            captured["config_kwargs"] = kwargs
            return expected_config

    class DummySessionFactory:
        def __call__(self):
            return self

        def __enter__(self):
            return session_sentinel

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyService:
        def __init__(self, session):
            captured["session"] = session

        def ingest(self, config, *, progress_callback=None):
            captured["config"] = config
            captured["progress_callback"] = progress_callback
            return IngestionSummary(
                source_rows_processed=3,
                papers_upserted=2,
                topics_upserted=1,
            )

    monkeypatch.setattr(cli, "IngestionConfig", DummyConfig)
    monkeypatch.setattr(cli, "CsvIngestionService", DummyService)
    monkeypatch.setattr(cli, "get_session_factory", lambda: DummySessionFactory())

    exit_code = cli.main(
        [
            "--csv-path",
            "papers.csv",
            "--citation-csv-path",
            "citations.csv",
            "--batch-size",
            "25",
            "--limit",
            "3",
        ]
    )

    assert exit_code == 0
    assert captured["session"] is session_sentinel
    assert captured["config"] is expected_config
    assert captured["progress_callback"] is cli.print_progress
    assert captured["config_kwargs"] == {
        "csv_path": "papers.csv",
        "citation_csv_path": "citations.csv",
        "batch_size": 25,
        "limit": 3,
    }

    assert json.loads(capsys.readouterr().out) == {
        "authors_upserted": 0,
        "authorships_upserted": 0,
        "citation_import_skipped": True,
        "citations_skipped_missing_papers": 0,
        "citations_upserted": 0,
        "institutions_upserted": 0,
        "papers_upserted": 2,
        "source_rows_processed": 3,
        "source_rows_skipped": 0,
        "topics_upserted": 1,
    }


def test_ingestion_cli_prints_progress_to_stderr(capsys) -> None:
    cli.print_progress(
        IngestionProgress(
            phase="metadata",
            metadata_rows_processed=5,
            metadata_rows_total=10,
            citation_rows_processed=0,
            citation_rows_total=4,
            source_rows_skipped=1,
            papers_upserted=4,
            citations_upserted=0,
            citations_skipped_missing_papers=0,
            elapsed_seconds=3,
            estimated_remaining_seconds=3,
        )
    )
    cli.print_progress(
        IngestionProgress(
            phase="citations",
            metadata_rows_processed=10,
            metadata_rows_total=10,
            citation_rows_processed=2,
            citation_rows_total=4,
            source_rows_skipped=1,
            papers_upserted=4,
            citations_upserted=2,
            citations_skipped_missing_papers=1,
            elapsed_seconds=5,
            estimated_remaining_seconds=5,
        )
    )

    assert capsys.readouterr().err == (
        "Ingestion metadata: rows 5/10, valid 4, skipped 1, "
        "papers upserted 4, elapsed 3s, eta 3s\n"
        "Ingestion citations: rows 2/4, citations upserted 2, "
        "skipped missing papers 1, elapsed 5s, eta 5s\n"
    )
