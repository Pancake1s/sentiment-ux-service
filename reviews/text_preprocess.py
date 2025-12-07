import inspect
from collections import namedtuple
from inspect import getfullargspec

# ПАТЧ ДЛЯ PYTHON 3.11+ (где getargspec убрали)
if not hasattr(inspect, "getargspec"):
    ArgSpec = namedtuple("ArgSpec", "args varargs keywords defaults")

    def getargspec(func):
        """
        приводим к старому формату (args, varargs, keywords, defaults),
        именно такой кортеж ждёт pymorphy2
        """
        fs = getfullargspec(func)
        return ArgSpec(
            fs.args,
            fs.varargs,
            fs.varkw, 
            fs.defaults,
        )

    inspect.getargspec = getargspec
# КОНЕЦ ПАТЧА

import re
from typing import Iterable, List

from nltk.corpus import stopwords
from pymorphy2 import MorphAnalyzer

_RU_STOP = set(stopwords.words("russian"))
_MORPH = MorphAnalyzer()

_COMMON_TRASH = {
    "ооо", "зао", "ип", "ooo", "ooo.", "магазин", "сайт", "компания",
    "интернет", "онлайн", "оплачивать", "курьер", "доставка"
}

_URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
# оставляем буквы/цифры/пробел, заменяя остальное на пробел
_NON_ALNUM_RE = re.compile(r"[^0-9a-zа-яё\s]+", flags=re.IGNORECASE)
_MULTI_SPACE_RE = re.compile(r"\s+")

def basic_cleanup(text: str) -> str:
    """
    Базовая очистка: нижний регистр, вырезаем URL/HTML/мусорные символы, схлопываем пробелы.
    """
    s = str(text).strip().lower()
    s = _URL_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    s = _NON_ALNUM_RE.sub(" ", s)
    s = _MULTI_SPACE_RE.sub(" ", s).strip()
    return s

def tokenize(s: str) -> List[str]:
    """
    Токенизация по пробелам после очистки.
    """
    if not s:
        return []
    return s.split()

def filter_stopwords(tokens: Iterable[str]) -> List[str]:
    """
    Удаляем стоп-слова и слишком короткие токены.
    """
    out = []
    for t in tokens:
        if len(t) <= 2:
            continue
        if t in _RU_STOP:
            continue
        if t in _COMMON_TRASH:
            continue
        out.append(t)
    return out

def lemmatize_ru(tokens: Iterable[str]) -> List[str]:
    """
    Лемматизация русских слов через pymorphy2.
    """
    out = []
    for t in tokens:
        if re.match(r"[a-z]+", t):
            out.append(t)
            continue
        out.append(_MORPH.parse(t)[0].normal_form)
    return out

def preprocess_pipeline(text: str, do_lemmatize: bool = True) -> str:
    """
    Полный пайплайн: clean -> tokenize -> stopwords -> (lemmatize) -> join.
    Возвращает строку, готовую для TF-IDF/модели.
    """
    s = basic_cleanup(text)
    toks = tokenize(s)
    toks = filter_stopwords(toks)
    if do_lemmatize:
        toks = lemmatize_ru(toks)
    return " ".join(toks)
