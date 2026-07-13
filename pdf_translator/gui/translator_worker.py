"""
Рабочий поток для перевода PDF.
Выполняет всю тяжелую работу в фоновом потоке, отправляя сигналы о прогрессе.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Optional, Callable
from pathlib import Path

from core.pdf_parser import PDFParser, PDFContent
from core.pdf_builder import ReplacementBlock
from core.translator import create_translator, BaseTranslator
from core.pdf_builder import PDFBuilder
from core.table_detector import TableDetector
from core.ocr_processor import OCRProcessor
from utils.lang_detect import detect_language, has_cjk


class TranslatorWorker(QThread):
    """
    Фоновый поток для выполнения перевода PDF.
    Не блокирует GUI.
    """

    # Сигналы
    progress = pyqtSignal(str, int, int)  # message, current, total
    step_changed = pyqtSignal(str)         # название текущего шага
    finished = pyqtSignal(bool, str)       # success, output_path/error_message
    preview_ready = pyqtSignal(int, bytes) # page_num, image_bytes

    def __init__(
        self,
        input_path: str,
        output_path: str,
        service: str = "google",
        api_key: str = "",
        source_lang: str = "auto",
        target_lang: str = "ru",
        use_cache: bool = True,
        use_ocr: bool = True,
        ocr_engine: str = "paddleocr",
    ):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.service = service
        self.api_key = api_key
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.use_cache = use_cache
        self.use_ocr = use_ocr
        self.ocr_engine = ocr_engine
        self._cancelled = False

    def cancel(self):
        """Отменяет операцию."""
        self._cancelled = True

    def run(self):
        """Основной метод потока."""
        try:
            self._translate_pdf()
        except Exception as e:
            self.finished.emit(False, str(e))

    def _translate_pdf(self):
        """Полный пайплайн перевода PDF."""
        # Шаг 1: Парсинг PDF
        self.step_changed.emit("Парсинг PDF...")
        parser = PDFParser(self.input_path)
        content = parser.parse()

        if self._cancelled:
            parser.close()
            self.finished.emit(False, "Отменено пользователем")
            return

        self.progress.emit(
            f"Найдено {len(content.text_blocks)} текстовых блоков на {content.total_pages} стр.",
            1, 5,
        )

        # Собираем тексты для перевода
        translatable_blocks = [
            b for b in content.text_blocks
            if b.spans and any(s.translatable for s in b.spans)
        ]

        texts_to_translate = [
            b.text for b in translatable_blocks
        ]

        # Добавляем тексты из таблиц
        all_table_cells = []
        if content.tables:
            for table in content.tables:
                for cell in table.get("cells", []):
                    if cell["text"].strip():
                        all_table_cells.append(cell)

        texts_to_translate.extend(
            c["text"] for c in all_table_cells
        )

        # Если нужен OCR — обрабатываем страницы
        ocr_results = []
        if self.use_ocr and content.has_scanned_pages:
            ocr_results = self._process_ocr(parser, content)
            texts_to_translate.extend(
                r["text"] for r in ocr_results
            )

        # Шаг 2: Перевод
        self.step_changed.emit("Перевод текста...")

        # Автоопределение языка если нужно
        if self.source_lang == "auto" and texts_to_translate:
            sample = " ".join(texts_to_translate[:10])
            detected = detect_language(sample)
            self.source_lang = detected

        translator = create_translator(
            service=self.service,
            api_key=self.api_key,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
        )

        # Переводим пакетно с прогрессом
        total_texts = len(texts_to_translate)
        translated = []

        batch_size = 50
        for i in range(0, total_texts, batch_size):
            if self._cancelled:
                self.finished.emit(False, "Отменено пользователем")
                return

            batch = texts_to_translate[i:i + batch_size]
            batch_translated = translator.translate_batch(batch)
            translated.extend(batch_translated)

            self.progress.emit(
                f"Переведено {min(i + batch_size, total_texts)}/{total_texts} фрагментов",
                min(i + batch_size, total_texts), total_texts + 1,
            )

        # Строим словарь переводов
        translations = {}
        block_count = len(translatable_blocks)

        for i, block in enumerate(translatable_blocks):
            if i < len(translated):
                translations[block.text] = translated[i]

        # Добавляем переводы ячеек таблиц
        cell_offset = block_count
        for j, cell in enumerate(all_table_cells):
            idx = cell_offset + j
            if idx < len(translated):
                translations[cell["text"]] = translated[idx]

        # Добавляем переводы OCR
        ocr_offset = block_count + len(all_table_cells)
        for k, item in enumerate(ocr_results):
            idx = ocr_offset + k
            if idx < len(translated):
                translations[item["text"]] = translated[idx]

        # Шаг 3: Реконструкция PDF
        self.step_changed.emit("Формирование переведенного PDF...")

        builder = PDFBuilder(self.input_path, self.output_path)

        # Формируем блоки для замены
        replacement_blocks = []

        for block in translatable_blocks:
            translated_text = translations.get(block.text, block.text)
            first_span = block.spans[0]

            rb = ReplacementBlock(
                page_num=first_span.page_num,
                bbox=block.bbox,
                original_text=block.text,
                translated_text=translated_text,
                original_font=first_span.font,
                font_size=first_span.size,
                color=first_span.color,
                is_bold=first_span.is_bold,
                is_italic=first_span.is_italic,
                block_type=block.block_type,
                translatable=True,
            )
            replacement_blocks.append(rb)

        # Заменяем текст
        builder.replace_text_blocks(
            replacement_blocks,
            progress_callback=self._builder_progress,
        )

        # Обрабатываем таблицы
        if content.tables:
            self.step_changed.emit("Перевод таблиц...")
            table_detector = TableDetector()
            translated_tables = table_detector.process_tables(
                content.tables, translations
            )
            builder.render_translated_tables(translated_tables)

        # Обрабатываем OCR результаты
        if ocr_results:
            self.step_changed.emit("Вставка OCR текста...")
            builder.render_ocr_text(ocr_results, translations)

        # Сохраняем
        self.step_changed.emit("Сохранение...")
        builder.save()
        parser.close()

        self.finished.emit(True, self.output_path)

    def _process_ocr(self, parser: PDFParser, content: PDFContent) -> list:
        """Обрабатывает страницы через OCR."""
        ocr = OCRProcessor(engine=self.ocr_engine)
        ocr_results = []

        self.step_changed.emit("OCR распознавание...")

        for page_num in range(content.total_pages):
            if self._cancelled:
                break

            page_images = parser.get_page_images(page_num)
            for img_info in page_images:
                results = ocr.process_pdf_page(
                    img_info["pixmap"], page_num
                )
                ocr_results.extend(results)

            self.progress.emit(
                f"OCR: {page_num + 1}/{content.total_pages}",
                page_num + 1, content.total_pages,
            )

        return ocr_results

    def _builder_progress(self, message: str, current: int, total: int):
        """Callback для прогресса реконструкции."""
        self.progress.emit(message, current, total)