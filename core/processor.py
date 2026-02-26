"""
Ядро обработки изображений:
  - Ресайз / кроп фото
  - Наложение текстовой таблички (левый нижний угол)
  - Наложение вотермарки (правый нижний угол)
  - Пакетная обработка + автосортировка по папкам
"""
import os
import shutil
from typing import Callable, List, Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.config import Config
from core.data_manager import get_point_number

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp")


# ──────────────────────────────────────────────────────────
#  Утилиты
# ──────────────────────────────────────────────────────────

def list_images(folder: str) -> List[str]:
    """Отсортированный список файлов-изображений в папке."""
    if not os.path.isdir(folder):
        return []
    return sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(IMAGE_EXTS)
    )


def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Загружает шрифт; при отсутствии — пробует fallback-варианты."""
    candidates = [
        name,
        "arial.ttf",
        "Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def build_lines(template: List[str], row: Dict) -> List[str]:
    """Подставляет значения из строки данных в шаблон."""
    cleaned: Dict[str, str] = {}
    for k, v in row.items():
        val = str(v).strip() if v is not None else ""
        key = k.strip()
        if key == "дата":
            val = val.replace(".", "-")
        elif key in ("широта", "долгота") and val:
            try:
                val = f"{float(val):.5f}"
            except ValueError:
                pass
        cleaned[key] = val

    result = []
    for tpl in template:
        try:
            result.append(tpl.format(**cleaned))
        except (KeyError, ValueError):
            result.append(tpl)
    return result


def build_output_name(template: str, row: Dict) -> str:
    """Формирует имя выходного файла из шаблона."""
    cleaned = {k.strip(): str(v).strip() if v is not None else ""
               for k, v in row.items()}
    try:
        return template.format(**cleaned)
    except (KeyError, ValueError):
        return "output.jpg"


def resize_image(img: Image.Image, width: int, height: int, mode: str) -> Image.Image:
    """
    Приводит изображение к заданному размеру.

    mode:
      crop        — обрезка по центру (по умолчанию)
      fit         — вписать в размер, заполнить чёрным
      stretch     — растянуть без сохранения пропорций
      shrink_only — только уменьшать (не увеличивать)
    """
    orig_w, orig_h = img.size
    img = img.convert("RGBA")

    if mode == "stretch":
        return img.resize((width, height), Image.Resampling.LANCZOS)

    if mode == "shrink_only":
        if orig_w <= width and orig_h <= height:
            return img
        mode = "fit"  # уменьшаем как fit

    if mode == "fit":
        ratio  = min(width / orig_w, height / orig_h)
        new_w  = int(orig_w * ratio)
        new_h  = int(orig_h * ratio)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas  = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        paste_x = (width  - new_w) // 2
        paste_y = (height - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y))
        return canvas

    # crop (center crop)
    ratio  = max(width / orig_w, height / orig_h)
    new_w  = int(orig_w * ratio)
    new_h  = int(orig_h * ratio)
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left   = (new_w - width)  // 2
    top    = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


# ──────────────────────────────────────────────────────────
#  Processor
# ──────────────────────────────────────────────────────────

class Processor:
    """Наложение таблички и вотермарки на одно изображение / пакет."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._font_cache: Dict[int, ImageFont.FreeTypeFont] = {}
        self._wm_cache:   Dict[tuple, Image.Image]         = {}

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            self._font_cache[size] = get_font(self.cfg["font_name"], size)
        return self._font_cache[size]

    # ------------------------------------------------------------------
    def process_one(
        self, image_path: str, row: Dict
    ) -> Tuple[Image.Image, str]:
        """
        Обрабатывает одно фото.
        Возвращает (PIL Image RGBA, имя выходного файла).
        """
        c = self.cfg

        img = Image.open(image_path).convert("RGBA")

        # ---- 1. Ресайз / кроп ----
        if c["resize_enabled"]:
            img = resize_image(
                img,
                int(c["resize_width"]),
                int(c["resize_height"]),
                c["resize_mode"],
            )

        W, H = img.size
        scale = (H / c["scale_base"]) * c["scale_multiplier"]

        font_sz  = max(8, int(c["font_size"]  * scale))
        margin_l = int(c["margin_left"]       * scale)
        margin_b = int(c["margin_bottom"]     * scale)
        pad      = int(c["box_padding"]       * scale)
        spacing  = int(c["line_spacing"]      * scale)
        extra_w  = int(c["box_extra_width"]   * scale)

        font      = self._font(font_sz)
        text_rgba = tuple(c["text_color"])
        box_rgb   = tuple(c["box_color"][:3])
        box_rgba  = (*box_rgb, c["box_opacity"])

        lines = build_lines(c["line_template"], row)

        # ---- 2. Размеры текстового блока ----
        line_heights: List[int] = []
        max_w = 0
        for ln in lines:
            bb  = font.getbbox(ln)
            lh  = bb[3] - bb[1]
            lw  = font.getlength(ln)
            line_heights.append(lh)
            if lw > max_w:
                max_w = lw

        text_w = int(max_w)
        text_h = int(sum(line_heights) + spacing * max(0, len(lines) - 1))
        box_w  = text_w + 2 * pad + extra_w
        box_h  = text_h + 2 * pad

        bx = margin_l
        by = H - box_h - margin_b

        # ---- 3. Текстовый слой ----
        txt_layer = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        draw_t    = ImageDraw.Draw(txt_layer)
        cy        = pad - int(3 * scale)
        for i, ln in enumerate(lines):
            draw_t.text((pad, cy), ln, font=font, fill=text_rgba)
            cy += line_heights[i] + spacing

        squash = c["text_squash_y"]
        if squash != 1.0:
            new_h = int(box_h * squash)
            if new_h > 0:
                txt_layer = txt_layer.transform(
                    (box_w, new_h), Image.AFFINE,
                    (1, 0, 0, 0, 1 / squash, 0),
                    resample=Image.BICUBIC,
                )

        # ---- 4. Оверлей с подложкой ----
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        drw     = ImageDraw.Draw(overlay)
        drw.rectangle([bx, by, bx + box_w, by + box_h], fill=box_rgba)
        overlay.paste(txt_layer, (bx, by), txt_layer)

        # ---- 5. Вотермарка ----
        if c.get("wm_enabled", True):
            wm_path = c["watermark_path"]
            if os.path.isfile(wm_path):
                cache_key = (wm_path, W)
                if cache_key not in self._wm_cache:
                    wm    = Image.open(wm_path).convert("RGBA")
                    wm_w  = int(W * c["wm_ratio"])
                    wm_h  = int(wm.height * (wm_w / wm.width))
                    self._wm_cache[cache_key] = wm.resize(
                        (wm_w, wm_h), Image.Resampling.LANCZOS
                    )
                wm    = self._wm_cache[cache_key]
                wm_w, wm_h = wm.size
                wx    = W - wm_w - c["wm_margin_x"]
                wy    = H - wm_h - c["wm_margin_y"]
                overlay.paste(wm, (wx, wy), wm)

        combined = Image.alpha_composite(img, overlay)
        name     = build_output_name(c["output_name_template"], row)
        return combined, name

    # ------------------------------------------------------------------
    def process_batch(
        self,
        rows: List[Dict],
        *,
        on_log:      Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int]:
        """
        Пакетная обработка фото.
        rows — список словарей (один на фото, по порядку сортировки файлов).
        Возвращает (успешно, ошибок).
        """
        c = self.cfg
        output_dir = c["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        files  = list_images(c["photo_dir"])
        total  = min(len(files), len(rows))

        ok   = 0
        fail = 0
        output_files: List[Tuple[str, Dict]] = []

        for i in range(total):
            try:
                img_path = os.path.join(c["photo_dir"], files[i])
                result, name = self.process_one(img_path, rows[i])
                out_path = os.path.join(output_dir, name)
                result.convert("RGB").save(
                    out_path, "JPEG", quality=c["jpeg_quality"]
                )
                ok += 1
                output_files.append((out_path, rows[i]))
                if on_log:
                    on_log(f"✅  {name}")
            except Exception as e:
                fail += 1
                if on_log:
                    on_log(f"❌  Строка {i + 1}: {e}")

            if on_progress:
                on_progress(i + 1, total)

        # ---- Автосортировка ----
        sort_mode = c.get("sort_mode", "none")
        if sort_mode != "none" and output_files:
            self._sort_output(output_files, sort_mode, output_dir, on_log)

        return ok, fail

    # ------------------------------------------------------------------
    def _sort_output(
        self,
        output_files: List[Tuple[str, Dict]],
        sort_mode: str,
        output_dir: str,
        on_log: Optional[Callable[[str], None]],
    ):
        """Раскладывает готовые файлы по подпапкам."""
        for out_path, row in output_files:
            if not os.path.isfile(out_path):
                continue

            folder_name: Optional[str] = None

            if sort_mode == "points":
                vydel = row.get("выдел", "")
                point_num = get_point_number(vydel)
                if point_num is not None:
                    folder_name = f"Точка {point_num}"

            elif sort_mode == "quarter":
                quarter = row.get("квартал", "").strip()
                if quarter:
                    folder_name = f"кв {quarter}"

            if folder_name:
                target_dir  = os.path.join(output_dir, folder_name)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, os.path.basename(out_path))
                try:
                    shutil.move(out_path, target_path)
                    if on_log:
                        on_log(f"   └─ → {folder_name}/")
                except Exception as e:
                    if on_log:
                        on_log(f"   └─ ⚠️ Сортировка: {e}")
