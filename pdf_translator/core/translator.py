"""
Модуль перевода: Google Translate (REST API), MyMemory (бесплатный без ключа),
Yandex Translate, DeepL.
С пакетным переводом и кэшированием.
"""

import re
import json
import time
import urllib.parse
import requests
from abc import ABC, abstractmethod
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import TRANSLATOR_CONFIG, PARALLEL_CONFIG
from utils.cache_manager import TranslationCache


class BaseTranslator(ABC):
    """Базовый класс переводчика."""

    def __init__(self, source_lang: str = "auto", target_lang: str = "ru"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cache = TranslationCache()

    @abstractmethod
    def _translate_single(self, text: str) -> str:
        """Перевод одного текста."""
        ...

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Имя сервиса для кэша."""
        ...

    def translate(self, text: str) -> str:
        """Переводит текст, используя кэш."""
        if not text or not text.strip():
            return text

        cached = self.cache.get(text, self.source_lang, self.target_lang, self.service_name)
        if cached:
            return cached

        result = self._translate_single(text)
        self.cache.set(text, self.source_lang, self.target_lang, self.service_name, result)
        return result

    def translate_batch(self, texts: List[str]) -> List[str]:
        """Пакетный перевод с параллельной обработкой."""
        if not texts:
            return []

        non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        result = [""] * len(texts)

        cached, to_translate = self.cache.get_batch(
            [t for _, t in non_empty],
            self.source_lang,
            self.target_lang,
            self.service_name,
        )

        need_translate_indices = []
        need_translate_texts = []
        for idx, text in non_empty:
            if text in cached:
                result[idx] = cached[text]
            else:
                need_translate_indices.append(idx)
                need_translate_texts.append(text)

        if not need_translate_texts:
            return result

        translated = self._translate_batch_parallel(need_translate_texts)

        for idx, translated_text in zip(need_translate_indices, translated):
            result[idx] = translated_text
            original = texts[idx]
            self.cache.set(
                original, self.source_lang, self.target_lang,
                self.service_name, translated_text,
            )

        self.cache.flush()
        return result

    def _translate_batch_parallel(self, texts: List[str]) -> List[str]:
        """Параллельный перевод пачек текста."""
        max_workers = PARALLEL_CONFIG["max_workers"]
        batch_size = PARALLEL_CONFIG["batch_size"]

        batches = [
            texts[i:i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]

        results = [""] * len(texts)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for batch_idx, batch in enumerate(batches):
                future = executor.submit(self._translate_single_batch, batch)
                futures[future] = batch_idx

            for future in as_completed(futures):
                batch_idx = futures[future]
                try:
                    batch_results = future.result()
                    start_idx = batch_idx * batch_size
                    for i, res in enumerate(batch_results):
                        results[start_idx + i] = res
                except Exception:
                    start_idx = batch_idx * batch_size
                    batch = batches[batch_idx]
                    for i, text in enumerate(batch):
                        try:
                            results[start_idx + i] = self._translate_single(text)
                        except Exception:
                            results[start_idx + i] = text

        return results

    def _translate_single_batch(self, texts: List[str]) -> List[str]:
        return [self._translate_single(t) for t in texts]


# ---------------------------------------------------------------------------
# Google Translate — через прямой REST API (googleapis.com/translate_a/single)
# ---------------------------------------------------------------------------

class GoogleTranslateRESTService(BaseTranslator):
    """
    Перевод через Google Translate REST API (бесплатно, без API ключа).
    Использует translate.googleapis.com/translate_a/t?client=gtx.
    """

    _API_URL = "https://translate.googleapis.com/translate_a/t"

    _LANG_FIX = {
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "zh": "zh-CN",
        "auto": "auto",
    }

    def _fix_lang(self, code: str) -> str:
        return self._LANG_FIX.get(code, code)

    @property
    def service_name(self) -> str:
        return "google"

    def _translate_single(self, text: str) -> str:
        source = self._fix_lang(self.source_lang)
        target = self._fix_lang(self.target_lang)

        for attempt in range(3):
            try:
                params = {
                    "client": "gtx",
                    "sl": source,
                    "tl": target,
                    "dt": "t",
                    "q": text,
                }
                response = requests.get(
                    self._API_URL,
                    params=params,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                    },
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    # Структура ответа: [[["translated text", "original", ...]], ...]
                    if data and isinstance(data, list) and len(data) > 0:
                        first = data[0]
                        if isinstance(first, list):
                            parts = []
                            for item in first:
                                if isinstance(item, list) and len(item) > 0:
                                    parts.append(str(item[0]))
                            result = "".join(parts)
                            if result.strip():
                                return result
            except Exception:
                pass
            time.sleep(1.5 * (attempt + 1))
        return text

    def _translate_single_batch(self, texts: List[str]) -> List[str]:
        if not texts:
            return []
        # Для длинных текстов переводим по одному
        if any(len(t) > 300 for t in texts):
            return [self._translate_single(t) for t in texts]

        combined = " ||| ".join(texts)
        translated_combined = self._translate_single(combined)
        results = translated_combined.split(" ||| ")
        while len(results) < len(texts):
            results.append(texts[len(results)])
        return results[:len(texts)]


# ---------------------------------------------------------------------------
# MyMemory — бесплатный без API ключа, без иностранной карты
# ---------------------------------------------------------------------------

class MyMemoryTranslatorService(BaseTranslator):
    """
    Перевод через MyMemory API (бесплатно, без API ключа).
    https://mymemory.translated.net/doc/spec.php
    """

    _API_URL = "https://api.mymemory.translated.net/get"

    _LANG_FIX = {
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "zh": "zh-CN",
        "auto": "en",
    }

    def _fix_lang(self, code: str) -> str:
        return self._LANG_FIX.get(code, code)

    @property
    def service_name(self) -> str:
        return "mymemory"

    def _translate_single(self, text: str) -> str:
        source = self._fix_lang(self.source_lang)
        target = self._fix_lang(self.target_lang)

        for attempt in range(3):
            try:
                params = {
                    "q": text,
                    "langpair": f"{source}|{target}",
                    "de": "your@email.com",  # Можно указать email для повышения лимита
                }
                response = requests.get(
                    self._API_URL,
                    params=params,
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    translated = data.get("responseData", {}).get("translatedText", "")
                    if translated and translated.strip():
                        return translated
            except Exception:
                pass
            time.sleep(1.0 * (attempt + 1))
        return text

    def _translate_single_batch(self, texts: List[str]) -> List[str]:
        return [self._translate_single(t) for t in texts]


# ---------------------------------------------------------------------------
# DeepL API — требуется API ключ
# ---------------------------------------------------------------------------

class DeepLTranslatorService(BaseTranslator):
    """Перевод через DeepL API (требуется API ключ)."""

    def __init__(self, api_key: str, source_lang: str = "auto", target_lang: str = "ru"):
        super().__init__(source_lang, target_lang)
        self.api_key = api_key
        self.api_url = TRANSLATOR_CONFIG["deepl"]["api_url"]

    @property
    def service_name(self) -> str:
        return "deepl"

    def _translate_single(self, text: str) -> str:
        try:
            response = requests.post(
                self.api_url,
                data={
                    "auth_key": self.api_key,
                    "text": text,
                    "source_lang": self.source_lang.upper() if self.source_lang != "auto" else None,
                    "target_lang": self.target_lang.upper(),
                },
                timeout=15,
            )
            result = response.json()
            if "translations" in result:
                return result["translations"][0]["text"]
            return text
        except Exception:
            time.sleep(1)
            try:
                response = requests.post(
                    self.api_url,
                    data={
                        "auth_key": self.api_key,
                        "text": text,
                        "target_lang": self.target_lang.upper(),
                    },
                    timeout=15,
                )
                result = response.json()
                if "translations" in result:
                    return result["translations"][0]["text"]
            except Exception:
                pass
            return text


# ---------------------------------------------------------------------------
# Yandex Translate — API ключ (можно получить в Яндекс Cloud бесплатно)
# ---------------------------------------------------------------------------

class YandexTranslatorService(BaseTranslator):
    """Перевод через Yandex Translate API (требуется API ключ)."""

    def __init__(self, api_key: str, source_lang: str = "auto", target_lang: str = "ru"):
        super().__init__(source_lang, target_lang)
        self.api_key = api_key
        self.api_url = TRANSLATOR_CONFIG["yandex"]["api_url"]

    @property
    def service_name(self) -> str:
        return "yandex"

    def _translate_single(self, text: str) -> str:
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.api_key}",
            }
            body = {
                "sourceLanguageCode": self.source_lang if self.source_lang != "auto" else "en",
                "targetLanguageCode": self.target_lang,
                "texts": [text],
            }
            response = requests.post(
                self.api_url,
                json=body,
                headers=headers,
                timeout=15,
            )
            result = response.json()
            if "translations" in result:
                return result["translations"][0]["text"]
            return text
        except Exception:
            time.sleep(1)
            return text


# ---------------------------------------------------------------------------
# Фабрика
# ---------------------------------------------------------------------------

def create_translator(
    service: str = "google",
    api_key: str = "",
    source_lang: str = "auto",
    target_lang: str = "ru",
) -> BaseTranslator:
    """Фабрика переводчиков."""
    if service == "deepl":
        if not api_key:
            raise ValueError("DeepL requires an API key")
        return DeepLTranslatorService(api_key=api_key, source_lang=source_lang, target_lang=target_lang)
    elif service == "yandex":
        if not api_key:
            raise ValueError("Yandex requires an API key")
        return YandexTranslatorService(api_key=api_key, source_lang=source_lang, target_lang=target_lang)
    elif service == "mymemory":
        return MyMemoryTranslatorService(source_lang=source_lang, target_lang=target_lang)
    else:
        # google — прямой REST API, без deep_translator
        return GoogleTranslateRESTService(source_lang=source_lang, target_lang=target_lang)