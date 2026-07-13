"""
Реконструктор PDF: создает переведенный PDF с сохранением форматирования.
Использует insert_htmlbox для корректной вставки кириллицы.
"""

import fitz
from typing import List, Tuple
from dataclasses import dataclass

from config import OUTPUT_CONFIG


@dataclass
class ReplacementBlock:
    """Блок для замены текста."""

    page_num: int
    bbox: Tuple[float, float, float, float]
    original_text: str
    translated_text: str
    original_font: str
    font_size: float
    color: Tuple[float, float, float]
    is_bold: bool
    is_italic: bool
    block_type: str = "paragraph"
    translatable: bool = True


def _rect(bbox):
    """Создает fitz.Rect из bbox tuple."""
    return fitz.Rect(*bbox)


def _color_to_hex(color: Tuple[float, float, float]) -> str:
    """Конвертирует RGB tuple (0-1) в hex строку."""
    r, g, b = [int(c * 255) for c in color]
    return f"#{r:02x}{g:02x}{b:02x}"


def _estimate_font_size(
    text: str, max_width: float, max_height: float, start_size: float
) -> Tuple[float, int]:
    """
    Подбирает размер шрифта так, чтобы текст поместился в bbox.
    Возвращает (font_size, estimated_lines).
    """
    # Примерная оценка: средняя ширина символа ~ 0.55 * font_size для sans-serif
    size = start_size
    min_size = OUTPUT_CONFIG["min_font_size"]
    step = OUTPUT_CONFIG["font_shrink_step"]

    while size >= min_size:
        chars_per_line = max_width / (size * 0.55)
        if chars_per_line <= 0:
            size *= (1 - step)
            continue
        estimated_lines = max(1, len(text) / chars_per_line)
        total_height = estimated_lines * size * OUTPUT_CONFIG["line_spacing"]
        if total_height <= max_height:
            return size, int(estimated_lines) + 1
        size *= (1 - step)

    return min_size, int(len(text) / (max_width / (min_size * 0.55))) + 1


class PDFBuilder:
    """
    Создает переведенный PDF.
    Использует HTML-вставку для корректной поддержки кириллицы.
    """

    def __init__(self, original_pdf_path: str, output_path: str):
        self.doc = fitz.open(original_pdf_path)
        self.output_path = output_path

    def replace_text_blocks(
        self,
        blocks: List[ReplacementBlock],
        progress_callback=None,
    ):
        """Заменяет текст в PDF на переведенный через HTML-вставку."""
        # Группируем по страницам
        pages_blocks: dict = {}
        for block in blocks:
            if not block.translatable:
                continue
            if block.page_num not in pages_blocks:
                pages_blocks[block.page_num] = []
            pages_blocks[block.page_num].append(block)

        total = len(pages_blocks)

        for page_num, page_blocks in pages_blocks.items():
            if progress_callback:
                progress_callback(
                    f"Обработка страницы {page_num + 1}...",
                    page_num, total
                )

            page = self.doc[page_num]

            # Удаляем старый текст
            self._redact_original_text(page, page_blocks)

            # Вставляем новый текст через HTML
            for block in page_blocks:
                self._insert_html_block(page, block)

    def _redact_original_text(self, page, blocks: List[ReplacementBlock]):
        """Удаляет оригинальный текст."""
        for block in blocks:
            x0, y0, x1, y1 = block.bbox
            padding = 2
            try:
                page.add_redact_annot(
                    fitz.Rect(x0 - padding, y0 - padding, x1 + padding, y1 + padding),
                    fill=(1, 1, 1)
                )
            except Exception:
                pass
        try:
            page.apply_redactions()
        except Exception:
            pass

    def _insert_html_block(self, page, block: ReplacementBlock):
        """Вставляет переведенный текст как HTML."""
        translated = block.translated_text
        if not translated or not translated.strip():
            return

        bbox = block.bbox
        x0, y0, x1, y1 = bbox
        available_width = x1 - x0
        available_height = y1 - y0

        if available_width <= 10 or available_height <= 5:
            return

        # Подбираем размер шрифта
        font_size, _ = _estimate_font_size(
            translated, available_width, available_height, block.font_size
        )

        font_size_pt = round(font_size, 1)
        color_hex = _color_to_hex(block.color)

        # Стили
        font_weight = "bold" if block.is_bold else "normal"
        font_style = "italic" if block.is_italic else "normal"
        text_align = "center" if block.block_type == "heading" else "left"

        # Экранируем спецсимволы для HTML
        safe_text = translated.replace("&", "&").replace("<", "<").replace(">", ">")
        safe_text = safe_text.replace("\n", "<br>")

        html = f"""
        <div style="
            font-family: sans-serif;
            font-size: {font_size_pt}pt;
            font-weight: {font_weight};
            font-style: {font_style};
            color: {color_hex};
            text-align: {text_align};
            line-height: 1.2;
            word-wrap: break-word;
            overflow: hidden;
        ">
        {safe_text}
        </div>
        """

        try:
            page.insert_htmlbox(_rect(bbox), html)
        except Exception:
            # Fallback: ещё проще
            try:
                page.insert_htmlbox(
                    _rect(bbox),
                    f'<p style="font-family:sans-serif;font-size:{font_size_pt}pt;color:{color_hex};">{safe_text}</p>'
                )
            except Exception:
                pass

    def render_translated_tables(self, translated_tables, progress_callback=None):
        """Отрисовывает переведенные таблицы через HTML."""
        total = len(translated_tables)
        for idx, table in enumerate(translated_tables):
            if progress_callback:
                progress_callback(f"Таблица {idx + 1}/{total}", idx, total)

            page = self.doc[table.page_num]
            for cell in table.cells:
                if cell.translated_text == cell.original_text:
                    continue
                self._render_table_cell(page, cell)

    def _render_table_cell(self, page, cell):
        """Отрисовывает одну ячейку HTML'ом."""
        x0, y0, x1, y1 = cell.bbox
        w, h = x1 - x0 - 4, y1 - y0 - 4
        if w <= 0 or h <= 0:
            return

        safe = cell.translated_text.replace("&", "&").replace("<", "<").replace(">", ">")
        size, _ = _estimate_font_size(cell.translated_text, w, h, 10)
        size = max(6, min(size, 10))

        html = f'<p style="font-family:sans-serif;font-size:{size:.1f}pt;margin:2px;">{safe}</p>'

        try:
            # Заливаем белым
            page.draw_rect(_rect(cell.bbox), color=(1, 1, 1), fill=(1, 1, 1))
            page.insert_htmlbox(fitz.Rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2), html)
        except Exception:
            pass

    def render_ocr_text(self, ocr_results, translations, progress_callback=None):
        """Отрисовывает OCR текст через HTML."""
        total = len(ocr_results)
        for idx, item in enumerate(ocr_results):
            if progress_callback:
                progress_callback(f"OCR {idx + 1}/{total}", idx, total)

            original = item["text"]
            translated = translations.get(original, original)
            if translated == original:
                continue

            page = self.doc[item["page_num"]]
            x0, y0, x1, y1 = item["bbox"]
            w, h = x1 - x0, y1 - y0
            if w <= 0 or h <= 0:
                continue

            safe = translated.replace("&", "&").replace("<", "<").replace(">", ">")
            size, _ = _estimate_font_size(translated, w, h, min(h / 2, 12))

            html = f'<p style="font-family:sans-serif;font-size:{size:.1f}pt;margin:0;">{safe}</p>'
            try:
                page.insert_htmlbox(_rect(item["bbox"]), html)
            except Exception:
                pass

    def save(self):
        """Сохраняет результат."""
        self.doc.save(self.output_path, deflate=True, garbage=4)
        self.doc.close()

    def get_page_preview(self, page_num: int, dpi: int = 72) -> bytes:
        """Превью страницы в PNG."""
        page = self.doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")