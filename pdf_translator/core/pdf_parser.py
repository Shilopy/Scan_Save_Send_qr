"""
Парсер PDF: извлекает текст, шрифты, цвета, координаты, таблицы и изображения.
"""

import fitz
import pdfplumber
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

from config import CYRILLIC_FONTS, OUTPUT_CONFIG
from utils.lang_detect import has_cjk


@dataclass
class TextSpan:
    """Элементарный текстовый фрагмент из PDF."""

    text: str
    font: str
    size: float
    color: Tuple[float, float, float]  # RGB
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int
    is_bold: bool
    is_italic: bool
    translatable: bool = True


@dataclass
class TextBlock:
    """Логический блок текста (заголовок, параграф, ячейка таблицы и т.д.)."""

    spans: List[TextSpan]
    block_type: str  # "heading", "paragraph", "table_cell", "list_item", "footer", "header"
    bbox: Tuple[float, float, float, float]
    page_num: int
    text: str = ""
    table_info: Optional[dict] = None

    def __post_init__(self):
        self.text = " ".join(s.text for s in self.spans).strip()


@dataclass
class PDFContent:
    """Структура, содержащая всё извлеченное из PDF."""

    path: Path
    total_pages: int
    text_blocks: List[TextBlock] = field(default_factory=list)
    tables: List[dict] = field(default_factory=list)
    images: List[dict] = field(default_factory=list)
    has_scanned_pages: bool = False


class PDFParser:
    """Извлекает весь контент из PDF с метаданными."""

    def __init__(self, pdf_path: str):
        self.path = Path(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)

    def parse(self) -> PDFContent:
        """Полный парсинг PDF: текст, таблицы, изображения."""
        content = PDFContent(
            path=self.path,
            total_pages=self.total_pages,
        )

        for page_num in range(self.total_pages):
            page = self.doc[page_num]
            page_dict = page.get_text("dict")

            for block in page_dict["blocks"]:
                if block["type"] == 0:
                    text_block = self._parse_text_block(block, page_num)
                    if text_block:
                        content.text_blocks.append(text_block)
                elif block["type"] == 1:
                    content.images.append(self._parse_image_block(block, page_num))

            # Парсинг таблиц через pdfplumber
            tables = self._extract_tables(page_num)
            content.tables.extend(tables)

        content.has_scanned_pages = self._detect_scanned_pages()
        return content

    def _parse_text_block(self, block: dict, page_num: int) -> Optional[TextBlock]:
        """Парсит один текстовый блок."""
        spans = []

        for line in block["lines"]:
            for span in line["spans"]:
                raw_text = span["text"]
                stripped = raw_text.strip()

                if not stripped:
                    continue

                text_span = TextSpan(
                    text=raw_text,
                    font=span["font"],
                    size=span["size"],
                    color=self._int_to_rgb(span["color"]),
                    bbox=tuple(span["bbox"]),
                    page_num=page_num,
                    is_bold=("Bold" in span["font"]),
                    is_italic=("Italic" in span["font"] or "Oblique" in span["font"]),
                    translatable=self._is_translatable_text(stripped),
                )
                spans.append(text_span)

        if not spans:
            return None

        block_type = self._detect_block_type(spans, block, page_num)

        return TextBlock(
            spans=spans,
            block_type=block_type,
            bbox=tuple(block["bbox"]),
            page_num=page_num,
        )

    def _parse_image_block(self, block: dict, page_num: int) -> dict:
        """Парсит блок изображения."""
        return {
            "bbox": tuple(block["bbox"]),
            "page_num": page_num,
            "size": block.get("size", 0),
            "width": block.get("width", 0),
            "height": block.get("height", 0),
        }

    def _extract_tables(self, page_num: int) -> List[dict]:
        """Извлекает таблицы со страницы через pdfplumber."""
        tables = []
        try:
            with pdfplumber.open(str(self.path)) as pdf:
                if page_num >= len(pdf.pages):
                    return tables

                page = pdf.pages[page_num]
                found_tables = page.extract_tables()
                found_table_settings = page.find_tables()

                for i, (table_data, table_obj) in enumerate(
                    zip(found_tables, found_table_settings)
                ):
                    if not table_data or not any(any(cell for cell in row) for row in table_data):
                        continue

                    tables.append(
                        {
                            "page_num": page_num,
                            "table_index": i,
                            "bbox": tuple(table_obj.bbox),
                            "rows": len(table_data),
                            "cols": len(table_data[0]) if table_data else 0,
                            "data": table_data,
                            "cells": self._extract_table_cells(table_data, table_obj, page_num),
                        }
                    )
        except Exception:
            pass

        return tables

    def _extract_table_cells(
        self, table_data: list, table_obj, page_num: int
    ) -> List[dict]:
        """Извлекает отдельные ячейки таблицы с координатами."""
        cells = []
        for row_idx, row in enumerate(table_data):
            for col_idx, cell_text in enumerate(row):
                if cell_text and cell_text.strip():
                    # Оцениваем bbox ячейки пропорционально
                    x0 = table_obj.bbox[0] + (table_obj.bbox[2] - table_obj.bbox[0]) * col_idx / max(len(row), 1)
                    x1 = table_obj.bbox[0] + (table_obj.bbox[2] - table_obj.bbox[0]) * (col_idx + 1) / max(len(row), 1)
                    y0 = table_obj.bbox[1] + (table_obj.bbox[3] - table_obj.bbox[1]) * row_idx / max(len(table_data), 1)
                    y1 = table_obj.bbox[1] + (table_obj.bbox[3] - table_obj.bbox[1]) * (row_idx + 1) / max(len(table_data), 1)

                    cells.append(
                        {
                            "row": row_idx,
                            "col": col_idx,
                            "text": cell_text.strip(),
                            "bbox": (x0, y0, x1, y1),
                            "page_num": page_num,
                        }
                    )
        return cells

    def _int_to_rgb(self, color_int: int) -> Tuple[float, float, float]:
        """Конвертирует int цвет (0xRRGGBB) в RGB tuple (0-1)."""
        r = ((color_int >> 16) & 255) / 255.0
        g = ((color_int >> 8) & 255) / 255.0
        b = (color_int & 255) / 255.0
        return (r, g, b)

    def _detect_block_type(self, spans: List[TextSpan], block: dict, page_num: int) -> str:
        """Определяет тип текстового блока."""
        if not spans:
            return "paragraph"

        avg_size = sum(s.size for s in spans) / len(spans)
        all_bold = all(s.is_bold for s in spans)
        text = " ".join(s.text for s in spans).strip()
        y_pos = block["bbox"][1]
        page_height = self.doc[page_num].rect.height

        # Колонтитулы: верхние 5% и нижние 5% страницы
        if y_pos < page_height * 0.05:
            return "header"
        if y_pos > page_height * 0.95:
            return "footer"

        # Заголовки: большой жирный шрифт, короткий текст
        if avg_size > 14 and all_bold and len(text) < 150:
            return "heading"

        # Элементы списка: начинаются с маркера
        if text.strip().startswith(("•", "-", "–", "—", "·", "○", "▪", "▸", "1.", "2.", "a.", "b.")):
            return "list_item"

        return "paragraph"

    def _is_translatable_text(self, text: str) -> bool:
        """Проверяет, нужно ли переводить этот текст."""
        if not text or len(text) < 2:
            return False

        import re

        # Только цифры и знаки
        if re.match(r'^[\d\s.,;:!?\-–—()\[\]{}<>+*/%=#@&|\\^~`\'"]+$', text):
            return False

        # Email
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', text):
            return False

        # URL
        if text.startswith("http://") or text.startswith("https://"):
            return False

        return True

    def _detect_scanned_pages(self) -> bool:
        """Определяет, есть ли сканированные страницы (без текстового слоя)."""
        total_text = 0
        for page in self.doc:
            total_text += len(page.get_text().strip())

        # Если текста меньше 50 символов на страницу — вероятно скан
        avg_text = total_text / max(self.total_pages, 1)
        return avg_text < 50

    def get_page_images(self, page_num: int, dpi: int = 150) -> List[dict]:
        """Рендерит страницу в изображение для OCR."""
        page = self.doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        return [{"page_num": page_num, "pixmap": pix, "dpi": dpi, "width": pix.width, "height": pix.height}]

    def close(self):
        """Закрывает документ."""
        self.doc.close()