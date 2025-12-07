from django.core.management.base import BaseCommand

from reviews.models import Review
from reviews.text_preprocess import preprocess_pipeline


class Command(BaseCommand):
    help = "Предобработка текстов: заполнить processed_text на основе review_text"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch", type=int, default=1000, help="Размер батча (по умолчанию 1000)"
        )
        parser.add_argument(
            "--only-empty",
            action="store_true",
            help="Обрабатывать только записи, где processed_text пуст",
        )
        parser.add_argument(
            "--no-lemma",
            action="store_true",
            help="Не делать лемматизацию (только чистка+стоп-слова)",
        )

    def handle(self, *args, **opts):
        batch_size = opts["batch"]
        only_empty = opts["only_empty"]
        do_lemma = not opts["no_lemma"]

        qs = Review.objects.all().order_by("id")
        if only_empty:
            qs = qs.filter(processed_text="")

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Найдено записей: {total}"))

        processed = 0
        buf = []

        # итерируемся по батчам, чтобы не держать всё в памяти
        for r in qs.iterator(chunk_size=batch_size):
            r.processed_text = preprocess_pipeline(r.review_text, do_lemmatize=do_lemma)
            buf.append(r)
            if len(buf) >= batch_size:
                Review.objects.bulk_update(
                    buf, ["processed_text"], batch_size=batch_size
                )
                processed += len(buf)
                self.stdout.write(f"Обработано: {processed}/{total}")
                buf.clear()

        if buf:
            Review.objects.bulk_update(buf, ["processed_text"], batch_size=batch_size)
            processed += len(buf)

        self.stdout.write(self.style.SUCCESS(f"Готово: обработано {processed} записей"))
