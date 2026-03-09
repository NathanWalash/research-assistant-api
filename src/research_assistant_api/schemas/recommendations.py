from research_assistant_api.schemas.discovery import PaperSummary


class ProjectRecommendationResponse(PaperSummary):
    recommendation_score: float
