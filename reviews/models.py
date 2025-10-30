from django.db import models

class Review(models.Model):
    SENTIMENT_CHOICES = [
        ("negative", "negative"),
        ("neutral", "neutral"),
        ("positive", "positive"),
        ("", "unknown"),
    ]

    review_text = models.TextField()
    processed_text = models.TextField(blank=True)
    sentiment = models.CharField(max_length=16, choices=SENTIMENT_CHOICES, default="", blank=True)

    date = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=128, blank=True)
    product_category = models.CharField(max_length=128, blank=True)
    gender = models.CharField(max_length=16, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["region"]),
            models.Index(fields=["product_category"]),
            models.Index(fields=["sentiment"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        parts = [self.date.isoformat() if self.date else "no_date", self.region or "no_region", self.sentiment or "unknown"]
        return " | ".join(parts)
