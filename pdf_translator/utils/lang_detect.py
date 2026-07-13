"""
Определение языка текста
"""

from langdetect import detect, DetectorFactory
from typing import Optional

DetectorFactory.seed = 42


# Нормализация кодов языков для переводчиков (Google Translate API)
LANG_CODE_MAP = {
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "zh": "zh-CN",
}


def normalize_lang_code(code: str) -> str:
    """Приводит код языка к формату, принимаемому переводчиками."""
    return LANG_CODE_MAP.get(code, code)


def detect_language(text: str) -> str:
    """
    Определяет язык текста.
    Возвращает нормализованный код языка: 'en', 'zh-CN', 'zh-TW', 'ja', 'ko' и т.д.
    """
    if not text or len(text.strip()) < 3:
        return "en"

    try:
        lang = detect(text)
        return normalize_lang_code(lang)
    except Exception:
        return "en"


def is_cjk_char(ch: str) -> bool:
    """Проверяет, является ли символ китайским, японским или корейским (CJK)"""
    code = ord(ch)
    return (
        (0x4E00 <= code <= 0x9FFF)        # CJK Unified Ideographs
        or (0x3400 <= code <= 0x4DBF)     # CJK Unified Ideographs Extension A
        or (0x20000 <= code <= 0x2A6DF)   # CJK Unified Ideographs Extension B
        or (0xF900 <= code <= 0xFAFF)     # CJK Compatibility Ideographs
        or (0x3040 <= code <= 0x309F)     # Hiragana
        or (0x30A0 <= code <= 0x30FF)     # Katakana
        or (0xAC00 <= code <= 0xD7AF)     # Hangul Syllables
    )


def has_cjk(text: str) -> bool:
    """Проверяет, содержит ли текст CJK символы"""
    return any(is_cjk_char(ch) for ch in text)


def get_text_direction(text: str) -> str:
    """Определяет направление текста: 'horizontal' или 'vertical'"""
    if has_cjk(text):
        # Для CJK текста может быть вертикальным
        return "horizontal"  # По умолчанию, вертикальность определяется из PDF
    return "horizontal"


def estimate_text_length_ratio(source_lang: str, target_lang: str = "ru") -> float:
    """
    Оценивает коэффициент увеличения длины при переводе.
    Например, EN→RU: ~1.2, ZH→RU: ~2.0
    """
    ratios = {
        "en": {"ru": 1.25},
        "zh-cn": {"ru": 2.0},
        "zh-tw": {"ru": 2.0},
        "ja": {"ru": 1.8},
        "ko": {"ru": 1.5},
        "de": {"ru": 1.3},
        "fr": {"ru": 1.2},
        "es": {"ru": 1.15},
    }
    return ratios.get(source_lang, {}).get(target_lang, 1.3)