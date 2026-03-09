import csv
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass(frozen=True, slots=True)
class CitationGraphExportConfig:
    dataset_csv_path: Path
    query_csv_path: Path
    works_jsonl_path: Path
    edge_pairs_csv_path: Path
    progress_path: Path
    batch_size: int = 50
    rate_interval: float = 0.2
    email: str = ""
    limit: int | None = None
    quiet: bool = False
    reset: bool = False


@dataclass(frozen=True, slots=True)
class CitationGraphProgress:
    batches_completed: int
    batches_total: int
    papers_fetched: int
    papers_total: int
    edges_exported: int
    elapsed_seconds: int
    estimated_remaining_seconds: int | None


@dataclass(frozen=True, slots=True)
class CitationGraphExportSummary:
    batches_completed: int
    batches_total: int
    papers_fetched: int
    papers_selected: int
    edges_exported: int
    query_csv_path: str
    works_jsonl_path: str
    edge_pairs_csv_path: str
    progress_path: str


def iter_dataset_paper_ids(csv_path: Path, *, limit: int | None = None) -> list[str]:
    seen_ids: set[str] = set()
    paper_ids: list[str] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            paper_id = (row.get("id") or "").strip()
            if not paper_id or paper_id in seen_ids:
                continue
            seen_ids.add(paper_id)
            paper_ids.append(paper_id)
            if limit is not None and len(paper_ids) >= limit:
                break

    return paper_ids


def chunk_paper_ids(paper_ids: Sequence[str], batch_size: int) -> list[list[str]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    return [
        list(paper_ids[index : index + batch_size])
        for index in range(0, len(paper_ids), batch_size)
    ]


def build_openalex_filter(paper_ids: Sequence[str]) -> str:
    if not paper_ids:
        raise ValueError("paper_ids must contain at least one work id")
    return "openalex:" + "|".join(paper_ids)


def write_query_file(
    output_path: Path,
    paper_ids: Sequence[str],
    *,
    batch_size: int,
) -> int:
    queries = chunk_paper_ids(paper_ids, batch_size)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["filter", "maxentities"])
        writer.writeheader()
        for batch in queries:
            writer.writerow(
                {
                    "filter": build_openalex_filter(batch),
                    "maxentities": len(batch),
                }
            )

    return len(queries)


def extract_citation_edges(
    work: dict[str, object],
    allowed_paper_ids: set[str],
) -> list[tuple[str, str]]:
    citing_paper_id = str(work.get("id") or "").strip()
    if not citing_paper_id:
        return []

    edges: list[tuple[str, str]] = []
    for referenced_work in work.get("referenced_works") or []:
        cited_paper_id = str(referenced_work).strip()
        if cited_paper_id in allowed_paper_ids:
            edges.append((citing_paper_id, cited_paper_id))

    return edges


def minimize_work_record(work: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(work.get("id") or "").strip(),
        "referenced_works": [
            str(referenced_work).strip()
            for referenced_work in work.get("referenced_works") or []
            if str(referenced_work).strip()
        ],
    }


def write_edge_pairs_csv(
    output_path: Path,
    works: Sequence[dict[str, object]],
    *,
    allowed_paper_ids: set[str],
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    edges_written = 0

    with output_path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=["citing_paper_id", "cited_paper_id"],
        )
        writer.writeheader()

        for work in works:
            for citing_paper_id, cited_paper_id in extract_citation_edges(
                work,
                allowed_paper_ids,
            ):
                writer.writerow(
                    {
                        "citing_paper_id": citing_paper_id,
                        "cited_paper_id": cited_paper_id,
                    }
                )
                edges_written += 1

    return edges_written


def append_works_jsonl(output_path: Path, works: Sequence[dict[str, object]]) -> None:
    if not works:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8", newline="\n") as handle:
        for work in works:
            handle.write(json.dumps(minimize_work_record(work), sort_keys=True))
            handle.write("\n")


def load_existing_works(works_jsonl_path: Path) -> list[dict[str, object]]:
    if not works_jsonl_path.exists():
        return []

    work_records: list[dict[str, object]] = []
    seen_paper_ids: set[str] = set()

    with works_jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            work = json.loads(stripped)
            minimized_work = minimize_work_record(work)
            paper_id = str(minimized_work.get("id") or "").strip()
            if not paper_id or paper_id in seen_paper_ids:
                continue
            seen_paper_ids.add(paper_id)
            work_records.append(minimized_work)

    return work_records


def _fetch_openalex_batch(
    paper_ids: Sequence[str],
    *,
    email: str,
    rate_interval: float,
) -> list[dict[str, object]]:
    try:
        from openalexnet.api import OpenAlexAPI
    except ImportError as exc:  # pragma: no cover - exercised in runtime usage
        raise RuntimeError(
            "openalexnet is not installed. Install it with "
            "`python -m pip install -r requirements-dev.txt` or "
            "`python -m pip install -e \".[graph]\"`."
        ) from exc

    openalex = OpenAlexAPI(email=email or None)
    return list(
        openalex.getEntities(
            "works",
            filter=build_openalex_filter(paper_ids),
            maxEntities=len(paper_ids),
            rateInterval=rate_interval,
        )
    )


def write_progress_file(
    progress_path: Path,
    progress: CitationGraphProgress,
) -> None:
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(
        json.dumps(asdict(progress), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _build_progress(
    *,
    batches_completed: int,
    batches_total: int,
    papers_fetched: int,
    papers_total: int,
    edges_exported: int,
    started_at: float,
    fetched_batches_this_run: int,
) -> CitationGraphProgress:
    elapsed_seconds = int(time.monotonic() - started_at)
    estimated_remaining_seconds: int | None = None
    if fetched_batches_this_run > 0:
        average_batch_seconds = elapsed_seconds / fetched_batches_this_run
        remaining_batches = max(batches_total - batches_completed, 0)
        estimated_remaining_seconds = int(average_batch_seconds * remaining_batches)

    return CitationGraphProgress(
        batches_completed=batches_completed,
        batches_total=batches_total,
        papers_fetched=papers_fetched,
        papers_total=papers_total,
        edges_exported=edges_exported,
        elapsed_seconds=elapsed_seconds,
        estimated_remaining_seconds=estimated_remaining_seconds,
    )


class CitationGraphExportService:
    def export(
        self,
        config: CitationGraphExportConfig,
        *,
        progress_callback: Callable[[CitationGraphProgress], None] | None = None,
    ) -> CitationGraphExportSummary:
        paper_ids = iter_dataset_paper_ids(
            config.dataset_csv_path,
            limit=config.limit,
        )
        started_at = time.monotonic()
        batches = chunk_paper_ids(paper_ids, config.batch_size)
        allowed_paper_ids = set(paper_ids)
        queries_written = write_query_file(
            config.query_csv_path,
            paper_ids,
            batch_size=config.batch_size,
        )

        if config.reset:
            for path in (
                config.works_jsonl_path,
                config.edge_pairs_csv_path,
                config.progress_path,
            ):
                if path.exists():
                    path.unlink()

        all_existing_works = load_existing_works(config.works_jsonl_path)
        if all_existing_works:
            config.works_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with config.works_jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
                for work in all_existing_works:
                    handle.write(json.dumps(work, sort_keys=True))
                    handle.write("\n")
        existing_works = [
            work
            for work in all_existing_works
            if str(work.get("id") or "").strip() in allowed_paper_ids
        ]
        fetched_paper_ids = {
            str(work.get("id") or "").strip()
            for work in existing_works
            if str(work.get("id") or "").strip()
        }
        edges_exported = write_edge_pairs_csv(
            config.edge_pairs_csv_path,
            existing_works,
            allowed_paper_ids=allowed_paper_ids,
        )

        batches_completed = sum(
            1 for batch in batches if all(paper_id in fetched_paper_ids for paper_id in batch)
        )
        fetched_batches_this_run = 0
        progress = _build_progress(
            batches_completed=batches_completed,
            batches_total=queries_written,
            papers_fetched=len(fetched_paper_ids),
            papers_total=len(paper_ids),
            edges_exported=edges_exported,
            started_at=started_at,
            fetched_batches_this_run=fetched_batches_this_run,
        )
        write_progress_file(config.progress_path, progress)
        if progress_callback is not None:
            progress_callback(progress)

        for batch in batches:
            if all(paper_id in fetched_paper_ids for paper_id in batch):
                continue

            fetched_works = _fetch_openalex_batch(
                batch,
                email=config.email,
                rate_interval=config.rate_interval,
            )

            new_works = [
                minimize_work_record(work)
                for work in fetched_works
                if str(work.get("id") or "").strip() not in fetched_paper_ids
            ]
            append_works_jsonl(config.works_jsonl_path, new_works)

            if new_works:
                with config.edge_pairs_csv_path.open(
                    "a",
                    encoding="utf-8",
                    newline="",
                ) as destination:
                    writer = csv.DictWriter(
                        destination,
                        fieldnames=["citing_paper_id", "cited_paper_id"],
                    )
                    for work in new_works:
                        paper_id = str(work.get("id") or "").strip()
                        if paper_id:
                            fetched_paper_ids.add(paper_id)
                        for citing_paper_id, cited_paper_id in extract_citation_edges(
                            work,
                            allowed_paper_ids,
                        ):
                            writer.writerow(
                                {
                                    "citing_paper_id": citing_paper_id,
                                    "cited_paper_id": cited_paper_id,
                                }
                            )
                            edges_exported += 1

            batches_completed += 1
            fetched_batches_this_run += 1
            progress = _build_progress(
                batches_completed=batches_completed,
                batches_total=queries_written,
                papers_fetched=len(fetched_paper_ids),
                papers_total=len(paper_ids),
                edges_exported=edges_exported,
                started_at=started_at,
                fetched_batches_this_run=fetched_batches_this_run,
            )
            write_progress_file(config.progress_path, progress)
            if progress_callback is not None:
                progress_callback(progress)

        return CitationGraphExportSummary(
            batches_completed=batches_completed,
            batches_total=queries_written,
            papers_fetched=len(fetched_paper_ids),
            papers_selected=len(paper_ids),
            edges_exported=edges_exported,
            query_csv_path=str(config.query_csv_path),
            works_jsonl_path=str(config.works_jsonl_path),
            edge_pairs_csv_path=str(config.edge_pairs_csv_path),
            progress_path=str(config.progress_path),
        )
