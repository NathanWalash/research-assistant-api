import json

from research_assistant_api.ingestion import cli
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

        def ingest(self, config):
            captured["config"] = config
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
