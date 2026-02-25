"""
Вкладка «Настройки» — внешний вид таблички, вотермарка,
параметры вывода, умолчания генерации.
"""
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QSlider, QTextEdit, QCheckBox, QColorDialog,
    QFileDialog, QScrollArea, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.config import Config, DEFAULTS


# ──────────────────────────────────────────────────────────
#  Вспомогательный виджет: кнопка выбора цвета
# ──────────────────────────────────────────────────────────

class ColorButton(QPushButton):
    color_changed = pyqtSignal(list)  # [R, G, B]

    def __init__(self, color: list, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_color(color[:3])
        self.clicked.connect(self._pick)

    def set_color(self, rgb: list):
        self._rgb = list(rgb[:3])
        r, g, b = self._rgb
        self.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); "
            f"border: 2px solid #45475a; border-radius: 4px;"
        )

    def get_rgba(self) -> list:
        return self._rgb + [255]

    def get_rgb(self) -> list:
        return list(self._rgb)

    def _pick(self):
        r, g, b = self._rgb
        c = QColorDialog.getColor(QColor(r, g, b), self, "Выбрать цвет")
        if c.isValid():
            self.set_color([c.red(), c.green(), c.blue()])
            self.color_changed.emit(self._rgb)


# ──────────────────────────────────────────────────────────
#  Вкладка
# ──────────────────────────────────────────────────────────

class SettingsTab(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self._setup_ui()
        self._load()

    # ──────────────────────────────────────────────────────────
    #  Построение UI
    # ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        root = QVBoxLayout(content)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Двухколоночный макет
        cols_row = QWidget()
        cr_layout = QHBoxLayout(cols_row)
        cr_layout.setContentsMargins(0, 0, 0, 0)
        cr_layout.setSpacing(12)

        left  = QVBoxLayout()
        right = QVBoxLayout()

        left.addWidget(self._make_overlay_group())
        left.addWidget(self._make_template_group())
        left.addStretch()

        right.addWidget(self._make_watermark_group())
        right.addWidget(self._make_output_group())
        right.addWidget(self._make_defaults_group())
        right.addStretch()

        cr_layout.addLayout(left, 1)
        cr_layout.addLayout(right, 1)
        root.addWidget(cols_row)

        # Кнопки сохранить / сбросить
        btns = QWidget()
        bl   = QHBoxLayout(btns)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)

        self.btn_save  = QPushButton("💾  Сохранить настройки")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.setMinimumHeight(36)
        self.btn_save.clicked.connect(self._save)

        self.btn_reset = QPushButton("Сбросить к умолчаниям")
        self.btn_reset.clicked.connect(self._reset)

        bl.addStretch()
        bl.addWidget(self.btn_reset)
        bl.addWidget(self.btn_save)
        root.addWidget(btns)

    # ─── Группы настроек ────────────────────────────────────

    def _make_overlay_group(self) -> QGroupBox:
        g  = QGroupBox("Внешний вид таблички")
        gl = QGridLayout(g)
        gl.setSpacing(8)
        gl.setColumnMinimumWidth(0, 185)

        r = 0

        gl.addWidget(QLabel("Размер шрифта (базовый):"), r, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        gl.addWidget(self.font_size, r, 1)
        r += 1

        gl.addWidget(QLabel("Файл шрифта (.ttf):"), r, 0)
        self.font_name = QLineEdit()
        self.font_name.setPlaceholderText("arial.ttf")
        gl.addWidget(self.font_name, r, 1)
        r += 1

        gl.addWidget(QLabel("Цвет текста:"), r, 0)
        self.text_color_btn = ColorButton([0, 0, 0])
        gl.addWidget(self.text_color_btn, r, 1)
        r += 1

        gl.addWidget(QLabel("Цвет фона таблички:"), r, 0)
        self.box_color_btn = ColorButton([255, 255, 255])
        gl.addWidget(self.box_color_btn, r, 1)
        r += 1

        gl.addWidget(QLabel("Прозрачность фона (0–255):"), r, 0)
        op_w  = QWidget()
        op_l  = QHBoxLayout(op_w)
        op_l.setContentsMargins(0, 0, 0, 0)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_lbl = QLabel("128")
        self.opacity_lbl.setFixedWidth(32)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_lbl.setText(str(v))
        )
        op_l.addWidget(self.opacity_slider)
        op_l.addWidget(self.opacity_lbl)
        gl.addWidget(op_w, r, 1)
        r += 1

        gl.addWidget(QLabel("Отступ слева (пкс):"), r, 0)
        self.margin_left = QSpinBox()
        self.margin_left.setRange(0, 200)
        gl.addWidget(self.margin_left, r, 1)
        r += 1

        gl.addWidget(QLabel("Отступ снизу (пкс):"), r, 0)
        self.margin_bottom = QSpinBox()
        self.margin_bottom.setRange(0, 200)
        gl.addWidget(self.margin_bottom, r, 1)
        r += 1

        gl.addWidget(QLabel("Внутренний отступ (пкс):"), r, 0)
        self.box_padding = QSpinBox()
        self.box_padding.setRange(0, 60)
        gl.addWidget(self.box_padding, r, 1)
        r += 1

        gl.addWidget(QLabel("Расширение рамки (пкс):"), r, 0)
        self.box_extra = QSpinBox()
        self.box_extra.setRange(0, 100)
        gl.addWidget(self.box_extra, r, 1)
        r += 1

        gl.addWidget(QLabel("Межстрочный интервал (пкс):"), r, 0)
        self.line_spacing = QSpinBox()
        self.line_spacing.setRange(0, 40)
        gl.addWidget(self.line_spacing, r, 1)
        r += 1

        gl.addWidget(QLabel("Сжатие текста по Y:"), r, 0)
        self.squash = QDoubleSpinBox()
        self.squash.setRange(0.5, 2.0)
        self.squash.setSingleStep(0.005)
        self.squash.setDecimals(3)
        gl.addWidget(self.squash, r, 1)
        r += 1

        gl.addWidget(QLabel("Масштаб-база (высота):"), r, 0)
        self.scale_base = QSpinBox()
        self.scale_base.setRange(100, 5000)
        gl.addWidget(self.scale_base, r, 1)
        r += 1

        gl.addWidget(QLabel("Множитель масштаба:"), r, 0)
        self.scale_mult = QDoubleSpinBox()
        self.scale_mult.setRange(0.1, 5.0)
        self.scale_mult.setSingleStep(0.05)
        self.scale_mult.setDecimals(2)
        gl.addWidget(self.scale_mult, r, 1)

        return g

    def _make_template_group(self) -> QGroupBox:
        g  = QGroupBox("Шаблон текста таблички")
        gl = QVBoxLayout(g)

        hint = QLabel(
            "Каждая строка = одна строка на фотографии.\n"
            "Доступные поля:  {квартал}  {выдел}  {дата}  "
            "{время}  {точность}  {широта}  {долгота}"
        )
        hint.setObjectName("lbl_muted")
        hint.setWordWrap(True)
        gl.addWidget(hint)

        self.template_edit = QTextEdit()
        self.template_edit.setMinimumHeight(110)
        self.template_edit.setMaximumHeight(150)
        gl.addWidget(self.template_edit)

        nm_w = QWidget()
        nm_l = QHBoxLayout(nm_w)
        nm_l.setContentsMargins(0, 0, 0, 0)
        nm_l.addWidget(QLabel("Шаблон имени файла:"))
        self.name_template = QLineEdit()
        self.name_template.setPlaceholderText(
            "кв {квартал} выдел {выдел}.jpg"
        )
        nm_l.addWidget(self.name_template, 1)
        gl.addWidget(nm_w)

        return g

    def _make_watermark_group(self) -> QGroupBox:
        g  = QGroupBox("Водяной знак")
        gl = QGridLayout(g)
        gl.setSpacing(8)
        gl.setColumnMinimumWidth(0, 165)

        r = 0

        self.wm_enabled = QCheckBox("Включить водяной знак")
        gl.addWidget(self.wm_enabled, r, 0, 1, 2)
        r += 1

        gl.addWidget(QLabel("Файл (PNG с прозрачностью):"), r, 0)
        wf_w = QWidget()
        wf_l = QHBoxLayout(wf_w)
        wf_l.setContentsMargins(0, 0, 0, 0)
        self.wm_path = QLineEdit()
        btn_wm = QPushButton("…")
        btn_wm.setFixedWidth(32)
        btn_wm.clicked.connect(self._browse_wm)
        wf_l.addWidget(self.wm_path, 1)
        wf_l.addWidget(btn_wm)
        gl.addWidget(wf_w, r, 1)
        r += 1

        gl.addWidget(QLabel("Ширина (доля от ширины фото):"), r, 0)
        self.wm_ratio = QDoubleSpinBox()
        self.wm_ratio.setRange(0.01, 0.95)
        self.wm_ratio.setSingleStep(0.01)
        self.wm_ratio.setDecimals(2)
        gl.addWidget(self.wm_ratio, r, 1)
        r += 1

        gl.addWidget(QLabel("Отступ по X (пкс):"), r, 0)
        self.wm_margin_x = QSpinBox()
        self.wm_margin_x.setRange(0, 300)
        gl.addWidget(self.wm_margin_x, r, 1)
        r += 1

        gl.addWidget(QLabel("Отступ по Y (пкс, < 0 — вверх):"), r, 0)
        self.wm_margin_y = QSpinBox()
        self.wm_margin_y.setRange(-300, 300)
        gl.addWidget(self.wm_margin_y, r, 1)

        return g

    def _make_output_group(self) -> QGroupBox:
        g  = QGroupBox("Параметры вывода")
        gl = QGridLayout(g)
        gl.setSpacing(8)
        gl.setColumnMinimumWidth(0, 165)

        gl.addWidget(QLabel("Качество JPEG (1–100):"), 0, 0)
        self.jpeg_quality = QSpinBox()
        self.jpeg_quality.setRange(1, 100)
        gl.addWidget(self.jpeg_quality, 0, 1)

        return g

    def _make_defaults_group(self) -> QGroupBox:
        g  = QGroupBox("Умолчания генерации данных")
        gl = QGridLayout(g)
        gl.setSpacing(8)
        gl.setColumnMinimumWidth(0, 165)

        gl.addWidget(QLabel("Точность мин. (м):"), 0, 0)
        self.accuracy_min = QDoubleSpinBox()
        self.accuracy_min.setRange(0.1, 100.0)
        self.accuracy_min.setSingleStep(0.1)
        self.accuracy_min.setDecimals(1)
        gl.addWidget(self.accuracy_min, 0, 1)

        gl.addWidget(QLabel("Точность макс. (м):"), 1, 0)
        self.accuracy_max = QDoubleSpinBox()
        self.accuracy_max.setRange(0.1, 100.0)
        self.accuracy_max.setSingleStep(0.1)
        self.accuracy_max.setDecimals(1)
        gl.addWidget(self.accuracy_max, 1, 1)

        return g

    # ──────────────────────────────────────────────────────────
    #  Загрузка / сохранение
    # ──────────────────────────────────────────────────────────

    def _load(self):
        c = self.cfg

        self.font_size.setValue(c.get("font_size", 22))
        self.font_name.setText(c.get("font_name", "arial.ttf"))

        tc = c.get("text_color", [0, 0, 0, 255])
        self.text_color_btn.set_color(tc[:3])
        bc = c.get("box_color", [255, 255, 255])
        self.box_color_btn.set_color(bc[:3] if isinstance(bc, list) else [255, 255, 255])

        self.opacity_slider.setValue(c.get("box_opacity", 128))
        self.margin_left.setValue(c.get("margin_left", 3))
        self.margin_bottom.setValue(c.get("margin_bottom", 4))
        self.box_padding.setValue(c.get("box_padding", 3))
        self.box_extra.setValue(c.get("box_extra_width", 10))
        self.line_spacing.setValue(c.get("line_spacing", 6))
        self.squash.setValue(c.get("text_squash_y", 1.025))
        self.scale_base.setValue(c.get("scale_base", 1000))
        self.scale_mult.setValue(c.get("scale_multiplier", 1.35))

        tpl = c.get("line_template", [])
        self.template_edit.setPlainText("\n".join(tpl))
        self.name_template.setText(
            c.get("output_name_template", "кв {квартал} выдел {выдел}.jpg")
        )

        self.wm_enabled.setChecked(c.get("wm_enabled", True))
        self.wm_path.setText(c.get("watermark_path", "watermark/watermark.png"))
        self.wm_ratio.setValue(c.get("wm_ratio", 0.21))
        self.wm_margin_x.setValue(c.get("wm_margin_x", 20))
        self.wm_margin_y.setValue(c.get("wm_margin_y", -4))

        self.jpeg_quality.setValue(c.get("jpeg_quality", 95))

        self.accuracy_min.setValue(c.get("accuracy_min", 1.3))
        self.accuracy_max.setValue(c.get("accuracy_max", 14.7))

    def _save(self):
        c = self.cfg

        c["font_size"]        = self.font_size.value()
        c["font_name"]        = self.font_name.text().strip()
        c["text_color"]       = self.text_color_btn.get_rgba()
        c["box_color"]        = self.box_color_btn.get_rgb()
        c["box_opacity"]      = self.opacity_slider.value()
        c["margin_left"]      = self.margin_left.value()
        c["margin_bottom"]    = self.margin_bottom.value()
        c["box_padding"]      = self.box_padding.value()
        c["box_extra_width"]  = self.box_extra.value()
        c["line_spacing"]     = self.line_spacing.value()
        c["text_squash_y"]    = self.squash.value()
        c["scale_base"]       = self.scale_base.value()
        c["scale_multiplier"] = self.scale_mult.value()

        tpl = [
            ln for ln in
            self.template_edit.toPlainText().splitlines()
            if ln.strip()
        ]
        c["line_template"]         = tpl
        c["output_name_template"]  = self.name_template.text().strip()

        c["wm_enabled"]   = self.wm_enabled.isChecked()
        c["watermark_path"] = self.wm_path.text().strip()
        c["wm_ratio"]     = self.wm_ratio.value()
        c["wm_margin_x"]  = self.wm_margin_x.value()
        c["wm_margin_y"]  = self.wm_margin_y.value()

        c["jpeg_quality"]  = self.jpeg_quality.value()
        c["accuracy_min"]  = self.accuracy_min.value()
        c["accuracy_max"]  = self.accuracy_max.value()

        c.save()
        self.settings_changed.emit()

    def _reset(self):
        self.cfg.reset_to_defaults()
        self._load()
        self.settings_changed.emit()

    def _browse_wm(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл вотермарки",
            os.path.dirname(self.wm_path.text()),
            "Изображения (*.png *.jpg *.jpeg);;Все файлы (*.*)",
        )
        if path:
            self.wm_path.setText(path)
