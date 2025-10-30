from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "region", "product_category", "gender", "age", "sentiment", "created_at")
    list_filter = ("sentiment", "region", "product_category", "gender", "date")
    search_fields = ("review_text", "processed_text", "region", "product_category")
    date_hierarchy = "date"
    ordering = ("-created_at",)
