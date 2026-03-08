from dataclasses import dataclass
from pathlib import Path

from research_assistant_api.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    csv_path: Path
    citation_csv_path: Path | None
    batch_size: int
    limit: int | None = None

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        csv_path: str | Path | None = None,
        citation_csv_path: str | Path | None = None,
        batch_size: int | None = None,
        limit: int | None = None,
    ) -> "IngestionConfig":
        resolved_settings = settings or get_settings()
        return cls(
            csv_path=Path(csv_path or resolved_settings.dataset_csv_path),
            citation_csv_path=(
                Path(citation_csv_path)
                if citation_csv_path
                else resolved_settings.citation_edges_csv_path
            ),
            batch_size=batch_size or resolved_settings.ingestion_batch_size,
            limit=limit,
        )
