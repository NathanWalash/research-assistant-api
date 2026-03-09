from datetime import datetime

from pydantic import BaseModel, Field


class AnnotationCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class AnnotationResponse(BaseModel):
    id: str
    user_id: str
    paper_id: str
    text: str
    created_at: datetime
