from django.core.management.base import BaseCommand

from reviews.ml_inference import predict_sentiment
from reviews.models import Review
from reviews.text_preprocess import preprocess_pipeline


class Command(BaseCommand):
    help = "Apply trained sentiment model to reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch",
            type=int,
            default=1000,
            help="Batch size for bulk_update. Default: 1000.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of reviews to process.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Process all reviews, including reviews with existing sentiment.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch"]
        limit = options["limit"]
        force = options["force"]

        if batch_size <= 0:
            raise ValueError("--batch must be greater than 0")
        if limit is not None and limit <= 0:
            raise ValueError("--limit must be greater than 0")

        qs = Review.objects.all().order_by("id")
        if not force:
            qs = qs.filter(sentiment="")

        total = qs.count()
        if limit is not None:
            total = min(total, limit)
            qs = qs[:limit]

        self.stdout.write(f"Found reviews: {total}")

        processed_count = 0
        buffer = []

        for review in qs.iterator(chunk_size=batch_size):
            text_for_prediction = review.processed_text or review.review_text
            if not review.processed_text:
                review.processed_text = preprocess_pipeline(review.review_text)
                text_for_prediction = review.processed_text

            review.sentiment = predict_sentiment(text_for_prediction)
            buffer.append(review)

            if len(buffer) >= batch_size:
                Review.objects.bulk_update(
                    buffer,
                    ["processed_text", "sentiment"],
                    batch_size=batch_size,
                )
                processed_count += len(buffer)
                self.stdout.write(f"Processed: {processed_count}/{total}")
                buffer.clear()

        if buffer:
            Review.objects.bulk_update(
                buffer,
                ["processed_text", "sentiment"],
                batch_size=batch_size,
            )
            processed_count += len(buffer)
            self.stdout.write(f"Processed: {processed_count}/{total}")

        self.stdout.write(
            self.style.SUCCESS(f"Done: processed {processed_count} reviews.")
        )
