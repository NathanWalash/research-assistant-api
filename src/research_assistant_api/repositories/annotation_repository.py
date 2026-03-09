from sqlalchemy import desc, select
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

    def list_for_user_and_paper(
        self,
        *,
        user_id: str,
        paper_id: str,
        limit: int,
        offset: int,
    ) -> list[Annotation]:
        statement = (
            select(Annotation)
            .where(
                Annotation.user_id == user_id,
                Annotation.paper_id == paper_id,
            )
            .order_by(desc(Annotation.created_at), desc(Annotation.id))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def get_for_user(self, annotation_id: str, user_id: str) -> Annotation | None:
        statement = select(Annotation).where(
            Annotation.id == annotation_id,
            Annotation.user_id == user_id,
        )
        return self.session.scalar(statement)

    def update(self, annotation: Annotation, *, text: str) -> Annotation:
        annotation.text = text
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        return annotation

    def delete(self, annotation: Annotation) -> None:
        self.session.delete(annotation)
        self.session.commit()
