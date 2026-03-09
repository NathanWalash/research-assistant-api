from research_assistant_api.schemas.discovery import PaperSummary


class SimilarPaperResponse(PaperSummary):
    similarity_score: float
