import json

from research_assistant_api.citation_graph import cli
from research_assistant_api.citation_graph.service import CitationGraphProgress
from research_assistant_api.citation_graph.service import CitationGraphExportSummary


def test_citation_graph_cli_prints_summary_and_forwards_args(
    monkeypatch,
    capsys,
) -> None:
    captured: dict[str, object] = {}

    class DummySettings:
        dataset_csv_path = "default-dataset.csv"

    class DummyService:
        def export(self, config, *, progress_callback):
            captured["config"] = config
            captured["progress_callback"] = progress_callback
            return CitationGraphExportSummary(
                batches_completed=1,
                batches_total=1,
                papers_fetched=3,
                papers_selected=3,
                edges_exported=2,
                query_csv_path=str(config.query_csv_path),
                works_jsonl_path=str(config.works_jsonl_path),
                edge_pairs_csv_path=str(config.edge_pairs_csv_path),
                progress_path=str(config.progress_path),
            )

    monkeypatch.setattr(cli, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(cli, "CitationGraphExportService", DummyService)

    exit_code = cli.main(
        [
            "--batch-size",
            "25",
            "--limit",
            "3",
            "--rate-interval",
            "0.5",
            "--email",
            "me@example.com",
            "--quiet",
            "--reset",
        ]
    )

    assert exit_code == 0
    config = captured["config"]
    assert str(config.dataset_csv_path) == "default-dataset.csv"
    assert str(config.query_csv_path) == ".tmp\\leeds_citation_queries.csv"
    assert config.batch_size == 25
    assert config.limit == 3
    assert config.rate_interval == 0.5
    assert config.email == "me@example.com"
    assert config.quiet is True
    assert config.reset is True
    assert json.loads(capsys.readouterr().out) == {
        "batches_completed": 1,
        "batches_total": 1,
        "edge_pairs_csv_path": ".tmp\\leeds_citation_edges.csv",
        "edges_exported": 2,
        "papers_fetched": 3,
        "papers_selected": 3,
        "progress_path": ".tmp\\leeds_citation_progress.json",
        "query_csv_path": ".tmp\\leeds_citation_queries.csv",
        "works_jsonl_path": ".tmp\\leeds_citation_works.jsonl",
    }


def test_citation_graph_print_progress_writes_single_line(capsys) -> None:
    cli.print_progress(
        CitationGraphProgress(
            batches_completed=12,
            batches_total=638,
            papers_fetched=600,
            papers_total=31856,
            edges_exported=123,
        )
    )

    assert (
        capsys.readouterr().err
        == "Fetched batches 12/638, papers 600/31856, edges 123\n"
    )
