"""
OCR процессор для сканированных PDF.
Поддерживает Tesseract и PaddleOCR.
"""

from typing import List, Optional, Tuple
from pathlib import Path
import tempfile
import os

from config import OCR_CONFIG


class OCRProcessor:
    """
    Распознает текст на сканированных страницах PDF.
    Приоритет:
    1. PaddleOCR (лучше для китайского)
    2. Tesseract (хорош для английского)
    """

    def __init__(self, engine: str = "paddleocr", languages: str = "eng+chi_sim+chi_tra"):
        self.engine = engine
        self.languages = languages
        self._ocr_engine = None
        self._initialized = False

    def initialize(self):
        """Инициализирует OCR движок."""
        if self._initialized:
            return

        if self.engine == "paddleocr":
            self._init_paddleocr()
        elif self.engine == "tesseract":
            self._init_tesseract()
        else:
            # Пробуем оба
            try:
                self._init_paddleocr()
            except Exception:
                self._init_tesseract()

        self._initialized = True

    def _init_paddleocr(self):
        """Инициализация PaddleOCR."""
        try:
            from paddleocr import PaddleOCR

            self._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang="ch",  # Поддерживает китайский + английский + русский
                use_gpu=False,
                show_log=False,
            )
            self.engine = "paddleocr"
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr"
            )

    def _init_tesseract(self):
        """Инициализация Tesseract."""
        try:
            import pytesseract

            self._ocr_engine = pytesseract
            self.engine = "tesseract"
        except ImportError:
            raise ImportError(
                "Tesseract not installed. Install with: pip install pytesseract"
            )

    def recognize_text(
        self, image_or_path
    ) -> List[dict]:
        """
        Распознает текст на изображении.

        Args:
            image_or_path: PIL Image, numpy array, или путь к файлу

        Returns:
            Список словарей: [{text, confidence, bbox, page_num}, ...]
        """
        if not self._initialized:
            self.initialize()

        if self.engine == "paddleocr":
            return self._recognize_paddleocr(image_or_path)
        else:
            return self._recognize_tesseract(image_or_path)

    def _recognize_paddleocr(self, image) -> List[dict]:
        """Распознавание через PaddleOCR."""
        results = []

        try:
            # Сохраняем изображение во временный файл если это numpy array
            if hasattr(image, "save"):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    img_path = f.name
                    image.save(img_path)
            elif isinstance(image, str):
                img_path = image
            else:
                import numpy as np
                from PIL import Image as PILImage

                img = PILImage.fromarray(image)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                    img_path = f.name
                    img.save(img_path)

            ocr_result = self._ocr_engine.ocr(img_path, cls=True)

            if ocr_result and ocr_result[0]:
                for line in ocr_result[0]:
                    bbox_points = line[0]
                    text = line[1][0]
                    confidence = line[1][1]

                    # Конвертируем 4 точки в bbox (x0, y0, x1, y1)
                    xs = [p[0] for p in bbox_points]
                    ys = [p[1] for p in bbox_points]
                    bbox = (min(xs), min(ys), max(xs), max(ys))

                    results.append(
                        {
                            "text": text,
                            "confidence": confidence,
                            "bbox": bbox,
                        }
                    )

            # Удаляем временный файл
            if img_path != image and os.path.exists(img_path):
                os.unlink(img_path)

        except Exception as e:
            pass

        return results

    def _recognize_tesseract(self, image) -> List[dict]:
        """Распознавание через Tesseract."""
        results = []

        try:
            import pytesseract
            from PIL import Image as PILImage

            if isinstance(image, str):
                img = PILImage.open(image)
            else:
                img = image

            # Получаем слова с координатами
            data = pytesseract.image_to_data(img, lang=self.languages, output_type=pytesseract.Output.DICT)

            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if not text:
                    continue

                conf = int(data["conf"][i])
                if conf < 30:  # Минимальная уверенность
                    continue

                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]

                results.append(
                    {
                        "text": text,
                        "confidence": conf / 100.0,
                        "bbox": (x, y, x + w, y + h),
                    }
                )

        except Exception as e:
            pass

        return results

    def process_pdf_page(
        self, pixmap, page_num: int, dpi: int = 150
    ) -> List[dict]:
        """
        Обрабатывает страницу PDF через OCR.

        Args:
            pixmap: PyMuPDF pixmap объект
            page_num: номер страницы
            dpi: разрешение

        Returns:
            Список распознанных текстовых блоков с координатами
        """
        from PIL import Image as PILImage

        # Конвертируем pixmap в PIL Image
        img_data = pixmap.tobytes("png")
        from io import BytesIO

        img = PILImage.open(BytesIO(img_data))

        # Распознаем
        results = self.recognize_text(img)

        # Добавляем номер страницы
        for r in results:
            r["page_num"] = page_num

        return results

    @staticmethod
    def is_ocr_needed(pdf_path: str, threshold: int = 50) -> bool:
        """
        Проверяет, нужен ли OCR для PDF.
        Если среднее количество текста на страницу < threshold символов — нужен OCR.
        """
        import fitz

        doc = fitz.open(pdf_path)
        total_text = sum(len(page.get_text().strip()) for page in doc)
        avg = total_text / max(len(doc), 1)
        doc.close()
        return avg < threshold