import json
from pathlib import Path

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
    assert Path(config.dataset_csv_path) == Path("default-dataset.csv")
    assert Path(config.query_csv_path) == Path(".tmp/leeds_citation_queries.csv")
    assert config.batch_size == 25
    assert config.limit == 3
    assert config.rate_interval == 0.5
    assert config.email == "me@example.com"
    assert config.quiet is True
    assert config.reset is True
    body = json.loads(capsys.readouterr().out)
    assert body["batches_completed"] == 1
    assert body["batches_total"] == 1
    assert body["edges_exported"] == 2
    assert body["papers_fetched"] == 3
    assert body["papers_selected"] == 3
    assert Path(body["edge_pairs_csv_path"]) == Path(".tmp/leeds_citation_edges.csv")
    assert Path(body["progress_path"]) == Path(".tmp/leeds_citation_progress.json")
    assert Path(body["query_csv_path"]) == Path(".tmp/leeds_citation_queries.csv")
    assert Path(body["works_jsonl_path"]) == Path(".tmp/leeds_citation_works.jsonl")


def test_citation_graph_print_progress_writes_single_line(capsys) -> None:
    cli.print_progress(
        CitationGraphProgress(
            batches_completed=12,
            batches_total=638,
            papers_fetched=600,
            papers_total=31856,
            edges_exported=123,
            elapsed_seconds=90,
            estimated_remaining_seconds=1200,
        )
    )

    assert (
        capsys.readouterr().err
        == "Fetched batches 12/638, papers 600/31856, edges 123, elapsed 90s, eta 1200s\n"
    )
