"""
Детектор и обработчик таблиц в PDF.
Извлекает таблицы, переводит содержимое ячеек, восстанавливает структуру.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TableCell:
    """Ячейка таблицы с переводом."""

    row: int
    col: int
    original_text: str
    translated_text: str
    bbox: Tuple[float, float, float, float]


@dataclass
class TranslatedTable:
    """Переведенная таблица."""

    page_num: int
    table_index: int
    bbox: Tuple[float, float, float, float]
    rows: int
    cols: int
    cells: List[TableCell]
    col_widths: List[float]
    row_heights: List[float]


class TableDetector:
    """
    Обрабатывает таблицы: вычисляет ширину столбцов, высоту строк,
    подготавливает данные для рендеринга.
    """

    def __init__(self):
        self.tables: List[TranslatedTable] = []

    def process_tables(
        self, tables_data: List[dict], translations: dict
    ) -> List[TranslatedTable]:
        """
        Обрабатывает таблицы из PDF, связывая с переводами.

        Args:
            tables_data: список таблиц из PDFParser
            translations: словарь {original_text: translated_text}
        """
        self.tables = []

        for table in tables_data:
            cells = []

            for cell_info in table.get("cells", []):
                original = cell_info["text"]
                translated = translations.get(original, original)

                cells.append(
                    TableCell(
                        row=cell_info["row"],
                        col=cell_info["col"],
                        original_text=original,
                        translated_text=translated,
                        bbox=cell_info["bbox"],
                    )
                )

            if not cells:
                continue

            # Вычисляем ширину столбцов и высоту строк
            col_widths = self._calculate_column_widths(cells, table)
            row_heights = self._calculate_row_heights(cells, table)

            self.tables.append(
                TranslatedTable(
                    page_num=table["page_num"],
                    table_index=table["table_index"],
                    bbox=table["bbox"],
                    rows=table["rows"],
                    cols=table["cols"],
                    cells=cells,
                    col_widths=col_widths,
                    row_heights=row_heights,
                )
            )

        return self.tables

    def _calculate_column_widths(
        self, cells: List[TableCell], table: dict
    ) -> List[float]:
        """Вычисляет ширину каждого столбца."""
        if not cells:
            return []

        cols = max(c.col for c in cells) + 1
        col_widths = defaultdict(float)

        # Собираем максимальную ширину ячейки в каждом столбце
        for cell in cells:
            width = cell.bbox[2] - cell.bbox[0]
            col_widths[cell.col] = max(col_widths[cell.col], width)

        # Нормализуем
        total_width = table["bbox"][2] - table["bbox"][0]
        result = [col_widths.get(i, 0) for i in range(cols)]

        # Если колонки не заняли всю ширину — растягиваем пропорционально
        total = sum(result)
        if total > 0:
            result = [w / total * total_width for w in result]

        return result

    def _calculate_row_heights(
        self, cells: List[TableCell], table: dict
    ) -> List[float]:
        """Вычисляет высоту каждой строки."""
        if not cells:
            return []

        rows = max(c.row for c in cells) + 1
        row_heights = defaultdict(float)

        for cell in cells:
            height = cell.bbox[3] - cell.bbox[1]
            row_heights[cell.row] = max(row_heights[cell.row], height)

        result = [row_heights.get(i, 20) for i in range(rows)]
        return result

    def redistribute_widths(
        self, table: TranslatedTable, length_ratios: List[List[float]]
    ) -> List[float]:
        """
        Перераспределяет ширину колонок с учетом увеличения длины текста при переводе.

        Args:
            table: переведенная таблица
            length_ratios: матрица коэффициентов увеличения [row][col]
        """
        cols = table.cols
        new_widths = list(table.col_widths)

        # Находим максимальное увеличение для каждой колонки
        for col in range(cols):
            max_ratio = 1.0
            for row in range(table.rows):
                if row < len(length_ratios) and col < len(length_ratios[row]):
                    max_ratio = max(max_ratio, length_ratios[row][col])
            new_widths[col] *= min(max_ratio, 2.5)  # Максимальное увеличение x2.5

        # Нормализуем к общей ширине
        total_original = sum(table.col_widths)
        total_new = sum(new_widths)
        if total_original > 0:
            new_widths = [w / total_new * total_original for w in new_widths]

        return new_widths

    def get_cell_bbox(
        self, table: TranslatedTable, row: int, col: int
    ) -> Tuple[float, float, float, float]:
        """Возвращает bbox ячейки таблицы."""
        x0 = table.bbox[0]
        y0 = table.bbox[1]

        # Суммируем ширины предыдущих колонок
        col_x = sum(table.col_widths[:col])
        col_y = sum(table.row_heights[:row])

        x0_cell = x0 + col_x
        y0_cell = y0 + col_y
        x1_cell = x0_cell + table.col_widths[col]
        y1_cell = y0_cell + table.row_heights[row]

        return (x0_cell, y0_cell, x1_cell, y1_cell)