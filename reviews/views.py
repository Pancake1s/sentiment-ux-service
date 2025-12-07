import os
import uuid
from typing import Dict, List

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.urls import reverse

from reviews.text_preprocess import preprocess_pipeline

from .forms import UploadFileForm, make_column_mapping_form
from .models import Review
from .utils import (
    dataframe_head_columns,
    parse_date_or_none,
    safe_read_textlike_file_to_df,
    suggest_text_columns,
    to_int_or_none,
    to_str_or_empty,
)


def home(request):
    return render(request, "home.html")


def reviews_list(request):
    qs = Review.objects.all()[:50]
    return render(request, "reviews_list.html", {"reviews": qs})


TMP_DIR = os.path.join(settings.MEDIA_ROOT, "uploads", "tmp")
os.makedirs(TMP_DIR, exist_ok=True)


def _save_temp_file(fobj) -> str:
    """Сохраняем загруженный файл в TMP_DIR с уникальным именем, возвращаем полный путь."""
    ext = os.path.splitext(fobj.name)[1].lower()
    tmp_name = f"{uuid.uuid4().hex}{ext}"
    fs = FileSystemStorage(location=TMP_DIR)
    path = fs.save(tmp_name, fobj)
    return os.path.join(TMP_DIR, path)


def upload_step1(request):
    """
    Шаг 1: загрузка файла, чтение первых строк и показ формы маппинга.
    """
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            tmp_full_path = _save_temp_file(form.cleaned_data["file"])
            original_name = form.cleaned_data["file"].name

            try:
                df = safe_read_textlike_file_to_df(tmp_full_path, original_name)
            except Exception as e:
                messages.error(request, f"Ошибка чтения файла: {e}")
                return render(request, "reviews/upload.html", {"form": form})

            cols = dataframe_head_columns(df)
            request.session["tmp_full_path"] = tmp_full_path
            request.session["original_name"] = original_name
            request.session["preview_cols"] = cols

            choices = [(c, c) for c in cols]
            ColumnMappingForm = make_column_mapping_form(choices)

            initial = {}
            text_candidates = suggest_text_columns(cols)
            if text_candidates:
                initial["review_text"] = text_candidates[0]

            form_map = ColumnMappingForm(initial=initial)
            return render(
                request,
                "reviews/column_mapping.html",
                {
                    "form": form_map,
                    "columns": cols,
                    "original_name": original_name,
                },
            )
    else:
        form = UploadFileForm()
    return render(request, "reviews/upload.html", {"form": form})


def upload_step2_import(request):
    """
    Шаг 2: импорт по маппингу колонок в БД.
    """
    tmp_full_path = request.session.get("tmp_full_path")
    original_name = request.session.get("original_name")
    preview_cols = request.session.get("preview_cols") or []

    if not (tmp_full_path and original_name and os.path.exists(tmp_full_path)):
        messages.error(request, "Не найден временный файл. Повторите загрузку.")
        return redirect("upload_step1")

    choices = [(c, c) for c in preview_cols]
    ColumnMappingForm = make_column_mapping_form(choices)

    if request.method == "POST":
        form = ColumnMappingForm(request.POST)
        if form.is_valid():
            mapping = form.cleaned_data
            try:
                df = safe_read_textlike_file_to_df(tmp_full_path, original_name)
            except Exception as e:
                messages.error(request, f"Ошибка чтения файла: {e}")
                return redirect("upload_step1")

            df.columns = [str(c).strip() for c in df.columns]

            review_col = mapping.get("review_text")
            if not review_col or review_col not in df.columns:
                messages.error(request, "Не выбрана валидная колонка с текстом отзыва.")
                return redirect("upload_step1")

            to_create = []
            skipped = 0

            date_col = mapping.get("date") or None
            region_col = mapping.get("region") or None
            cat_col = mapping.get("product_category") or None
            gender_col = mapping.get("gender") or None
            age_col = mapping.get("age") or None
            src_col = mapping.get("source") or None

            for _, row in df.iterrows():
                text_raw = row.get(review_col, "")
                text = to_str_or_empty(text_raw)
                if not text:
                    skipped += 1
                    continue

                processed = preprocess_pipeline(text)
                date_val = parse_date_or_none(row.get(date_col)) if date_col else None
                region_val = to_str_or_empty(row.get(region_col)) if region_col else ""
                cat_val = to_str_or_empty(row.get(cat_col)) if cat_col else ""
                gender_val = to_str_or_empty(row.get(gender_col)) if gender_col else ""
                age_val = to_int_or_none(row.get(age_col)) if age_col else None
                source_val = to_str_or_empty(row.get(src_col)) if src_col else ""

                to_create.append(
                    Review(
                        review_text=text,
                        processed_text=processed,
                        sentiment="",
                        date=date_val,
                        region=region_val,
                        product_category=cat_val,
                        gender=gender_val,
                        age=age_val,
                        source=source_val,
                    )
                )

            created = 0
            if to_create:
                Review.objects.bulk_create(to_create, batch_size=1000)
                created = len(to_create)

            try:
                os.remove(tmp_full_path)
            except OSError:
                pass

            return render(
                request,
                "reviews/import_result.html",
                {
                    "original_name": original_name,
                    "created": created,
                    "skipped": skipped,
                    "total": int(created) + int(skipped),
                },
            )

    # если не POST — вернуть на шаг 1
    messages.error(request, "Неверный метод запроса. Повторите загрузку.")
    return redirect("upload_step1")
