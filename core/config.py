"""
Управление конфигурацией приложения.
Загрузка/сохранение настроек в config.json.
"""
import json
import os

DEFAULTS: dict = {
    # --- Пути ---
    "photo_dir":        "photo",
    "output_dir":       "output",
    "watermark_path":   "watermark/watermark.png",
    "csv_path":         "gps.csv",

    # --- Режим работы ---
    "mode": "lesoseka",          # lesoseka | proseki

    # --- Ресайз фото ---
    "resize_enabled":   True,
    "resize_width":     1280,
    "resize_height":    720,
    "resize_mode":      "crop",  # crop | fit | stretch | shrink_only

    # --- Внешний вид таблички ---
    "font_name":        "arial.ttf",
    "font_size":        22,
    "text_squash_y":    1.025,
    "line_spacing":     6,
    "box_opacity":      128,
    "box_padding":      3,
    "box_extra_width":  10,
    "margin_left":      3,
    "margin_bottom":    4,
    "text_color":       [0, 0, 0, 255],
    "box_color":        [255, 255, 255],
    "scale_base":       1000,
    "scale_multiplier": 1.35,

    # --- Водяной знак ---
    "wm_enabled":       True,
    "wm_ratio":         0.21,
    "wm_margin_x":      20,
    "wm_margin_y":      -4,

    # --- Вывод ---
    "jpeg_quality":             95,
    "output_name_template":     "кв {квартал} выдел {выдел}.jpg",
    "sort_mode":                "points",  # points | quarter | none

    # --- Шаблон строк ---
    "line_template": [
        "Широта: {широта}",
        "Долгота: {долгота}",
        "Точность: {точность} м",
        "Время: {дата} {время}",
    ],

    # --- Генерация данных ---
    "interval_min":  5,
    "interval_max":  7,
    "accuracy_min":  1.3,
    "accuracy_max":  14.7,
}


class Config:
    """Загрузка / сохранение настроек в JSON-файл."""

    FILE = "config.json"

    def __init__(self):
        self.d: dict = {k: v for k, v in DEFAULTS.items()}
        self._load()

    # ---------- dict-like доступ ----------
    def __getitem__(self, key: str):
        return self.d[key]

    def __setitem__(self, key: str, value):
        self.d[key] = value

    def get(self, key: str, default=None):
        return self.d.get(key, default)

    # ---------- файл ----------
    def _load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.d.update(saved)
            except Exception:
                pass

    def save(self):
        try:
            with open(self.FILE, "w", encoding="utf-8") as f:
                json.dump(self.d, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] Ошибка сохранения: {e}")

    def reset_to_defaults(self):
        self.d = {k: v for k, v in DEFAULTS.items()}
        self.save()
