import io
import json
import os
import re
from typing import List, Optional, Tuple

import pandas as pd
from dateutil import parser

CSV_EXTS = {".csv"}
XLS_EXTS = {".xlsx", ".xls"}
JSON_EXTS = {".json"}

HEADER_ROWS_PREVIEW = 5


def get_ext(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]


def safe_read_textlike_file_to_df(path: str, filename: str) -> pd.DataFrame:
    """
    Универсальное чтение CSV/XLSX/JSON в DataFrame.
    - CSV: пробуем utf-8, затем cp1251; autodetect sep (',' ';' '\t')
    - XLS/XLSX: через pandas.read_excel
    - JSON: ожидается список объектов (list[dict]) или NDJSON (по строкам)
    """
    ext = get_ext(filename)
    if ext in CSV_EXTS:
        seps = [",", ";", "\t", "|"]
        encodings = ["utf-8", "cp1251"]  # разные кодировки и разделители
        last_err = None
        for enc in encodings:
            for sep in seps:
                try:
                    return pd.read_csv(
                        path, encoding=enc, sep=sep, engine="python", quotechar='"'
                    )
                except Exception as e:
                    last_err = e
        raise last_err or ValueError("Не удалось прочитать CSV")

    if ext in XLS_EXTS:
        return pd.read_excel(path)

    if ext in JSON_EXTS:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except json.JSONDecodeError:
            records = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    records.append(json.loads(line))
            return pd.DataFrame(records)

    raise ValueError("Неподдерживаемый формат файла")


def suggest_text_columns(columns: List[str]) -> List[str]:
    """Небольшая эвристика: ищем колонки, похожие на текст отзыва."""
    patt = re.compile(r"(text|review|comment|отзыв|коммент)", re.IGNORECASE)
    return [c for c in columns if patt.search(c)] or columns


def dataframe_head_columns(df: pd.DataFrame) -> List[str]:
    """
    Приводит имена колонок DataFrame к нормальному виду:
    превращает в строки и обрезает пробелы по краям.
    """
    cols = list(df.columns)
    return [str(c).strip() for c in cols]


def to_int_or_none(x) -> Optional[int]:
    """
    Пытается привести значение к целому числу.
    Если не получилось или число отрицательное — возвращает None.
    """
    try:
        v = int(str(x).strip())
        return v if v >= 0 else None
    except Exception:
        return None


def to_str_or_empty(x) -> str:
    """
    Превращает значение в строку без пробелов по краям.
    Если значение пустое/None — возвращает пустую строку.
    """
    if x is None:
        return ""
    s = str(x).strip()
    return s


def parse_date_or_none(x):
    """
    Пытается распарсить дату из строки в разных форматах.
    Если дата не распознаётся — возвращает None.
    """
    if x in (None, "", "nan", "NaT"):
        return None
    try:
        # parser сам справляется с "2025-10-27", "27.10.2025", "10/27/2025 14:33" и т.п.
        return parser.parse(str(x)).date()
    except Exception:
        return None
