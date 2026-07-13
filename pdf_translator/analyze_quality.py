"""
Анализ качества перевода PDF.
Сравнивает исходный и переведённый PDF: структура, таблицы, текст.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
import json

output_dir = os.path.join(os.path.dirname(__file__), "output")
files = os.listdir(output_dir)

# Разделяем исходник и перевод
originals = [f for f in files if not f.startswith("MSDS_APHYS_H926_HT-GBENV2022_zcCMfI")]
translated = [f for f in files if f.startswith("MSDS_APHYS_H926_HT-GBENV2022_zcCMfI")]

print("Исходный:", originals)
print("Перевод:", translated)

if not originals or not translated:
    print("Не найдены оба файла!")
    sys.exit(1)

orig_path = os.path.join(output_dir, originals[0])
trans_path = os.path.join(output_dir, translated[0])

orig_doc = fitz.open(orig_path)
trans_doc = fitz.open(trans_path)

print(f"\n=== ИСХОДНЫЙ PDF: {len(orig_doc)} страниц ===")
print(f"=== ПЕРЕВОД: {len(trans_doc)} страниц ===")

# Сравниваем постранично
for page_num in range(min(len(orig_doc), len(trans_doc))):
    print(f"\n{'='*60}")
    print(f"СТРАНИЦА {page_num + 1}")
    print(f"{'='*60}")
    
    orig_page = orig_doc[page_num]
    trans_page = trans_doc[page_num]
    
    # Анализ исходной страницы
    orig_dict = orig_page.get_text("dict")
    orig_blocks = [b for b in orig_dict["blocks"] if b["type"] == 0]
    orig_images = [b for b in orig_dict["blocks"] if b["type"] == 1]
    
    # Анализ переведённой страницы  
    trans_dict = trans_page.get_text("dict")
    trans_blocks = [b for b in trans_dict["blocks"] if b["type"] == 0]
    trans_images = [b for b in trans_dict["blocks"] if b["type"] == 1]
    
    print(f"\n  ИСХОДНИК: {len(orig_blocks)} текстовых блоков, {len(orig_images)} изображений")
    print(f"  ПЕРЕВОД: {len(trans_blocks)} текстовых блоков, {len(trans_images)} изображений")
    
    # Сравниваем текст
    orig_text = orig_page.get_text()
    trans_text = trans_page.get_text()
    
    orig_chars = len(orig_text.strip())
    trans_chars = len(trans_text.strip())
    
    # Считаем кириллицу
    cyrillic = sum(1 for c in trans_text if 'А' <= c <= 'я' or c in 'Ёё')
    
    print(f"  Символов: исходный={orig_chars}, перевод={trans_chars}")
    print(f"  Кириллицы в переводе: {cyrillic}")
    
    # Показываем первые 3 блока для сравнения
    print(f"\n  ПЕРВЫЕ 3 БЛОКА ИСХОДНИКА:")
    for i, block in enumerate(orig_blocks[:3]):
        text = ""
        for line in block["lines"][:2]:
            for span in line["spans"]:
                text += span["text"]
        print(f"    [{i}] bbox={block['bbox']} font={block['lines'][0]['spans'][0]['font'] if block['lines'] else '?'} size={block['lines'][0]['spans'][0]['size'] if block['lines'] else 0:.0f}")
        print(f"        '{text[:80]}'")
    
    print(f"\n  ПЕРВЫЕ 3 БЛОКА ПЕРЕВОДА:")
    for i, block in enumerate(trans_blocks[:3]):
        text = ""
        for line in block["lines"][:2]:
            for span in line["spans"]:
                text += span["text"]
        if text.strip():
            print(f"    [{i}] bbox={block['bbox']}")
            print(f"        '{text[:80]}'")
    
    # Ищем таблицы в исходнике
    print(f"\n  ПОИСК ТАБЛИЦ В ИСХОДНИКЕ:")
    # Признаки таблиц: моноширинные шрифты, выровненные блоки
    mono_blocks = []
    for b in orig_blocks:
        for line in b["lines"]:
            for span in line["spans"]:
                font = span["font"].lower()
                if any(f in font for f in ["courier", "mono", "cour", "code"]):
                    mono_blocks.append((span["text"], span["bbox"]))
                    break
    
    if mono_blocks:
        print(f"    Найдено {len(mono_blocks)} блоков с моноширинным шрифтом (вероятно таблица)")
        for text, bbox in mono_blocks[:5]:
            print(f"      '{text[:60]}...' bbox={bbox}")
    else:
        print("    Моноширинные шрифты не найдены")
    
    # Проверяем, сохранились ли изображения
    if orig_images:
        print(f"\n  ИЗОБРАЖЕНИЯ: {len(orig_images)} в исходнике, {len(trans_images)} в переводе")

orig_doc.close()
trans_doc.close()

print("\n\n=== ВЫВОДЫ ===")
print("Сравните блоки выше — обратите внимание на:")
print("1. Количество текстовых блоков (должно быть примерно одинаковым)")
print("2. Наличие кириллицы в переводе")
print("3. Размеры bbox (не должны сильно отличаться)")
print("4. Сохранность изображений")