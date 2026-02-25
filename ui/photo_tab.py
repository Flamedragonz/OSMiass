"""
Вкладка «Фото» — выбор папки, настройки ресайза, сетка миниатюр.
"""
import os
from typing import List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QCheckBox, QSpinBox, QComboBox,
    QScrollArea, QGridLayout, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QImage

from core.config import Config
from core.processor import list_images

# Режимы ресайза — отображение → ключ в конфиге
RESIZE_MODES = [
    ("Обрезать по центру (crop)",   "crop"),
    ("Вписать, добавить поля (fit)", "fit"),
    ("Растянуть (stretch)",          "stretch"),
    ("Только уменьшить",             "shrink_only"),
]

THUMB_W = 128
THUMB_H = 96
THUMB_COLS = 6  # максимум столбцов в сетке


class ThumbnailLoader(QThread):
    """Фоновая загрузка миниатюр."""

    thumbnail_ready = pyqtSignal(int, QPixmap, str)   # index, pixmap, tooltip

    def __init__(self, files: List[str], folder: str, parent=None):
        super().__init__(parent)
        self.files  = files
        self.folder = folder
        self._stop  = False

    def stop(self):
        self._stop = True

    def run(self):
        from PIL import Image as PILImage

        for i, filename in enumerate(self.files):
            if self._stop:
                break
            path = os.path.join(self.folder, filename)
            try:
                img = PILImage.open(path)
                orig_w, orig_h = img.size
                img.thumbnail((THUMB_W, THUMB_H), PILImage.Resampling.LANCZOS)
                img = img.convert("RGB")

                data  = img.tobytes("raw", "RGB")
                qimg  = QImage(data, img.width, img.height,
                               QImage.Format.Format_RGB888)
                px    = QPixmap.fromImage(qimg)
                size_kb = os.path.getsize(path) // 1024
                tip   = (f"{filename}\n"
                         f"Оригинал: {orig_w}×{orig_h}  |  {size_kb} KB")
                self.thumbnail_ready.emit(i, px, tip)
            except Exception:
                self.thumbnail_ready.emit(i, QPixmap(), filename)


class PhotoTab(QWidget):
    """Вкладка управления исходными фотографиями."""

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self._cells: dict = {}      # index → cell widget
        self._loader: ThumbnailLoader | None = None
        self._setup_ui()
        self._refresh_photos()

    # ──────────────────────────────────────────────────────────
    #  Построение UI
    # ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- Папка источника ---
        folder_group = QGroupBox("Папка с исходными фото")
        fl = QHBoxLayout(folder_group)

        self.folder_input = QLineEdit(self.cfg.get("photo_dir", "photo"))
        self.btn_browse   = QPushButton("Обзор...")
        self.btn_refresh  = QPushButton("Обновить список")

        self.btn_browse.clicked.connect(self._browse_folder)
        self.btn_refresh.clicked.connect(self._refresh_photos)
        self.folder_input.returnPressed.connect(self._refresh_photos)

        fl.addWidget(self.folder_input, 1)
        fl.addWidget(self.btn_browse)
        fl.addWidget(self.btn_refresh)
        layout.addWidget(folder_group)

        # --- Настройки ресайза ---
        resize_group = QGroupBox("Изменение размера перед наложением таблички")
        rl = QHBoxLayout(resize_group)
        rl.setSpacing(12)

        self.resize_check = QCheckBox("Изменять размер")
        self.resize_check.setChecked(self.cfg.get("resize_enabled", True))
        self.resize_check.toggled.connect(self._on_resize_toggled)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 9999)
        self.width_spin.setValue(self.cfg.get("resize_width", 1280))
        self.width_spin.setFixedWidth(75)

        x_lbl = QLabel("×")
        x_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 9999)
        self.height_spin.setValue(self.cfg.get("resize_height", 720))
        self.height_spin.setFixedWidth(75)

        px_lbl = QLabel("пикселей")

        mode_lbl = QLabel("Режим:")
        self.resize_mode_combo = QComboBox()
        for label, _ in RESIZE_MODES:
            self.resize_mode_combo.addItem(label)
        cur_mode = self.cfg.get("resize_mode", "crop")
        mode_keys = [k for _, k in RESIZE_MODES]
        if cur_mode in mode_keys:
            self.resize_mode_combo.setCurrentIndex(mode_keys.index(cur_mode))

        rl.addWidget(self.resize_check)
        rl.addSpacing(8)
        rl.addWidget(self.width_spin)
        rl.addWidget(x_lbl)
        rl.addWidget(self.height_spin)
        rl.addWidget(px_lbl)
        rl.addSpacing(12)
        rl.addWidget(mode_lbl)
        rl.addWidget(self.resize_mode_combo)
        rl.addStretch()

        layout.addWidget(resize_group)

        # --- Сетка миниатюр ---
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        self.photo_header = QLabel("Фотографии: нет")
        self.photo_header.setObjectName("lbl_section")

        self.btn_save = QPushButton("Сохранить настройки")
        self.btn_save.clicked.connect(self._save_settings)

        hl.addWidget(self.photo_header)
        hl.addStretch()
        hl.addWidget(self.btn_save)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.grid_container = QWidget()
        self.grid_layout    = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll, 1)

        # Начальное состояние спинбоксов
        self._on_resize_toggled(self.resize_check.isChecked())

    # ──────────────────────────────────────────────────────────
    #  Логика
    # ──────────────────────────────────────────────────────────

    def _on_resize_toggled(self, checked: bool):
        for w in [self.width_spin, self.height_spin, self.resize_mode_combo]:
            w.setEnabled(checked)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "Выбрать папку с фото", self.folder_input.text()
        )
        if path:
            self.folder_input.setText(path)
            self._refresh_photos()

    def _refresh_photos(self):
        folder = self.folder_input.text().strip()

        # Остановить предыдущий загрузчик
        if self._loader and self._loader.isRunning():
            self._loader.stop()
            self._loader.wait()

        # Очистить сетку
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()

        files = list_images(folder)

        if not files:
            self.photo_header.setText(
                f"Фотографий не найдено  ({folder})"
            )
            return

        self.photo_header.setText(
            f"Фотографии: {len(files)} файлов  "
            f"(сортировка по имени файла)"
        )

        cols = THUMB_COLS
        for i, filename in enumerate(files):
            cell = self._make_cell(i + 1, filename)
            self.grid_layout.addWidget(cell, i // cols, i % cols)
            self._cells[i] = cell

        # Загрузить миниатюры в фоне
        self._loader = ThumbnailLoader(files, folder, self)
        self._loader.thumbnail_ready.connect(self._on_thumb_ready)
        self._loader.start()

    def _make_cell(self, num: int, filename: str) -> QWidget:
        """Создаёт placeholder-ячейку для одного фото."""
        cell = QWidget()
        cell.setFixedSize(THUMB_W + 10, THUMB_H + 26)

        vl = QVBoxLayout(cell)
        vl.setContentsMargins(3, 3, 3, 3)
        vl.setSpacing(2)

        img_lbl = QLabel(str(num))
        img_lbl.setFixedSize(THUMB_W, THUMB_H)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet(
            "background:#27273a; border-radius:4px; color:#6c7086; font-size:16pt;"
        )

        short = filename if len(filename) <= 18 else filename[:15] + "…"
        name_lbl = QLabel(short)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("font-size:8pt; color:#6c7086;")

        vl.addWidget(img_lbl)
        vl.addWidget(name_lbl)

        # Сохраняем ссылку
        cell._img_lbl  = img_lbl   # type: ignore[attr-defined]
        cell._name_lbl = name_lbl  # type: ignore[attr-defined]
        return cell

    def _on_thumb_ready(self, index: int, pixmap: QPixmap, tooltip: str):
        cell = self._cells.get(index)
        if not cell:
            return
        img_lbl = cell._img_lbl  # type: ignore[attr-defined]
        if not pixmap.isNull():
            img_lbl.setPixmap(
                pixmap.scaled(
                    THUMB_W, THUMB_H,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            img_lbl.setStyleSheet(
                "background:#181825; border-radius:4px;"
            )
        img_lbl.setToolTip(tooltip)

    def _save_settings(self):
        mode_keys = [k for _, k in RESIZE_MODES]
        self.cfg["photo_dir"]       = self.folder_input.text().strip()
        self.cfg["resize_enabled"]  = self.resize_check.isChecked()
        self.cfg["resize_width"]    = self.width_spin.value()
        self.cfg["resize_height"]   = self.height_spin.value()
        self.cfg["resize_mode"]     = mode_keys[self.resize_mode_combo.currentIndex()]
        self.cfg.save()

    # ──────────────────────────────────────────────────────────
    #  Публичный API
    # ──────────────────────────────────────────────────────────

    def get_photo_count(self) -> int:
        return len(list_images(self.folder_input.text().strip()))

    def get_folder(self) -> str:
        return self.folder_input.text().strip()

    def apply_settings_to_config(self):
        """Записывает текущие настройки в конфиг (вызывается перед обработкой)."""
        self._save_settings()
