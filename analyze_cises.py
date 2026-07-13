#!/usr/bin/env python3
"""
Анализ данных ЧЗ: разрывы между эмиссией, нанесением и вводом в оборот.
"""
import csv
import sys
from datetime import datetime, date
from collections import defaultdict, Counter

INPUT_FILE = r"C:\Users\Alexey Shilo\Downloads\chz_cises_проверить.txt"

# Колонки (0-based):
# 0 - cis
# 1 - cis_print_view
# 2 - gtin
# 3 - serial_number
# 4 - status
# 8 - emission_date
# 9 - introduced_date
# 10 - application_date

def parse_dt(s):
    """Парсит дату-время вида '2026-07-09 10:38:29.849 +0300' -> date"""
    if not s or s.strip() == '':
        return None
    s = s.strip()
    try:
        # форматы: "2026-07-09 10:38:29.849 +0300" или "2026-06-02 03:00:00.000 +0300"
        dt = datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        return dt.date()
    except (ValueError, IndexError):
        return None

def days_between(d1, d2):
    """Разница в днях (d2 - d1). Если один из None -> None"""
    if d1 is None or d2 is None:
        return None
    return (d2 - d1).days

def main():
    records = []
    total_lines = 0
    skipped = 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            total_lines += 1
            if len(row) < 12:
                skipped += 1
                continue

            status = row[4].strip() if len(row) > 4 else ''
            em_date = parse_dt(row[8]) if len(row) > 8 else None
            intro_date = parse_dt(row[9]) if len(row) > 9 else None
            app_date = parse_dt(row[10]) if len(row) > 10 else None

            records.append({
                'status': status,
                'cis': row[0].strip() if len(row) > 0 else '',
                'emission_date': em_date,
                'introduced_date': intro_date,
                'application_date': app_date,
            })

    print(f"Всего строк: {total_lines}")
    print(f"Пропущено (мало колонок): {skipped}")
    print(f"Обработано: {len(records)}")
    print()

    # ---- Фильтрация: только те, у кого есть introduced_date (INTRODUCED) ----
    introduced = [r for r in records if r['introduced_date'] is not None]
    print(f"Записей с introduced_date (введены в оборот): {len(introduced)}")

    emitted_with_dates = [r for r in records if r['emission_date'] is not None]
    print(f"Записей с emission_date: {len(emitted_with_dates)}")

    applied_with_dates = [r for r in records if r['application_date'] is not None]
    print(f"Записей с application_date: {len(applied_with_dates)}")
    print()

    # ---- 1. Средний разрыв между этапами ----
    gaps = {
        'emission_to_intro': [],  # emission -> introduced
        'emission_to_app': [],    # emission -> application
        'app_to_intro': [],       # application -> introduced
    }

    for r in introduced:
        if r['emission_date'] and r['introduced_date']:
            d = days_between(r['emission_date'], r['introduced_date'])
            if d is not None and d >= 0:
                gaps['emission_to_intro'].append(d)

        if r['emission_date'] and r['application_date']:
            d = days_between(r['emission_date'], r['application_date'])
            if d is not None and d >= 0:
                gaps['emission_to_app'].append(d)

        if r['application_date'] and r['introduced_date']:
            d = days_between(r['application_date'], r['introduced_date'])
            if d is not None and d >= 0:
                gaps['app_to_intro'].append(d)

    # ---- 2. Статистика ----
    def calc_stats(arr, label):
        if not arr:
            print(f"  {label}: нет данных")
            return
        n = len(arr)
        total = sum(arr)
        avg = total / n
        sorted_arr = sorted(arr)
        median = sorted_arr[n // 2] if n % 2 else (sorted_arr[n//2 - 1] + sorted_arr[n//2]) / 2
        print(f"  {label}:")
        print(f"    Количество: {n}")
        print(f"    Среднее:    {avg:.1f} дн.")
        print(f"    Медиана:    {median:.0f} дн.")
        print(f"    Min:        {min(arr)} дн.")
        print(f"    Max:        {max(arr)} дн.")

    print("=== РАЗРЫВЫ МЕЖДУ ЭТАПАМИ (в днях) ===")
    calc_stats(gaps['emission_to_intro'], 'Эмиссия -> Ввод в оборот')
    print()
    calc_stats(gaps['emission_to_app'], 'Эмиссия -> Нанесение')
    print()
    calc_stats(gaps['app_to_intro'], 'Нанесение -> Ввод в оборот')
    print()

    # ---- 3. Распределение разрывов ----
    def print_distribution(arr, label):
        if not arr:
            return
        bins = [(0, 0), (1, 1), (2, 7), (8, 30), (31, 90), (91, 365), (366, 99999)]
        print(f"  Распределение ({label}):")
        total = len(arr)
        for lo, hi in bins:
            cnt = sum(1 for d in arr if lo <= d <= hi)
            pct = cnt / total * 100
            if lo == hi:
                print(f"    {lo} дн.:          {cnt:>6} ({pct:5.1f}%)")
            elif hi == 99999:
                print(f"    >={lo} дн.:        {cnt:>6} ({pct:5.1f}%)")
            else:
                print(f"    {lo}-{hi} дн.:       {cnt:>6} ({pct:5.1f}%)")

    print("=== РАСПРЕДЕЛЕНИЕ РАЗРЫВОВ ===")
    print_distribution(gaps['emission_to_intro'], 'Эмиссия -> Ввод в оборот')
    print()
    print_distribution(gaps['app_to_intro'], 'Нанесение -> Ввод в оборот')
    print()

    # ---- 4. Совпадение этапов в один день ----
    zero_gap_em_intro = sum(1 for d in gaps['emission_to_intro'] if d == 0)
    zero_gap_app_intro = sum(1 for d in gaps['app_to_intro'] if d == 0)

    print("=== СОВПАДЕНИЕ ЭТАПОВ В ОДИН ДЕНЬ ===")
    print(f"  Эмиссия == Ввод в оборот:     {zero_gap_em_intro} кодов ({zero_gap_em_intro/len(gaps['emission_to_intro'])*100:.1f}% если есть даты)")
    print(f"  Нанесение == Ввод в оборот:   {zero_gap_app_intro} кодов ({zero_gap_app_intro/len(gaps['app_to_intro'])*100:.1f}% если есть даты)")

    # Все три в один день
    three_same = 0
    for r in introduced:
        if r['emission_date'] and r['application_date'] and r['introduced_date']:
            if r['emission_date'] == r['introduced_date'] == r['application_date']:
                three_same += 1
    print(f"  Все три этапа в один день:     {three_same}")
    print()

    # ---- 5. Статистика по дням (календарь) ----
    print("=== СТАТИСТИКА ПО ДНЯМ (ввод в оборот) ===")
    day_stats = defaultdict(lambda: {'total': 0, 'gap_sum_em_intro': 0, 'gap_sum_app_intro': 0,
                                       'gap_cnt_em_intro': 0, 'gap_cnt_app_intro': 0,
                                       'zero_em_intro': 0, 'zero_app_intro': 0})

    for r in introduced:
        intro_d = r['introduced_date']
        if intro_d is None:
            continue
        day_stats[intro_d]['total'] += 1

        if r['emission_date'] and r['introduced_date']:
            d = days_between(r['emission_date'], r['introduced_date'])
            if d is not None and d >= 0:
                day_stats[intro_d]['gap_sum_em_intro'] += d
                day_stats[intro_d]['gap_cnt_em_intro'] += 1
                if d == 0:
                    day_stats[intro_d]['zero_em_intro'] += 1

        if r['application_date'] and r['introduced_date']:
            d = days_between(r['application_date'], r['introduced_date'])
            if d is not None and d >= 0:
                day_stats[intro_d]['gap_sum_app_intro'] += d
                day_stats[intro_d]['gap_cnt_app_intro'] += 1
                if d == 0:
                    day_stats[intro_d]['zero_app_intro'] += 1

    print(f"{'Дата':<14} {'Всего':>7} {'Ср.разрыв(Э->В)':>16} {'Ср.разрыв(Н->В)':>16} {'Э==В':>6} {'Н==В':>6}")
    print("-" * 70)
    for d in sorted(day_stats.keys()):
        s = day_stats[d]
        avg_em = s['gap_sum_em_intro'] / s['gap_cnt_em_intro'] if s['gap_cnt_em_intro'] else None
        avg_app = s['gap_sum_app_intro'] / s['gap_cnt_app_intro'] if s['gap_cnt_app_intro'] else None
        avg_em_str = f"{avg_em:.1f}" if avg_em is not None else "-"
        avg_app_str = f"{avg_app:.1f}" if avg_app is not None else "-"
        print(f"{d.isoformat():<14} {s['total']:>7} {avg_em_str:>16} {avg_app_str:>16} {s['zero_em_intro']:>6} {s['zero_app_intro']:>6}")

    print()

    # ---- 6. Статистика по неделям ----
    print("=== СТАТИСТИКА ПО НЕДЕЛЯМ (ввод в оборот) ===")
    week_stats = defaultdict(lambda: {'total': 0, 'gap_sum_em_intro': 0, 'gap_cnt_em_intro': 0,
                                       'gap_sum_app_intro': 0, 'gap_cnt_app_intro': 0,
                                       'zero_em_intro': 0, 'zero_app_intro': 0})

    for r in introduced:
        intro_d = r['introduced_date']
        if intro_d is None:
            continue
        # начало недели (понедельник)
        week_start = intro_d - __import__('datetime').timedelta(days=intro_d.weekday())
        week_stats[week_start]['total'] += 1

        if r['emission_date'] and r['introduced_date']:
            d = days_between(r['emission_date'], r['introduced_date'])
            if d is not None and d >= 0:
                week_stats[week_start]['gap_sum_em_intro'] += d
                week_stats[week_start]['gap_cnt_em_intro'] += 1
                if d == 0:
                    week_stats[week_start]['zero_em_intro'] += 1

        if r['application_date'] and r['introduced_date']:
            d = days_between(r['application_date'], r['introduced_date'])
            if d is not None and d >= 0:
                week_stats[week_start]['gap_sum_app_intro'] += d
                week_stats[week_start]['gap_cnt_app_intro'] += 1
                if d == 0:
                    week_stats[week_start]['zero_app_intro'] += 1

    print(f"{'Неделя (пн)':<14} {'Всего':>7} {'Ср.разрыв(Э->В)':>16} {'Ср.разрыв(Н->В)':>16} {'Э==В':>6} {'Н==В':>6}")
    print("-" * 70)
    for d in sorted(week_stats.keys()):
        s = week_stats[d]
        avg_em = s['gap_sum_em_intro'] / s['gap_cnt_em_intro'] if s['gap_cnt_em_intro'] else None
        avg_app = s['gap_sum_app_intro'] / s['gap_cnt_app_intro'] if s['gap_cnt_app_intro'] else None
        avg_em_str = f"{avg_em:.1f}" if avg_em is not None else "-"
        avg_app_str = f"{avg_app:.1f}" if avg_app is not None else "-"
        print(f"{d.isoformat():<14} {s['total']:>7} {avg_em_str:>16} {avg_app_str:>16} {s['zero_em_intro']:>6} {s['zero_app_intro']:>6}")

    # ---- 7. Статусная статистика ----
    print()
    print("=== СТАТИСТИКА ПО СТАТУСАМ ===")
    status_counts = Counter(r['status'] for r in records if r['status'])
    for st, cnt in status_counts.most_common():
        print(f"  {st:<30} {cnt:>7}")

if __name__ == '__main__':
    main()
