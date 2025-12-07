from django import forms

ALLOWED_EXTENSIONS = (".csv", ".xlsx", ".xls", ".json")


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Файл с отзывами (CSV / XLSX / JSON)",
        help_text="Макс. 20 МБ; поддерживаются CSV, XLSX, JSON",
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        name = f.name.lower()
        # простая проверка расширения
        if not name.endswith(ALLOWED_EXTENSIONS):
            raise forms.ValidationError(
                "Неподдерживаемый тип файла. Разрешены: CSV, XLSX, JSON."
            )
        # ограничение на размер файла (пример: 20 МБ)
        limit = 20 * 1024 * 1024
        if f.size > limit:
            raise forms.ValidationError("Размер файла превышает 20 МБ.")
        return f


def make_column_mapping_form(choices):
    """
    Фабрика формы маппинга с динамическими choices.
    'choices' — список кортежей [('col1','col1'), ('col2','col2'), ...]
    """
    NONE_CHOICE = [("", "— нет —")]
    col_choices = NONE_CHOICE + choices

    class ColumnMappingForm(forms.Form):
        review_text = forms.ChoiceField(
            label="Столбец с текстом отзыва", choices=choices
        )  # ОБЯЗАТЕЛЬНО
        date = forms.ChoiceField(label="Дата", required=False, choices=col_choices)
        region = forms.ChoiceField(label="Регион", required=False, choices=col_choices)
        product_category = forms.ChoiceField(
            label="Категория товара", required=False, choices=col_choices
        )
        gender = forms.ChoiceField(label="Пол", required=False, choices=col_choices)
        age = forms.ChoiceField(label="Возраст", required=False, choices=col_choices)
        source = forms.ChoiceField(
            label="Источник", required=False, choices=col_choices
        )

    return ColumnMappingForm
