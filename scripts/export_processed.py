import os
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from django.conf import settings
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reviews_project.settings")
application = get_wsgi_application()

from reviews.models import Review  # noqa: E402


def main(limit: int | None = None):
    qs = Review.objects.all().order_by("-created_at")
    if limit:
        qs = qs[:limit]
    rows = []
    for r in qs:
        rows.append(
            {
                "id": r.id,
                "date": r.date.isoformat() if r.date else "",
                "region": r.region,
                "product_category": r.product_category,
                "gender": r.gender,
                "age": r.age if r.age is not None else "",
                "source": r.source,
                "review_text": r.review_text,
                "processed_text": r.processed_text,
                "sentiment": r.sentiment,
            }
        )
    df = pd.DataFrame(rows)
    out_dir = os.path.join(settings.BASE_DIR, "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "processed_reviews.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Экспортировано: {len(df)} строк -> {out_path}")


if __name__ == "__main__":
    main(limit=None)
