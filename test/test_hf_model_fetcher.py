import json

from pipeline.batch_digest import fetch_hf_trending_models
from pipeline.content_strategy import evaluate_candidate


def test_huggingface_model_adapter_normalizes_momentum(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps([{
                "id": "org/Builder-Model",
                "downloads": 42000,
                "likes": 180,
                "trendingScore": 92.5,
                "lastModified": "2026-10-28T12:00:00Z",
                "tags": ["text-generation", "transformers"],
                "description": "A local model for coding agents.",
            }]).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    candidates = fetch_hf_trending_models(limit=1)
    assert candidates[0]["source"] == "huggingface_models"
    assert candidates[0]["model_metadata"]["trending_score"] == 92.5
    decision = evaluate_candidate(candidates[0], reference_date=__import__("datetime").date(2026, 10, 29))
    assert decision.recommended_format == "practical_demo"
    assert decision.eligible
