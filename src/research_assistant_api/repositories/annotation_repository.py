from sqlalchemy.orm import Session

from research_assistant_api.models import Annotation


class AnnotationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, user_id: str, paper_id: str, text: str) -> Annotation:
        annotation = Annotation(user_id=user_id, paper_id=paper_id, text=text)
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        return annotation
