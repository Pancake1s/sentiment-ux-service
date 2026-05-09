import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reviews_project.settings")

from reviews.text_preprocess import preprocess_pipeline  # noqa: E402


DATASET_PATH = BASE_DIR / "data" / "women-clothing-accessories.3-class.balanced.csv"
ML_DIR = BASE_DIR / "ml"
VECTORIZER_PATH = ML_DIR / "sentiment_vectorizer.joblib"
MODEL_PATH = ML_DIR / "sentiment_model.joblib"
LABELS_PATH = ML_DIR / "sentiment_labels.joblib"

REQUIRED_COLUMNS = {"review", "sentiment"}
LABEL_FIXES = {"neautral": "neutral"}
ALLOWED_LABELS = ["negative", "neutral", "positive"]
QUICK_TEST_PHRASES = [
    "Ужасное качество, больше не куплю",
    "Нормальный товар, ничего особенного",
    "Очень понравилось, буду заказывать ещё",
]


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path, sep="\t")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Dataset is missing required columns: {missing_list}")

    df = df[["review", "sentiment"]].copy()
    df["review"] = df["review"].fillna("").astype(str).str.strip()
    df["sentiment"] = (
        df["sentiment"].fillna("").astype(str).str.strip().str.lower().replace(LABEL_FIXES)
    )
    df = df[df["sentiment"].isin(ALLOWED_LABELS)]
    df = df[df["review"] != ""]
    df = df.drop_duplicates(subset=["review", "sentiment"]).reset_index(drop=True)

    if df.empty:
        raise ValueError("Dataset has no valid rows after cleaning.")

    return df


def preprocess_reviews(reviews: pd.Series) -> list[str]:
    return [preprocess_pipeline(text) for text in reviews]


def main() -> None:
    print(f"Reading dataset: {DATASET_PATH}")
    df = load_dataset(DATASET_PATH)

    print(f"Rows after cleaning: {len(df)}")
    print("Class distribution:")
    print(df["sentiment"].value_counts().reindex(ALLOWED_LABELS, fill_value=0))

    print("Preprocessing reviews...")
    X = preprocess_reviews(df["review"])
    y = df["sentiment"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    vectorizer = TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2)
    model = LogisticRegression(max_iter=2000, class_weight="balanced", n_jobs=-1)

    print("Vectorizing train data...")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("Training LogisticRegression...")
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"Accuracy: {accuracy:.4f}")
    print("Classification report:")
    print(classification_report(y_test, y_pred, labels=ALLOWED_LABELS))
    print("Confusion matrix:")
    print(pd.DataFrame(confusion_matrix(y_test, y_pred, labels=ALLOWED_LABELS), index=ALLOWED_LABELS, columns=ALLOWED_LABELS))

    ML_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(ALLOWED_LABELS, LABELS_PATH)

    print("Saved artifacts:")
    print(f"- {VECTORIZER_PATH}")
    print(f"- {MODEL_PATH}")
    print(f"- {LABELS_PATH}")

    print("Quick test:")
    quick_processed = preprocess_reviews(pd.Series(QUICK_TEST_PHRASES))
    quick_vectors = vectorizer.transform(quick_processed)
    quick_predictions = model.predict(quick_vectors)
    for phrase, label in zip(QUICK_TEST_PHRASES, quick_predictions):
        print(f"- {phrase} -> {label}")


if __name__ == "__main__":
    main()
