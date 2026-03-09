from pydantic import BaseModel

from research_assistant_api.schemas.discovery import PaperSummary


class CitationNeighborhoodResponse(BaseModel):
    paper_id: str
    cited_papers: list[PaperSummary]
    citing_papers: list[PaperSummary]


class CitationPathResponse(BaseModel):
    source_paper_id: str
    target_paper_id: str
    path_length: int
    path: list[PaperSummary]
