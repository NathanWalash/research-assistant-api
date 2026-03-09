from research_assistant_api.repositories.citation_repository import CitationRepository
from research_assistant_api.repositories.paper_repository import PaperRepository
from research_assistant_api.schemas.citations import CitationNeighborhoodResponse
from research_assistant_api.schemas.citations import CitationPathResponse
from research_assistant_api.services.discovery import DiscoveryNotFoundError
from research_assistant_api.services.discovery import _build_paper_summary


class CitationPathNotFoundError(Exception):
    def __init__(self, source_paper_id: str, target_paper_id: str, max_depth: int):
        super().__init__(
            "No citation path found from "
            f"'{source_paper_id}' to '{target_paper_id}' within depth {max_depth}"
        )


class CitationGraphService:
    def __init__(
        self,
        citation_repository: CitationRepository,
        paper_repository: PaperRepository,
    ):
        self.citation_repository = citation_repository
        self.paper_repository = paper_repository

    def get_citation_neighborhood(
        self,
        paper_id: str,
        *,
        limit: int,
        offset: int,
    ) -> CitationNeighborhoodResponse:
        if not self.paper_repository.exists(paper_id):
            raise DiscoveryNotFoundError("paper", paper_id)

        cited_papers = self.citation_repository.list_cited_papers(
            paper_id,
            limit=limit,
            offset=offset,
        )
        citing_papers = self.citation_repository.list_citing_papers(
            paper_id,
            limit=limit,
            offset=offset,
        )
        return CitationNeighborhoodResponse(
            paper_id=paper_id,
            cited_papers=[_build_paper_summary(paper) for paper in cited_papers],
            citing_papers=[_build_paper_summary(paper) for paper in citing_papers],
        )

    def get_citation_path(
        self,
        source_paper_id: str,
        target_paper_id: str,
        *,
        max_depth: int,
    ) -> CitationPathResponse:
        if not self.paper_repository.exists(source_paper_id):
            raise DiscoveryNotFoundError("paper", source_paper_id)
        if not self.paper_repository.exists(target_paper_id):
            raise DiscoveryNotFoundError("paper", target_paper_id)

        if source_paper_id == target_paper_id:
            papers = self.citation_repository.list_papers_by_ids([source_paper_id])
            return CitationPathResponse(
                source_paper_id=source_paper_id,
                target_paper_id=target_paper_id,
                path_length=0,
                path=[_build_paper_summary(papers[0])],
            )

        frontier = [source_paper_id]
        parents: dict[str, str | None] = {source_paper_id: None}
        depth = 0

        while frontier and depth < max_depth:
            next_frontier: list[str] = []
            for citing_paper_id, cited_paper_id in self.citation_repository.list_outgoing_edges(
                frontier
            ):
                if cited_paper_id in parents:
                    continue
                parents[cited_paper_id] = citing_paper_id
                if cited_paper_id == target_paper_id:
                    return self._build_path_response(
                        source_paper_id,
                        target_paper_id,
                        self._reconstruct_path(parents, target_paper_id),
                    )
                next_frontier.append(cited_paper_id)
            frontier = next_frontier
            depth += 1

        raise CitationPathNotFoundError(
            source_paper_id,
            target_paper_id,
            max_depth,
        )

    def _reconstruct_path(
        self,
        parents: dict[str, str | None],
        target_paper_id: str,
    ) -> list[str]:
        path_ids: list[str] = []
        current_paper_id: str | None = target_paper_id
        while current_paper_id is not None:
            path_ids.append(current_paper_id)
            current_paper_id = parents[current_paper_id]
        path_ids.reverse()
        return path_ids

    def _build_path_response(
        self,
        source_paper_id: str,
        target_paper_id: str,
        path_ids: list[str],
    ) -> CitationPathResponse:
        papers_by_id = {
            paper.id: paper
            for paper in self.citation_repository.list_papers_by_ids(path_ids)
        }
        return CitationPathResponse(
            source_paper_id=source_paper_id,
            target_paper_id=target_paper_id,
            path_length=max(len(path_ids) - 1, 0),
            path=[_build_paper_summary(papers_by_id[paper_id]) for paper_id in path_ids],
        )
