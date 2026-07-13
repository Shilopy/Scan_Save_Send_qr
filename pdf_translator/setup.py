"""
Установщик зависимостей PDF Translator.
Проверяет и устанавливает все нужные пакеты.
При проблемах с PyPI автоматически пробует зеркала.
Использование:
    python setup.py          # интерактивный режим (спросит про опциональные)
    python setup.py --auto   # автоматический режим (ставит всё без вопросов)
"""

import subprocess
import sys
import importlib
import os
import time
import argparse


def run_pip(args, timeout=300):
    """Запускает pip install с заданными аргументами."""
    cmd = [sys.executable, "-m", "pip", "install"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def check_package(package_name, import_name=None):
    """Проверяет, установлен ли пакет."""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def get_version(package_name, import_name=None):
    """Возвращает версию установленного пакета."""
    if import_name is None:
        import_name = package_name.replace("-", "_").lower()
    try:
        mod = importlib.import_module(import_name)
        for attr in ["__version__", "VERSION", "version"]:
            if hasattr(mod, attr):
                return getattr(mod, attr)
    except Exception:
        pass
    return "?"


MIRRORS = [
    ("PyPI (официальный)", "https://pypi.org/simple/", 60),
    ("USTC (Китай)", "https://mirrors.ustc.edu.cn/pypi/web/simple/", 300),
    ("Aliyun (Китай)", "https://mirrors.aliyun.com/pypi/simple/", 300),
    ("Tsinghua (Китай)", "https://pypi.tuna.tsinghua.edu.cn/simple/", 300),
]

# Зависимости: [(pip_name, import_name, required, description)]
DEPENDENCIES = [
    ("pymupdf", "fitz", True, "PyMuPDF — работа с PDF (v1.24+)"),
    ("deep-translator", "deep_translator", True, "Deep Translator — Google/Yandex перевод"),
    ("pdfplumber", "pdfplumber", True, "pdfplumber — извлечение таблиц"),
    ("langdetect", "langdetect", True, "langdetect — определение языка"),
    ("requests", "requests", True, "requests — HTTP запросы (DeepL API)"),
    ("PyQt6", "PyQt6", True, "PyQt6 — графический интерфейс"),
    ("Pillow", "PIL", False, "Pillow — обработка изображений (OCR)"),
    ("pytesseract", "pytesseract", False, "pytesseract — Tesseract OCR"),
    ("paddlepaddle", "paddle", False, "PaddlePaddle — нейросети (PaddleOCR)"),
    ("paddleocr", "paddleocr", False, "PaddleOCR — распознавание китайского"),
    ("opencv-python", "cv2", False, "OpenCV — обработка изображений"),
]


def install_package(package_name, version=None):
    """Устанавливает пакет, пробуя разные зеркала."""
    pkg = f"{package_name}>={version}" if version else package_name

    for mirror_name, mirror_url, timeout in MIRRORS:
        print(f"  ⏳ Пробуем: {mirror_name}...")
        success, output = run_pip(
            ["-i", mirror_url, "--trusted-host", mirror_url.split("/")[2],
             "--default-timeout", str(timeout), "--retries", "3",
             pkg],
            timeout=timeout + 60,
        )
        if success:
            print(f"  ✅ Установлено через {mirror_name}")
            return True
        elif "TIMEOUT" in output:
            print(f"  ⚠️  Таймаут на {mirror_name}, пробую следующий...")
        else:
            if "already satisfied" in output.lower() or "requirement already satisfied" in output.lower():
                print(f"  ✅ Уже установлено")
                return True
            print(f"  ❌ Ошибка на {mirror_name}")

    return False


def main():
    """Основная функция установки."""
    parser = argparse.ArgumentParser(description="PDF Translator — установка зависимостей")
    parser.add_argument("--auto", action="store_true", help="Автоматическая установка (без вопросов)")
    args = parser.parse_args()

    print("=" * 55)
    print("  PDF Translator — Установка зависимостей")
    print("=" * 55)
    print()

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"🐍 Python: {py_version} ({sys.executable})")

    if sys.version_info < (3, 10):
        print("❌ Требуется Python 3.10 или выше!")
        return 1

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except Exception:
        print("❌ pip не найден! Установите pip.")
        return 1

    print()

    missing_required = []
    missing_optional = []
    installed = []

    print("📋 Проверка зависимостей...\n")

    for pip_name, import_name, required, description in DEPENDENCIES:
        status = "✅" if check_package(import_name) else "❌"
        version = get_version(import_name)
        ver_str = f" v{version}" if version and version != "?" else ""

        print(f"  {status} {pip_name}{ver_str} — {description} {'(обязательно)' if required else '(опционально)'}")

        if status == "❌":
            if required:
                missing_required.append((pip_name, import_name))
            else:
                missing_optional.append((pip_name, import_name))
        else:
            installed.append(pip_name)

    print()

    if missing_required:
        print(f"📦 Установка {len(missing_required)} обязательных пакетов...\n")
        for pip_name, import_name in missing_required:
            print(f"  📥 {pip_name}...")
            if install_package(pip_name):
                installed.append(pip_name)
            else:
                print(f"  ❌ Не удалось установить {pip_name}!")
                return 1
        print()

    if missing_optional:
        if args.auto:
            install_opt = True
        else:
            print(f"📦 Опциональные пакеты ({len(missing_optional)}):")
            for pip_name, import_name in missing_optional:
                desc = next(d[3] for d in DEPENDENCIES if d[0] == pip_name)
                print(f"  • {pip_name} — {desc}")
            print()
            answer = input("Установить опциональные пакеты? [Y/n]: ").strip().lower()
            install_opt = answer in ("", "y", "yes", "да")

        if install_opt:
            print(f"\n📦 Установка {len(missing_optional)} опциональных пакетов...\n")
            for pip_name, import_name in missing_optional:
                print(f"  📥 {pip_name}...")
                success = install_package(pip_name)
                if success:
                    installed.append(pip_name)
        else:
            print("⏭️  Опциональные пакеты пропущены\n")

    print()
    print("🔍 Проверка версий...")

    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()

        if hasattr(page, "insert_htmlbox"):
            print("  ✅ PyMuPDF поддерживает insert_htmlbox (кириллица будет работать)")
        else:
            print("  ⚠️  PyMuPDF не поддерживает insert_htmlbox — обновляю...")
            doc.close()
            if install_package("pymupdf", version="1.24.0"):
                print("  ✅ PyMuPDF обновлён")
            else:
                print("  ❌ Не удалось обновить PyMuPDF. Кириллица может не работать.")

        doc.close()
        del doc
    except Exception as e:
        print(f"  ⚠️  Ошибка проверки PyMuPDF: {e}")

    print()
    print("=" * 55)
    print("  ✅ Установка завершена!")
    print(f"  Установлено пакетов: {len(installed)}")
    print()
    print("  Для запуска:")
    print("    python main.py")
    print("    или двойной клик по run.bat")
    print("=" * 55)

    return 0


if __name__ == "__main__":
    sys.exit(main())