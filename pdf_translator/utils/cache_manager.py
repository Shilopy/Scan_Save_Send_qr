"""
Менеджер кэширования переводов.
Сохраняет переводы в JSON-файл для ускорения повторных запросов.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional
from config import CACHE_DIR, CACHE_CONFIG


class TranslationCache:
    """
    Кэш переводов с TTL и ограничением размера.
    Ключ = хеш (исходный текст + исходный язык + целевой язык + сервис).
    """

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or (CACHE_DIR / "translations.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache: dict = {}
        self.enabled = CACHE_CONFIG["enabled"]
        self.ttl_seconds = CACHE_CONFIG["ttl_days"] * 86400
        self._load()

    def _make_key(self, text: str, source_lang: str, target_lang: str, service: str) -> str:
        """Генерирует уникальный ключ для кэша."""
        raw = f"{text}|{source_lang}|{target_lang}|{service}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _load(self):
        """Загружает кэш из файла."""
        if not self.enabled:
            self.cache = {}
            return

        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.cache = {}
        else:
            self.cache = {}

        # Удаляем устаревшие записи
        self._cleanup()

    def _save(self):
        """Сохраняет кэш в файл."""
        if not self.enabled:
            return

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def _cleanup(self):
        """Удаляет записи с истекшим TTL."""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry.get("timestamp", 0) > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

        # Проверяем общий размер
        self._check_size_limit()

    def _check_size_limit(self):
        """Проверяет, не превышен ли лимит размера кэша."""
        max_size = CACHE_CONFIG["max_size_mb"] * 1024 * 1024
        json_size = len(json.dumps(self.cache, ensure_ascii=False))

        if json_size > max_size:
            # Удаляем самые старые записи пока размер не станет приемлемым
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k].get("timestamp", 0),
            )
            while json_size > max_size * 0.8 and sorted_keys:
                del self.cache[sorted_keys[0]]
                sorted_keys.pop(0)
                json_size = len(json.dumps(self.cache, ensure_ascii=False))

    def get(
        self, text: str, source_lang: str, target_lang: str, service: str
    ) -> Optional[str]:
        """Получает перевод из кэша."""
        if not self.enabled:
            return None

        key = self._make_key(text, source_lang, target_lang, service)

        if key in self.cache:
            entry = self.cache[key]
            now = time.time()
            if now - entry.get("timestamp", 0) <= self.ttl_seconds:
                return entry.get("translated_text")
            else:
                del self.cache[key]

        return None

    def set(
        self, text: str, source_lang: str, target_lang: str, service: str, translated_text: str
    ):
        """Сохраняет перевод в кэш."""
        if not self.enabled:
            return

        key = self._make_key(text, source_lang, target_lang, service)
        self.cache[key] = {
            "original_text": text,
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "service": service,
            "timestamp": time.time(),
        }

        # Сохраняем периодически (каждые 10 записей)
        if len(self.cache) % 10 == 0:
            self._cleanup()
            self._save()

    def get_batch(
        self, texts: list[str], source_lang: str, target_lang: str, service: str
    ) -> tuple[dict[str, str], list[str]]:
        """
        Возвращает (словарь найденных переводов, список текстов без переводов).
        """
        found = {}
        not_found = []

        for text in texts:
            result = self.get(text, source_lang, target_lang, service)
            if result is not None:
                found[text] = result
            else:
                not_found.append(text)

        return found, not_found

    def flush(self):
        """Принудительно сохраняет кэш."""
        self._cleanup()
        self._save()

    def clear(self):
        """Очищает весь кэш."""
        self.cache = {}
        self._save()

    def stats(self) -> dict:
        """Возвращает статистику кэша."""
        total_entries = len(self.cache)
        total_size = len(json.dumps(self.cache, ensure_ascii=False))

        return {
            "entries": total_entries,
            "size_kb": round(total_size / 1024, 2),
            "size_mb": round(total_size / 1024 / 1024, 2),
            "file": str(self.cache_file),
        }