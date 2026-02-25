"""
Управление данными: генерация строк, чтение/запись CSV, импорт Excel.
"""
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

COLUMNS = ["квартал", "выдел", "дата", "время", "точность", "широта", "долгота"]


def generate_rows(
    quarter: str,
    section: str,
    count: int,
    date: str,
    start_time: str,
    interval_min: int,
    interval_max: int,
    accuracy_min: float,
    accuracy_max: float,
) -> List[Dict]:
    """
    Генерирует строки данных для заданного квартала/выдела.

    На каждую точку создаются 2 строки:
      - section_N   (первое фото точки)
      - section_N_  (второе фото точки, та же метка времени)

    Время между точками — случайный интервал [interval_min, interval_max] минут.
    Точность — случайное значение в диапазоне [accuracy_min, accuracy_max].
    """
    rows: List[Dict] = []
    try:
        current_time = datetime.strptime(start_time, "%H:%M")
    except ValueError:
        current_time = datetime.strptime("12:00", "%H:%M")

    for point_num in range(1, count + 1):
        time_str  = current_time.strftime("%H:%M")
        accuracy  = round(random.uniform(accuracy_min, accuracy_max), 1)

        # Первое фото точки
        rows.append({
            "квартал":  quarter,
            "выдел":    f"{section}_{point_num}",
            "дата":     date,
            "время":    time_str,
            "точность": str(accuracy),
            "широта":   "",
            "долгота":  "",
        })

        # Второе фото точки (то же время, суффикс «_»)
        rows.append({
            "квартал":  quarter,
            "выдел":    f"{section}_{point_num}_",
            "дата":     date,
            "время":    time_str,
            "точность": str(accuracy),
            "широта":   "",
            "долгота":  "",
        })

        # Сдвигаем время перед следующей точкой
        if point_num < count:
            interval = random.randint(interval_min, interval_max)
            current_time += timedelta(minutes=interval)

    return rows


def load_csv(path: str) -> List[Dict]:
    """Читает CSV (разделитель «;») и возвращает список словарей."""
    rows: List[Dict] = []
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                normalized: Dict = {}
                for k, v in row.items():
                    if k is not None:
                        key = k.strip()
                        val = (v or "").strip()
                        # Нормализуем дату: точки → дефисы
                        if key == "дата":
                            val = val.replace(".", "-")
                        normalized[key] = val
                rows.append(normalized)
    except FileNotFoundError:
        raise RuntimeError(f"Файл не найден: {path}")
    except Exception as e:
        raise RuntimeError(f"Ошибка чтения CSV: {e}")
    return rows


def save_csv(path: str, rows: List[Dict]):
    """
    Сохраняет строки в CSV (разделитель «;», UTF-8 BOM).
    Дата всегда в формате ДД-ММ-ГГГГ (через дефис).
    """
    if not rows:
        return
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=COLUMNS,
                delimiter=";",
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in rows:
                r = dict(row)
                if "дата" in r and r["дата"]:
                    r["дата"] = r["дата"].replace(".", "-")
                writer.writerow(r)
    except Exception as e:
        raise RuntimeError(f"Ошибка сохранения CSV: {e}")


def load_excel(path: str) -> List[Dict]:
    """Импортирует данные из Excel-файла (.xlsx/.xlsm) через openpyxl."""
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("Установите openpyxl: pip install openpyxl")

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows: List[Dict] = []
        headers: Optional[List[str]] = None

        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = [str(c).strip() if c is not None else f"col{j}"
                           for j, c in enumerate(row)]
                continue
            if all(v is None for v in row):
                continue

            row_dict: Dict = {}
            for j, val in enumerate(row):
                if headers and j < len(headers):
                    key = headers[j]
                    if val is None:
                        row_dict[key] = ""
                    elif isinstance(val, datetime):
                        row_dict[key] = val.strftime("%d-%m-%Y")
                    else:
                        text = str(val).strip()
                        if key == "дата":
                            text = text.replace(".", "-")
                        row_dict[key] = text
            rows.append(row_dict)

        wb.close()
        return rows
    except Exception as e:
        raise RuntimeError(f"Ошибка чтения Excel: {e}")


def get_point_number(vydel: str) -> Optional[int]:
    """
    Извлекает номер точки из строки выдела.
    Примеры:  '72_1' → 1,  '72_1_' → 1,  '29_3' → 3
    """
    if not vydel:
        return None
    # Убираем финальный «_» и разбиваем
    parts = vydel.rstrip("_").split("_")
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None
