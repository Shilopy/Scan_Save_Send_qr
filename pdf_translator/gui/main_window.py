"""
Главное окно приложения PDF Translator.
Содержит drag & drop область, настройки, прогресс-бар и предпросмотр.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QComboBox, QGroupBox, QFileDialog,
    QMessageBox, QTextEdit, QSplitter, QCheckBox, QLineEdit,
    QTabWidget, QScrollArea, QApplication, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QPixmap, QFont, QIcon, QPalette,
    QColor, QPainter, QPen, QBrush,
)

from config import (
    SUPPORTED_LANGUAGES, TRANSLATOR_CONFIG, OCR_CONFIG,
    CACHE_CONFIG, BASE_DIR, OUTPUT_DIR,
)
from gui.translator_worker import TranslatorWorker


class DropArea(QWidget):
    """Область для drag & drop PDF файлов."""

    file_dropped = object()  # Сигнал-заглушка, используется через вызов родителя

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(400, 200)
        self.setMaximumHeight(250)
        self.file_path: Optional[str] = None
        self._highlighted = False

    def paintEvent(self, event):
        """Отрисовка области с пунктирной рамкой."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Фон
        if self._highlighted:
            painter.setBrush(QBrush(QColor("#e3f2fd")))
        else:
            painter.setBrush(QBrush(QColor("#fafafa")))

        # Рамка
        pen = QPen()
        pen.setColor(QColor("#1976d2") if self._highlighted else QColor("#bdbdbd"))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)

        painter.drawRoundedRect(5, 5, self.width() - 10, self.height() - 10, 15, 15)

        # Текст
        painter.setPen(QColor("#616161"))
        font = QFont("Segoe UI", 14)
        painter.setFont(font)

        if self.file_path:
            filename = os.path.basename(self.file_path)
            size = os.path.getsize(self.file_path) / 1024
            text = f"📄 {filename}\n({size:.1f} КБ)"
        else:
            text = "📂 Перетащите PDF файл сюда\nили нажмите для выбора"

        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.toLocalFile().lower().endswith('.pdf'):
                    self._highlighted = True
                    event.acceptProposedAction()
                    self.update()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._highlighted = False
        self.update()

    def dropEvent(self, event: QDropEvent):
        self._highlighted = False
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                self.file_path = path
                self.update()
                # Ищем MainWindow вверх по иерархии
                win = self.window()
                if win and hasattr(win, 'on_file_selected'):
                    win.on_file_selected(path)
                break

    def mousePressEvent(self, event):
        """Клик для выбора файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF файлы (*.pdf)"
        )
        if file_path:
            self.file_path = file_path
            self.update()
            win = self.window()
            if win and hasattr(win, 'on_file_selected'):
                win.on_file_selected(file_path)


class PreviewWidget(QWidget):
    """Виджет предпросмотра страниц PDF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.image_label = QLabel("Предпросмотр появится здесь")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 500)
        self.image_label.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 8px;"
        )

        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll)

        # Навигация по страницам
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("◀ Предыдущая")
        self.prev_btn.setEnabled(False)

        self.page_label = QLabel("Страница 0/0")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("Следующая ▶")
        self.next_btn.setEnabled(False)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_btn)
        layout.addLayout(nav_layout)


class MainWindow(QMainWindow):
    """Главное окно PDF Translator."""

    def __init__(self):
        super().__init__()
        self.worker: Optional[TranslatorWorker] = None
        self.input_path: Optional[str] = None
        self.output_dir = str(OUTPUT_DIR)
        self.preview_pages = []
        self.current_page = 0

        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        """Создает все UI элементы."""
        self.setWindowTitle("PDF Translator")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # === Drag & Drop область ===
        self.drop_area = DropArea(self)
        main_layout.addWidget(self.drop_area)

        # === Splitter: настройки + предпросмотр ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель — настройки
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 5, 0)

        # Группа: Сервис перевода
        translator_group = QGroupBox("⚙️ Сервис перевода")
        translator_layout = QVBoxLayout(translator_group)

        self.service_combo = QComboBox()
        for key, config in TRANSLATOR_CONFIG.items():
            text = f"{config['name']} - {config['description']}"
            self.service_combo.addItem(text, key)
        # MyMemory по умолчанию (надёжный бесплатный сервис)
        idx = self.service_combo.findData("mymemory")
        if idx >= 0:
            self.service_combo.setCurrentIndex(idx)
        self.service_combo.currentIndexChanged.connect(self._on_service_changed)
        translator_layout.addWidget(QLabel("Сервис:"))
        translator_layout.addWidget(self.service_combo)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API ключ (для DeepL/Yandex)")
        self.api_key_input.setVisible(False)
        self.api_key_label = QLabel("API Ключ:")
        self.api_key_label.setVisible(False)
        translator_layout.addWidget(self.api_key_label)
        translator_layout.addWidget(self.api_key_input)

        left_layout.addWidget(translator_group)

        # Группа: Языки
        lang_group = QGroupBox("🌐 Языки")
        lang_layout = QVBoxLayout(lang_group)

        lang_layout.addWidget(QLabel("Исходный язык:"))
        self.source_lang_combo = QComboBox()
        for code, name in SUPPORTED_LANGUAGES.items():
            self.source_lang_combo.addItem(f"{name} ({code})", code)
        lang_layout.addWidget(self.source_lang_combo)

        lang_layout.addWidget(QLabel("Целевой язык:"))
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItem("Русский (ru)", "ru")
        self.target_lang_combo.addItem("Английский (en)", "en")
        lang_layout.addWidget(self.target_lang_combo)

        left_layout.addWidget(lang_group)

        # Группа: OCR
        ocr_group = QGroupBox("🔍 OCR (для сканов)")
        ocr_layout = QVBoxLayout(ocr_group)

        self.ocr_check = QCheckBox("Использовать OCR")
        self.ocr_check.setChecked(True)
        ocr_layout.addWidget(self.ocr_check)

        self.ocr_engine_combo = QComboBox()
        for key, config in OCR_CONFIG.items():
            self.ocr_engine_combo.addItem(
                f"{config['name']} - {config.get('description', '')}", key
            )
        ocr_layout.addWidget(QLabel("OCR движок:"))
        ocr_layout.addWidget(self.ocr_engine_combo)

        left_layout.addWidget(ocr_group)

        # Группа: Кэш
        cache_group = QGroupBox("💾 Кэш")
        cache_layout = QVBoxLayout(cache_group)

        self.cache_check = QCheckBox("Использовать кэш переводов")
        self.cache_check.setChecked(CACHE_CONFIG["enabled"])
        cache_layout.addWidget(self.cache_check)

        self.clear_cache_btn = QPushButton("🗑️ Очистить кэш")
        self.clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addWidget(self.clear_cache_btn)

        left_layout.addWidget(cache_group)

        # Информация о файле
        self.file_info_label = QLabel("Файл не выбран")
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet(
            "color: #616161; font-size: 12px; padding: 8px; "
            "background-color: #f5f5f5; border-radius: 6px;"
        )
        left_layout.addWidget(self.file_info_label)

        left_layout.addStretch()

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("🚀 Перевести")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_translation)
        btn_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_translation)
        btn_layout.addWidget(self.cancel_btn)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Правая панель — предпросмотр
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 0, 0)

        preview_group = QGroupBox("👁️ Предпросмотр")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = PreviewWidget()
        self.preview_widget.prev_btn.clicked.connect(self._prev_page)
        self.preview_widget.next_btn.clicked.connect(self._next_page)
        preview_layout.addWidget(self.preview_widget)

        right_layout.addWidget(preview_group)
        splitter.addWidget(right_panel)

        splitter.setSizes([380, 680])
        main_layout.addWidget(splitter)

        # === Прогресс ===
        progress_group = QGroupBox("📊 Прогресс")
        progress_layout = QVBoxLayout(progress_group)

        self.step_label = QLabel("Ожидание...")
        self.step_label.setFont(QFont("Segoe UI", 10))
        progress_layout.addWidget(self.step_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        progress_layout.addWidget(self.detail_label)

        main_layout.addWidget(progress_group)

        # === Статус бар ===
        self.statusBar().showMessage("Готов к работе")

    def _apply_style(self):
        """Применяет стили."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #757575;
            }
            QPushButton#cancel_btn {
                background-color: #d32f2f;
            }
            QPushButton#cancel_btn:hover {
                background-color: #c62828;
            }
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                background-color: #ffffff;
                color: #212121;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 1px solid #1976d2;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #212121;
                selection-background-color: #e3f2fd;
                selection-color: #212121;
                border: 1px solid #bdbdbd;
                outline: none;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdbdbd;
                border-radius: 6px;
                background-color: #ffffff;
                color: #212121;
                font-size: 13px;
            }
            QLabel {
                color: #424242;
                font-size: 13px;
            }
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                text-align: center;
                height: 22px;
                background-color: #f5f5f5;
                color: #212121;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 5px;
            }
            QCheckBox {
                font-size: 13px;
                color: #212121;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def on_file_selected(self, path: str):
        """Обработчик выбора файла."""
        self.input_path = path
        self.start_btn.setEnabled(True)

        size_mb = os.path.getsize(path) / (1024 * 1024)
        filename = os.path.basename(path)

        self.file_info_label.setText(
            f"📄 {filename}\n"
            f"📏 Размер: {size_mb:.2f} МБ\n"
            f"📁 {os.path.dirname(path)}"
        )

        self.statusBar().showMessage(f"Выбран: {filename}")

        # Показываем превью первой страницы
        self._load_preview(path)

    def _load_preview(self, path: str):
        """Загружает превью первой страницы."""
        try:
            import fitz

            doc = fitz.open(path)
            self.preview_pages = []
            self.current_page = 0

            for page_num in range(min(len(doc), 10)):  # Max 10 preview pages
                page = doc[page_num]
                mat = fitz.Matrix(0.5, 0.5)  # 50% размер для предпросмотра
                pix = page.get_pixmap(matrix=mat)
                self.preview_pages.append(pix.tobytes("png"))
            doc.close()

            self._show_page(0)

            total = len(self.preview_pages)
            self.preview_widget.prev_btn.setEnabled(False)
            self.preview_widget.next_btn.setEnabled(total > 1)
            self.preview_widget.page_label.setText(f"Страница 1/{total}")

        except Exception as e:
            self.preview_widget.image_label.setText(f"Ошибка загрузки: {e}")

    def _show_page(self, index: int):
        """Показывает страницу предпросмотра."""
        if 0 <= index < len(self.preview_pages):
            pixmap = QPixmap()
            pixmap.loadFromData(self.preview_pages[index])
            self.preview_widget.image_label.setPixmap(pixmap)
            self.preview_widget.page_label.setText(
                f"Страница {index + 1}/{len(self.preview_pages)}"
            )

    def _prev_page(self):
        """Предыдущая страница предпросмотра."""
        if self.current_page > 0:
            self.current_page -= 1
            self._show_page(self.current_page)
            self.preview_widget.prev_btn.setEnabled(self.current_page > 0)
            self.preview_widget.next_btn.setEnabled(True)

    def _next_page(self):
        """Следующая страница предпросмотра."""
        if self.current_page < len(self.preview_pages) - 1:
            self.current_page += 1
            self._show_page(self.current_page)
            self.preview_widget.next_btn.setEnabled(
                self.current_page < len(self.preview_pages) - 1
            )
            self.preview_widget.prev_btn.setEnabled(True)

    def _on_service_changed(self, index: int):
        """Обработчик смены сервиса перевода."""
        service = self.service_combo.currentData()
        requires_key = TRANSLATOR_CONFIG[service]["api_key_required"]

        self.api_key_label.setVisible(requires_key)
        self.api_key_input.setVisible(requires_key)

    def _start_translation(self):
        """Запускает перевод."""
        if not self.input_path:
            QMessageBox.warning(self, "Ошибка", "Выберите PDF файл!")
            return

        # Формируем путь для выходного файла
        input_name = os.path.splitext(os.path.basename(self.input_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{input_name}_RU_{timestamp}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        service = self.service_combo.currentData()
        api_key = self.api_key_input.text().strip() if TRANSLATOR_CONFIG[service]["api_key_required"] else ""
        source_lang = self.source_lang_combo.currentData()
        target_lang = self.target_lang_combo.currentData()
        use_cache = self.cache_check.isChecked()
        use_ocr = self.ocr_check.isChecked()
        ocr_engine = self.ocr_engine_combo.currentData()

        if TRANSLATOR_CONFIG[service]["api_key_required"] and not api_key:
            QMessageBox.warning(self, "Ошибка", f"Введите API ключ для {TRANSLATOR_CONFIG[service]['name']}!")
            return

        # Блокируем UI
        self._set_ui_enabled(False)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.step_label.setText("Начинаю...")
        self.detail_label.setText("")

        # Создаем worker
        self.worker = TranslatorWorker(
            input_path=self.input_path,
            output_path=output_path,
            service=service,
            api_key=api_key,
            source_lang=source_lang,
            target_lang=target_lang,
            use_cache=use_cache,
            use_ocr=use_ocr,
            ocr_engine=ocr_engine,
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.step_changed.connect(self._on_step_changed)
        self.worker.finished.connect(self._on_finished)

        self.worker.start()

    def _cancel_translation(self):
        """Отменяет перевод."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.step_label.setText("Отмена...")
            self.detail_label.setText("Ожидание завершения текущей операции...")

    def _on_progress(self, message: str, current: int, total: int):
        """Обновление прогресса."""
        self.detail_label.setText(message)
        if total > 0:
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)

    def _on_step_changed(self, step: str):
        """Смена шага."""
        self.step_label.setText(step)
        self.statusBar().showMessage(step)

    def _on_finished(self, success: bool, result: str):
        """Завершение перевода."""
        self._set_ui_enabled(True)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.step_label.setText("✅ Готово!")
            self.detail_label.setText(f"Файл сохранен:\n{result}")
            self.statusBar().showMessage("Перевод завершен!")

            reply = QMessageBox.question(
                self,
                "Успешно!",
                f"Перевод завершен!\n\nФайл: {os.path.basename(result)}\n\nОткрыть папку с файлом?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(os.path.dirname(result))
        else:
            self.step_label.setText("❌ Ошибка")
            self.detail_label.setText(f"Ошибка: {result}")
            self.statusBar().showMessage("Ошибка перевода")

    def _set_ui_enabled(self, enabled: bool):
        """Включает/выключает элементы UI."""
        self.service_combo.setEnabled(enabled)
        self.source_lang_combo.setEnabled(enabled)
        self.target_lang_combo.setEnabled(enabled)
        self.ocr_check.setEnabled(enabled)
        self.ocr_engine_combo.setEnabled(enabled)
        self.cache_check.setEnabled(enabled)
        self.clear_cache_btn.setEnabled(enabled)
        self.api_key_input.setEnabled(enabled)

    def _clear_cache(self):
        """Очищает кэш переводов."""
        reply = QMessageBox.question(
            self,
            "Очистить кэш",
            "Удалить весь кэш переводов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            from utils.cache_manager import TranslationCache
            cache = TranslationCache()
            cache.clear()
            stats = cache.stats()
            QMessageBox.information(
                self, "Кэш очищен",
                f"Записей: {stats['entries']}\nРазмер: {stats['size_kb']} КБ"
            )