"""
Менеджер шрифтов: подбор кириллических аналогов, регистрация шрифтов.
Использует системные шрифты Windows с поддержкой кириллицы.
"""

import os
import fitz
from typing import Optional

from config import CYRILLIC_FONTS


# Системные пути к шрифтам Windows
WINDOWS_FONTS_DIR = os.environ.get("WINDIR", "C:\\Windows") + "\\Fonts"

FONT_PATHS = {
    "helv": os.path.join(WINDOWS_FONTS_DIR, "arial.ttf"),
    "helv-bold": os.path.join(WINDOWS_FONTS_DIR, "arialbd.ttf"),
    "helv-italic": os.path.join(WINDOWS_FONTS_DIR, "ariali.ttf"),
    "helv-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "arialbi.ttf"),
    "tiro": os.path.join(WINDOWS_FONTS_DIR, "times.ttf"),
    "tiro-bold": os.path.join(WINDOWS_FONTS_DIR, "timesbd.ttf"),
    "tiro-italic": os.path.join(WINDOWS_FONTS_DIR, "timesi.ttf"),
    "tiro-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "timesbi.ttf"),
    "cour": os.path.join(WINDOWS_FONTS_DIR, "cour.ttf"),
    "cour-bold": os.path.join(WINDOWS_FONTS_DIR, "courbd.ttf"),
    "cour-italic": os.path.join(WINDOWS_FONTS_DIR, "couri.ttf"),
    "cour-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "courbi.ttf"),
}

# Fallback: используем arial для всего если specialised нет
FONT_FALLBACKS = {
    "helv-bold": os.path.join(WINDOWS_FONTS_DIR, "arial.ttf"),
    "helv-italic": os.path.join(WINDOWS_FONTS_DIR, "arial.ttf"),
    "helv-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "arial.ttf"),
    "tiro-bold": os.path.join(WINDOWS_FONTS_DIR, "times.ttf"),
    "tiro-italic": os.path.join(WINDOWS_FONTS_DIR, "times.ttf"),
    "tiro-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "times.ttf"),
    "cour-bold": os.path.join(WINDOWS_FONTS_DIR, "cour.ttf"),
    "cour-italic": os.path.join(WINDOWS_FONTS_DIR, "cour.ttf"),
    "cour-bolditalic": os.path.join(WINDOWS_FONTS_DIR, "cour.ttf"),
}


class FontManager:
    """
    Управляет шрифтами для PDF.
    Регистрирует системные шрифты Windows с поддержкой кириллицы.
    """

    STYLE_MAP = {
        (True, False): "-Bold",
        (False, True): "-Italic",
        (True, True): "-BoldItalic",
        (False, False): "",
    }

    def __init__(self):
        self.registered_fonts = {}
        self._register_system_fonts()

    def _register_system_fonts(self):
        """Регистрирует системные шрифты Windows."""
        for name, path in FONT_PATHS.items():
            if os.path.exists(path):
                try:
                    font_name_lower = name.lower()
                    fitz.Font(fontname=name, fontfile=path)
                    self.registered_fonts[font_name_lower] = {
                        "base": name,
                        "path": path,
                    }
                except Exception:
                    pass
            else:
                # Пробуем fallback
                fallback = FONT_FALLBACKS.get(name, "")
                if fallback and os.path.exists(fallback):
                    try:
                        font_name_lower = name.lower()
                        fitz.Font(fontname=name, fontfile=fallback)
                        self.registered_fonts[font_name_lower] = {
                            "base": name,
                            "path": fallback,
                        }
                    except Exception:
                        pass

        # Если Arial не зарегистрирован — пробуем прямой путь
        if "helv" not in self.registered_fonts:
            for alt_name in ["arial", "Arial"]:
                alt_path = os.path.join(WINDOWS_FONTS_DIR, f"{alt_name}.ttf")
                if os.path.exists(alt_path):
                    try:
                        fitz.Font(fontname="helv", fontfile=alt_path)
                        self.registered_fonts["helv"] = {
                            "base": "helv",
                            "path": alt_path,
                        }
                        break
                    except Exception:
                        pass

    def _clean_font_name(self, font_name: str) -> str:
        """Очищает имя шрифта от префиксов и постфиксов."""
        if "+" in font_name:
            font_name = font_name.split("+")[-1]
        for suffix in ["-Bold", "-Italic", "-Oblique", "-BoldItalic", ",Bold", ",Italic"]:
            font_name = font_name.replace(suffix, "")
        return font_name.strip()

    def get_cyrillic_font(
        self, original_font: str, bold: bool = False, italic: bool = False
    ) -> str:
        """
        Возвращает имя зарегистрированного шрифта с поддержкой кириллицы.

        Args:
            original_font: имя оригинального шрифта
            bold: жирный
            italic: курсив

        Returns:
            имя шрифта для PyMuPDF insert_text
        """
        clean = self._clean_font_name(original_font).lower()

        # Определяем базовое семейство
        is_serif = any(t in clean for t in ["times", "roman", "tiro", "serif"])
        is_mono = any(t in clean for t in ["cour", "courier", "mono", "monospace"])
        
        if is_mono:
            base = "cour"
        elif is_serif:
            base = "tiro"
        else:
            base = "helv"

        # Собираем полное имя с учётом стиля
        style = self.STYLE_MAP.get((bold, italic), "")
        full_name = f"{base}{style}"

        if full_name.lower() in self.registered_fonts:
            return full_name

        # Fallback: без стиля
        if base.lower() in self.registered_fonts:
            return base

        # Last resort: helv
        return "helv"

    def is_font_available(self, font_name: str) -> bool:
        """Проверяет, зарегистрирован ли шрифт."""
        return font_name.lower() in self.registered_fonts


# Синглтон
font_manager = FontManager()