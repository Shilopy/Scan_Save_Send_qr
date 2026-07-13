"""
PDF Translator — программа для перевода PDF файлов с сохранением форматирования.
Поддерживает: таблицы, OCR для сканов, кэширование, прогресс-бар.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Translator")
    app.setOrganizationName("PDFTranslator")

    # Устанавливаем стиль
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()