"""
Конфигурация PDF Translator
"""

import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"

# Создаем директории
CACHE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Настройки переводчиков
TRANSLATOR_CONFIG = {
    "google": {
        "name": "Google Translate",
        "description": "Бесплатный, лучшее качество",
        "api_key_required": False,
    },
    "mymemory": {
        "name": "MyMemory",
        "description": "Бесплатный, без ограничений, без карты",
        "api_key_required": False,
    },
    "deepl": {
        "name": "DeepL",
        "description": "Отличное качество, требуется API ключ + иностр. карта",
        "api_key_required": True,
        "api_url": "https://api-free.deepl.com/v2/translate",
    },
    "yandex": {
        "name": "Yandex Translate",
        "description": "Хорошее качество для русского, API ключ (бесплатно в Яндекс Cloud)",
        "api_key_required": True,
        "api_url": "https://translate.api.cloud.yandex.net/translate/v2/translate",
    },
}

# Языки
SUPPORTED_LANGUAGES = {
    "auto": "Автоопределение",
    "en": "Английский",
    "zh": "Китайский",
    "ja": "Японский",
    "ko": "Корейский",
    "de": "Немецкий",
    "fr": "Французский",
    "es": "Испанский",
    "it": "Итальянский",
}

# Настройки OCR
OCR_CONFIG = {
    "tesseract": {
        "name": "Tesseract",
        "languages": "eng+chi_sim+chi_tra+jpn+rus",
    },
    "paddleocr": {
        "name": "PaddleOCR",
        "description": "Лучше для китайского",
    },
}

# Настройки кэширования
CACHE_CONFIG = {
    "enabled": True,
    "max_size_mb": 500,
    "ttl_days": 30,
}

# Настройки вывода
OUTPUT_CONFIG = {
    "default_dpi": 150,
    "min_font_size": 6,
    "max_font_size": 72,
    "font_shrink_step": 0.05,
    "line_spacing": 1.2,
}

# Поддерживаемые шрифты с кириллицей
CYRILLIC_FONTS = {
    "Arial": "Arial",
    "TimesNewRoman": "Times-Roman",
    "Calibri": "Arial",
    "Helvetica": "Helvetica",
    "SimSun": "Arial",
    "MSung": "Arial",
    "MingLiU": "Arial",
    "PMingLiU": "Arial",
    "Heiti": "Arial",
    "MicrosoftYaHei": "Arial",
    "KaiTi": "Arial",
    "FangSong": "Arial",
    "MSMincho": "Arial",
    "Gothic": "Arial",
}

# Настройки параллельной обработки
PARALLEL_CONFIG = {
    "max_workers": min(os.cpu_count() or 4, 8),
    "batch_size": 10,
}