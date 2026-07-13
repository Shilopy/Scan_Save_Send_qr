"""
Утилиты для работы с текстом: измерение, перенос строк, разбивка
"""

import re
import fitz


def measure_text_width(text: str, fontname: str, fontsize: float) -> float:
    """
    Измеряет ширину текста в пунктах с заданным шрифтом и размером.
    Использует встроенную функцию PyMuPDF.
    """
    try:
        return fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
    except Exception:
        # Fallback: примерная оценка
        return len(text) * fontsize * 0.5


def wrap_text_to_width(
    text: str,
    fontname: str,
    fontsize: float,
    max_width: float,
    max_lines: int = 0,
) -> list[str]:
    """
    Разбивает текст на строки, помещающиеся в max_width.
    Если max_lines > 0, ограничивает количество строк (добавляет "...").
    """
    if not text:
        return [""]

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = measure_text_width(test_line, fontname, fontsize)

        if width <= max_width:
            current_line = test_line
        else:
            # Слово не помещается в текущую строку
            if current_line:
                lines.append(current_line)

            # Если одно слово шире max_width — принудительно разбиваем по символам
            word_width = measure_text_width(word, fontname, fontsize)
            if word_width > max_width:
                # Разбиваем слово по символам
                current_part = ""
                for ch in word:
                    test_part = current_part + ch
                    if measure_text_width(test_part, fontname, fontsize) <= max_width:
                        current_part = test_part
                    else:
                        if current_part:
                            lines.append(current_part)
                        current_part = ch
                current_line = current_part
            else:
                current_line = word

            # Проверяем лимит строк
            if max_lines > 0 and len(lines) >= max_lines:
                if len(lines) > 0:
                    lines[-1] = lines[-1].rstrip() + "..."
                return lines

    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


def calculate_font_size(
    text: str,
    fontname: str,
    max_width: float,
    max_height: float,
    start_size: float,
    min_size: float = 6.0,
    step: float = 0.05,
    line_spacing: float = 1.2,
) -> tuple[float, list[str]]:
    """
    Подбирает максимальный размер шрифта, при котором текст помещается
    в заданные ширину и высоту. Возвращает (font_size, lines).
    """
    size = start_size

    while size >= min_size:
        lines = wrap_text_to_width(text, fontname, size, max_width)
        total_height = len(lines) * size * line_spacing

        if total_height <= max_height:
            return size, lines

        size *= (1 - step)

    # Минимальный размер — принудительно влазим
    lines = wrap_text_to_width(text, fontname, min_size, max_width)
    return min_size, lines


def split_into_sentences(text: str) -> list[str]:
    """Разбивает текст на предложения (с сохранением разделителей)."""
    pattern = r'(?<=[.!?。！？\n])\s+'
    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def clean_text(text: str) -> str:
    """Очищает текст от лишних пробелов и спецсимволов."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def is_translatable(text: str) -> bool:
    """
    Проверяет, нужно ли переводить текст.
    Пропускаем: числа, спецсимволы, email, URL, одиночные символы.
    """
    if not text or len(text.strip()) < 2:
        return False

    stripped = text.strip()

    # Только цифры и знаки пунктуации
    if re.match(r'^[\d\s.,;:!?\-–—()\[\]{}<>+*/%=#@&|\\^~`\'"]+$', stripped):
        return False

    # Email
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', stripped):
        return False

    # URL
    if re.match(r'^https?://', stripped):
        return False

    return True


def normalize_quotes(text: str) -> str:
    """Нормализует кавычки для русского языка: заменяет английские на «ёлочки»."""
    # Уже содержит русские кавычки
    if '«' in text or '»' in text:
        return text

    # Простая замена: " -> «» (чередование)
    result = []
    quote_open = True
    for ch in text:
        if ch == '"':
            result.append('«' if quote_open else '»')
            quote_open = not quote_open
        elif ch == "'":
            result.append(ch)  # оставляем как есть
        else:
            result.append(ch)

    return ''.join(result)