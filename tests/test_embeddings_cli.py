import json

from research_assistant_api.embeddings import cli
from research_assistant_api.embeddings.service import EmbeddingGenerationSummary


def test_embeddings_cli_prints_summary_and_forwards_args(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}
    session_sentinel = object()

    class DummySettings:
        embedding_model_name = "test-model"
        embedding_batch_size = 16

    class DummySessionFactory:
        def __call__(self):
            return self

        def __enter__(self):
            return session_sentinel

        def __exit__(self, exc_type, exc, tb):
            return False

    class DummyEmbedder:
        def __init__(self, model_name, batch_size):
            captured["model_name"] = model_name
            captured["batch_size"] = batch_size

    class DummyService:
        def __init__(self, repository, embedder):
            captured["repository"] = repository
            captured["embedder"] = embedder

        def generate_embeddings(self, *, limit, paper_id, force):
            captured["generate_kwargs"] = {
                "limit": limit,
                "paper_id": paper_id,
                "force": force,
            }
            return EmbeddingGenerationSummary(papers_selected=2, papers_embedded=2)

    monkeypatch.setattr(cli, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(cli, "get_session_factory", lambda: DummySessionFactory())
    monkeypatch.setattr(cli, "SentenceTransformerEmbedder", DummyEmbedder)
    monkeypatch.setattr(cli, "PaperEmbeddingService", DummyService)
    monkeypatch.setattr(cli, "EmbeddingRepository", lambda session: session)

    exit_code = cli.main(["--paper-id", "paper-1", "--limit", "2", "--force"])

    assert exit_code == 0
    assert captured["model_name"] == "test-model"
    assert captured["batch_size"] == 16
    assert captured["repository"] is session_sentinel
    assert captured["generate_kwargs"] == {
        "limit": 2,
        "paper_id": "paper-1",
        "force": True,
    }
    assert json.loads(capsys.readouterr().out) == {
        "papers_embedded": 2,
        "papers_selected": 2,
    }
