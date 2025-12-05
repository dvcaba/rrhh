import importlib
from types import ModuleType
from typing import Tuple

import numpy as np


def _stub_embedder(monkeypatch) -> Tuple[ModuleType, ModuleType]:
    """
    Replace SentenceTransformer with a lightweight stub and reload modules
    so ranker features don't try to load the real model during tests.
    """
    from smart_filtering.embedder import embed as embed_mod  # type: ignore

    class DummySentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return np.zeros((1, 5))
            return np.zeros((len(texts), 5))

    monkeypatch.setattr(embed_mod, "SentenceTransformer", DummySentenceTransformer)
    importlib.reload(embed_mod)

    # Reload ranker modules so they pick the stubbed embedder
    from smart_filtering.ranker import features as features_mod  # type: ignore
    from smart_filtering.ranker import score as score_mod  # type: ignore

    importlib.reload(features_mod)
    importlib.reload(score_mod)

    # Inject a stub embedder instance on the reloaded features module
    features_mod.embedder = embed_mod.get_embedder()
    return features_mod, score_mod


def _sample_cv():
    return {
        "id": "cv_test",
        "name": "Test User",
        "title": "Data Engineer",
        "experience_years_total": 3,
        "skills": {"python": "advanced", "sql": "intermediate"},
        "experiences": [],
        "education": ["BSc Computer Science"],
        "languages": {"es": "native"},
        "certs": [],
        "location": {"city": "Remote", "country": "ES", "lat": 0.0, "lon": 0.0},
        "remote_preference": "remote",
    }


def _sample_jd():
    return {
        "id": "jd_test",
        "role": "Data Engineer",
        "min_total_years": 2,
        "must_have": ["python"],
        "nice_to_have": ["sql"],
        "min_skill_years": {},
        "location_policy": {"type": "remote", "city": "Remote", "max_km": 0},
        "weights": {
            "skill_semantic": 0.4,
            "title_semantic": 0.2,
            "experience": 0.2,
            "location": 0.1,
            "education": 0.1,
        },
    }


def test_score_positive_when_meeting_requirements(monkeypatch):
    features_mod, score_mod = _stub_embedder(monkeypatch)
    cv = _sample_cv()
    jd = _sample_jd()

    result = score_mod.calculate_score(cv, jd)

    assert result["score"] > 0
    assert result["features"]["must_have_coverage"] == 1.0


def test_score_penalizes_missing_must_have(monkeypatch):
    features_mod, score_mod = _stub_embedder(monkeypatch)
    cv = _sample_cv()
    cv["skills"] = {"excel": "advanced"}  # remove python
    jd = _sample_jd()

    result_missing = score_mod.calculate_score(cv, jd)

    assert result_missing["features"]["must_have_coverage"] == 0
    assert result_missing["score"] < 0.5
