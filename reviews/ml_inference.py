from pathlib import Path
from typing import Any

import joblib
from django.conf import settings

ML_DIR = Path(settings.BASE_DIR) / "ml"
VECTORIZER_PATH = ML_DIR / "sentiment_vectorizer.joblib"
MODEL_PATH = ML_DIR / "sentiment_model.joblib"
LABELS_PATH = ML_DIR / "sentiment_labels.joblib"

_ARTIFACTS: tuple[Any, Any, list[str]] | None = None


def model_files_exist() -> bool:
    return (
        VECTORIZER_PATH.exists()
        and MODEL_PATH.exists()
        and LABELS_PATH.exists()
    )


def load_model_artifacts():
    global _ARTIFACTS

    if _ARTIFACTS is not None:
        return _ARTIFACTS

    if not model_files_exist():
        raise RuntimeError(
            "Sentiment model artifacts are missing. "
            "Run: python scripts/train_sentiment_model.py"
        )

    vectorizer = joblib.load(VECTORIZER_PATH)
    model = joblib.load(MODEL_PATH)
    labels = joblib.load(LABELS_PATH)
    _ARTIFACTS = (vectorizer, model, labels)
    return _ARTIFACTS


def predict_sentiment(text: str) -> str:
    if not text or not str(text).strip():
        return ""

    vectorizer, model, labels = load_model_artifacts()

    from reviews.text_preprocess import preprocess_pipeline

    processed_text = preprocess_pipeline(str(text))
    if not processed_text:
        return ""

    vector = vectorizer.transform([processed_text])
    prediction = model.predict(vector)[0]
    prediction = str(prediction)

    if prediction not in labels:
        raise RuntimeError(f"Sentiment model returned unknown label: {prediction}")

    return prediction
