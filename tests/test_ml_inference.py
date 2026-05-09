import pytest
from django.conf import settings

from reviews import ml_inference


def test_model_files_exist_returns_bool():
    assert isinstance(ml_inference.model_files_exist(), bool)


def test_predict_sentiment_empty_text_returns_unknown():
    assert ml_inference.predict_sentiment("") == ""


def test_predict_sentiment_raises_runtime_error_when_files_missing(monkeypatch):
    missing_dir = settings.BASE_DIR / "ml" / "__missing_for_test__"
    monkeypatch.setattr(ml_inference, "_ARTIFACTS", None)
    monkeypatch.setattr(
        ml_inference,
        "VECTORIZER_PATH",
        missing_dir / "missing_vectorizer.joblib",
    )
    monkeypatch.setattr(
        ml_inference,
        "MODEL_PATH",
        missing_dir / "missing_model.joblib",
    )
    monkeypatch.setattr(
        ml_inference,
        "LABELS_PATH",
        missing_dir / "missing_labels.joblib",
    )

    with pytest.raises(RuntimeError, match="Sentiment model artifacts are missing"):
        ml_inference.predict_sentiment("some text")
