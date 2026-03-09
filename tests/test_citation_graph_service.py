import csv
import json
from pathlib import Path
from uuid import uuid4

import pytest

from research_assistant_api.citation_graph import service
from research_assistant_api.citation_graph.service import CitationGraphExportConfig
from research_assistant_api.citation_graph.service import CitationGraphProgress
from research_assistant_api.citation_graph.service import CitationGraphExportService
from research_assistant_api.citation_graph.service import build_openalex_filter
from research_assistant_api.citation_graph.service import chunk_paper_ids
from research_assistant_api.citation_graph.service import extract_citation_edges
from research_assistant_api.citation_graph.service import iter_dataset_paper_ids
from research_assistant_api.citation_graph.service import load_existing_works
from research_assistant_api.citation_graph.service import write_query_file


def make_repo_temp_dir() -> Path:
    path = Path(".tmp") / f"citation-graph-tests-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_iter_dataset_paper_ids_deduplicates_and_skips_missing() -> None:
    csv_path = make_repo_temp_dir() / "papers.csv"
    csv_path.write_text(
        "id,display_name\n"
        "https://openalex.org/W1,Paper 1\n"
        ",Missing Id\n"
        "https://openalex.org/W1,Duplicate\n"
        "https://openalex.org/W2,Paper 2\n",
        encoding="utf-8",
    )

    assert iter_dataset_paper_ids(csv_path) == [
        "https://openalex.org/W1",
        "https://openalex.org/W2",
    ]


def test_chunk_paper_ids_rejects_non_positive_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size"):
        chunk_paper_ids(["https://openalex.org/W1"], 0)


def test_build_openalex_filter_joins_exact_ids() -> None:
    assert build_openalex_filter(
        ["https://openalex.org/W1", "https://openalex.org/W2"]
    ) == "openalex:https://openalex.org/W1|https://openalex.org/W2"


def test_write_query_file_batches_exact_ids() -> None:
    output_path = make_repo_temp_dir() / "queries.csv"

    query_count = write_query_file(
        output_path,
        [
            "https://openalex.org/W1",
            "https://openalex.org/W2",
            "https://openalex.org/W3",
        ],
        batch_size=2,
    )

    assert query_count == 2
    with output_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "filter": "openalex:https://openalex.org/W1|https://openalex.org/W2",
            "maxentities": "2",
        },
        {
            "filter": "openalex:https://openalex.org/W3",
            "maxentities": "1",
        },
    ]


def test_extract_citation_edges_filters_to_leeds_subset() -> None:
    assert extract_citation_edges(
        {
            "id": "https://openalex.org/W1",
            "referenced_works": [
                "https://openalex.org/W2",
                "https://openalex.org/W999",
            ],
        },
        {"https://openalex.org/W1", "https://openalex.org/W2"},
    ) == [
        ("https://openalex.org/W1", "https://openalex.org/W2"),
    ]


def test_load_existing_works_deduplicates_existing_jsonl() -> None:
    temp_dir = make_repo_temp_dir()
    works_jsonl_path = temp_dir / "works.jsonl"
    works_jsonl_path.write_text(
        json.dumps({"id": "https://openalex.org/W1", "referenced_works": []})
        + "\n"
        + json.dumps({"id": "https://openalex.org/W1", "referenced_works": []})
        + "\n"
        + json.dumps({"id": "https://openalex.org/W2", "referenced_works": []})
        + "\n",
        encoding="utf-8",
    )

    assert [work["id"] for work in load_existing_works(works_jsonl_path)] == [
        "https://openalex.org/W1",
        "https://openalex.org/W2",
    ]


def test_export_service_runs_openalexnet_and_converts_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_dir = make_repo_temp_dir()
    dataset_csv_path = temp_dir / "papers.csv"
    dataset_csv_path.write_text(
        "id,display_name\n"
        "https://openalex.org/W1,Paper 1\n"
        "https://openalex.org/W2,Paper 2\n",
        encoding="utf-8",
    )
    config = CitationGraphExportConfig(
        dataset_csv_path=dataset_csv_path,
        query_csv_path=temp_dir / "queries.csv",
        works_jsonl_path=temp_dir / "works.jsonl",
        edge_pairs_csv_path=temp_dir / "citation_edges.csv",
        progress_path=temp_dir / "progress.json",
        batch_size=50,
    )
    progress_updates: list[CitationGraphProgress] = []

    def fake_fetch_batch(paper_ids, *, email, rate_interval):
        assert paper_ids == [
            "https://openalex.org/W1",
            "https://openalex.org/W2",
        ]
        assert email == ""
        assert rate_interval == 0.2
        return [
            {
                "id": "https://openalex.org/W1",
                "referenced_works": ["https://openalex.org/W2"],
            },
            {
                "id": "https://openalex.org/W2",
                "referenced_works": [],
            },
        ]

    monkeypatch.setattr(service, "_fetch_openalex_batch", fake_fetch_batch)

    summary = CitationGraphExportService().export(
        config,
        progress_callback=progress_updates.append,
    )

    assert summary.papers_selected == 2
    assert summary.papers_fetched == 2
    assert summary.batches_completed == 1
    assert summary.batches_total == 1
    assert summary.edges_exported == 1
    with config.edge_pairs_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "citing_paper_id": "https://openalex.org/W1",
            "cited_paper_id": "https://openalex.org/W2",
        }
    ]
    assert progress_updates == [
        CitationGraphProgress(
            batches_completed=0,
            batches_total=1,
            papers_fetched=0,
            papers_total=2,
            edges_exported=0,
            elapsed_seconds=0,
            estimated_remaining_seconds=None,
        ),
        CitationGraphProgress(
            batches_completed=1,
            batches_total=1,
            papers_fetched=2,
            papers_total=2,
            edges_exported=1,
            elapsed_seconds=0,
            estimated_remaining_seconds=0,
        ),
    ]


def test_export_service_resumes_from_existing_jsonl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_dir = make_repo_temp_dir()
    dataset_csv_path = temp_dir / "papers.csv"
    dataset_csv_path.write_text(
        "id,display_name\n"
        "https://openalex.org/W1,Paper 1\n"
        "https://openalex.org/W2,Paper 2\n"
        "https://openalex.org/W3,Paper 3\n",
        encoding="utf-8",
    )
    works_jsonl_path = temp_dir / "works.jsonl"
    works_jsonl_path.write_text(
        json.dumps(
            {
                "id": "https://openalex.org/W1",
                "referenced_works": ["https://openalex.org/W2"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = CitationGraphExportConfig(
        dataset_csv_path=dataset_csv_path,
        query_csv_path=temp_dir / "queries.csv",
        works_jsonl_path=works_jsonl_path,
        edge_pairs_csv_path=temp_dir / "citation_edges.csv",
        progress_path=temp_dir / "progress.json",
        batch_size=2,
    )

    calls: list[list[str]] = []

    def fake_fetch_batch(paper_ids, *, email, rate_interval):
        calls.append(list(paper_ids))
        if paper_ids == ["https://openalex.org/W1", "https://openalex.org/W2"]:
            return [
                {
                    "id": "https://openalex.org/W1",
                    "referenced_works": ["https://openalex.org/W2"],
                },
                {
                    "id": "https://openalex.org/W2",
                    "referenced_works": ["https://openalex.org/W3"],
                },
            ]
        return [
            {
                "id": "https://openalex.org/W3",
                "referenced_works": [],
            }
        ]

    monkeypatch.setattr(service, "_fetch_openalex_batch", fake_fetch_batch)

    summary = CitationGraphExportService().export(config)

    assert calls == [["https://openalex.org/W1", "https://openalex.org/W2"], ["https://openalex.org/W3"]]
    assert summary.batches_completed == 2
    assert summary.batches_total == 2
    assert summary.papers_fetched == 3
    with config.edge_pairs_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "citing_paper_id": "https://openalex.org/W1",
            "cited_paper_id": "https://openalex.org/W2",
        },
        {
            "citing_paper_id": "https://openalex.org/W2",
            "cited_paper_id": "https://openalex.org/W3",
        },
    ]


def test_export_service_filters_existing_jsonl_to_current_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_dir = make_repo_temp_dir()
    dataset_csv_path = temp_dir / "papers.csv"
    dataset_csv_path.write_text(
        "id,display_name\n"
        "https://openalex.org/W1,Paper 1\n"
        "https://openalex.org/W2,Paper 2\n",
        encoding="utf-8",
    )
    works_jsonl_path = temp_dir / "works.jsonl"
    works_jsonl_path.write_text(
        json.dumps(
            {
                "id": "https://openalex.org/W1",
                "referenced_works": ["https://openalex.org/W2"],
            }
        )
        + "\n"
        + json.dumps(
            {
                "id": "https://openalex.org/W999",
                "referenced_works": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = CitationGraphExportConfig(
        dataset_csv_path=dataset_csv_path,
        query_csv_path=temp_dir / "queries.csv",
        works_jsonl_path=works_jsonl_path,
        edge_pairs_csv_path=temp_dir / "citation_edges.csv",
        progress_path=temp_dir / "progress.json",
        batch_size=50,
        limit=2,
    )

    def fake_fetch_batch(paper_ids, *, email, rate_interval):
        return [
            {
                "id": "https://openalex.org/W2",
                "referenced_works": [],
            }
        ]

    monkeypatch.setattr(service, "_fetch_openalex_batch", fake_fetch_batch)

    summary = CitationGraphExportService().export(config)

    assert summary.papers_fetched == 2
    with config.edge_pairs_csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows == [
        {
            "citing_paper_id": "https://openalex.org/W1",
            "cited_paper_id": "https://openalex.org/W2",
        }
    ]
