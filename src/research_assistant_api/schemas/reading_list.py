from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from research_assistant_api.schemas.discovery import PaperSummary

ReadingListPriority = Literal["low", "medium", "high"]


class ReadingListItemCreateRequest(BaseModel):
    paper_id: str = Field(min_length=1, max_length=255)
    priority: ReadingListPriority = "medium"
    notes: str | None = Field(default=None, max_length=5000)


class ReadingListItemUpdateRequest(BaseModel):
    priority: ReadingListPriority | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ReadingListItemResponse(BaseModel):
    id: str
    project_id: str
    paper_id: str
    priority: ReadingListPriority
    notes: str | None = None
    created_at: datetime
    paper: PaperSummary
