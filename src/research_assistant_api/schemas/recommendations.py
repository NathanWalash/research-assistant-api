from typing import Literal

from research_assistant_api.schemas.discovery import PaperSummary


class ProjectRecommendationResponse(PaperSummary):
    recommendation_score: float
    semantic_score: float
    citation_score: float
    scoring_mode: Literal["semantic", "citation", "hybrid"]
    semantic_weight: float
    citation_weight: float
