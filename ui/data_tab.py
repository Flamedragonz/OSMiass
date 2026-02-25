"""
Вкладка «Данные» — генерация таблицы, редактирование координат,
импорт/экспорт CSV и Excel.
"""
import os
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QLineEdit, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QButtonGroup, QRadioButton, QMenu, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont

from core.config import Config
from core.data_manager import (
    generate_rows, load_csv, save_csv, load_excel, COLUMNS
)


class DataTab(QWidget):
    """Вкладка редактирования данных GPS."""

    data_changed = pyqtSignal()

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self._setup_ui()

    # ──────────────────────────────────────────────────────────
    #  Построение UI
    # ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left  = self._build_left_panel()
        right = self._build_right_panel()

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([310, 800])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ---------- Левая панель ----------

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("left_panel")
        panel.setFixedWidth(310)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 8, 12)
        layout.setSpacing(10)

        # --- Режим работы ---
        mode_group = QGroupBox("Режим работы")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(6)

        self.radio_lesoseka = QRadioButton("Лесосека")
        self.radio_proseki  = QRadioButton("Квартальные просеки")

        btn_grp = QButtonGroup(self)
        btn_grp.addButton(self.radio_lesoseka)
        btn_grp.addButton(self.radio_proseki)

        mode = self.cfg.get("mode", "lesoseka")
        self.radio_lesoseka.setChecked(mode == "lesoseka")
        self.radio_proseki.setChecked(mode == "proseki")
        self.radio_lesoseka.toggled.connect(self._on_mode_changed)

        mode_layout.addWidget(self.radio_lesoseka)
        mode_layout.addWidget(self.radio_proseki)
        layout.addWidget(mode_group)

        # --- Генерация строк ---
        gen_group = QGroupBox("Добавить строки в таблицу")
        gen_layout = QVBoxLayout(gen_group)
        gen_layout.setSpacing(6)

        def field_row(label: str, attr: str, default: str) -> QLineEdit:
            row = QWidget()
            rl  = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label)
            lbl.setFixedWidth(90)
            inp = QLineEdit(default)
            setattr(self, attr, inp)
            rl.addWidget(lbl)
            rl.addWidget(inp)
            gen_layout.addWidget(row)
            return inp

        field_row("Квартал:", "quarter_input", "16")
        field_row("Выдел:",   "section_input", "72")

        # Количество точек
        pts_row = QWidget()
        pts_l   = QHBoxLayout(pts_row)
        pts_l.setContentsMargins(0, 0, 0, 0)
        pts_lbl = QLabel("Точек (пар):")
        pts_lbl.setFixedWidth(90)
        self.points_spin = QSpinBox()
        self.points_spin.setRange(1, 999)
        self.points_spin.setValue(7)
        pts_l.addWidget(pts_lbl)
        pts_l.addWidget(self.points_spin)
        gen_layout.addWidget(pts_row)

        field_row("Дата:", "date_input", "26-11-2025")\
            .setPlaceholderText("ДД-ММ-ГГГГ")
        field_row("Время:", "time_input", "12:22")\
            .setPlaceholderText("ЧЧ:ММ")

        # Интервал
        int_row = QWidget()
        int_l   = QHBoxLayout(int_row)
        int_l.setContentsMargins(0, 0, 0, 0)
        int_lbl = QLabel("Интервал:")
        int_lbl.setFixedWidth(90)
        self.interval_min = QSpinBox()
        self.interval_min.setRange(1, 120)
        self.interval_min.setValue(self.cfg.get("interval_min", 5))
        self.interval_min.setFixedWidth(56)
        dash = QLabel("—")
        dash.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash.setFixedWidth(14)
        self.interval_max = QSpinBox()
        self.interval_max.setRange(1, 120)
        self.interval_max.setValue(self.cfg.get("interval_max", 7))
        self.interval_max.setFixedWidth(56)
        min_lbl = QLabel("мин")
        int_l.addWidget(int_lbl)
        int_l.addWidget(self.interval_min)
        int_l.addWidget(dash)
        int_l.addWidget(self.interval_max)
        int_l.addWidget(min_lbl)
        int_l.addStretch()
        gen_layout.addWidget(int_row)

        self.btn_generate = QPushButton("▶  Добавить строки")
        self.btn_generate.setObjectName("btn_primary")
        self.btn_generate.clicked.connect(self._generate_rows)
        gen_layout.addWidget(self.btn_generate)

        layout.addWidget(gen_group)

        # --- Управление строками ---
        edit_group = QGroupBox("Управление строками")
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setSpacing(5)

        self.btn_add_empty = QPushButton("+ Добавить пустую строку")
        self.btn_delete    = QPushButton("✕  Удалить выбранные")
        self.btn_move_up   = QPushButton("↑  Переместить вверх")
        self.btn_move_down = QPushButton("↓  Переместить вниз")

        self.btn_add_empty.clicked.connect(self._add_empty_row)
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_move_up.clicked.connect(self._move_up)
        self.btn_move_down.clicked.connect(self._move_down)

        for btn in [self.btn_add_empty, self.btn_delete,
                    self.btn_move_up, self.btn_move_down]:
            edit_layout.addWidget(btn)
        layout.addWidget(edit_group)

        # --- Импорт / Экспорт ---
        io_group = QGroupBox("Импорт / Экспорт")
        io_layout = QVBoxLayout(io_group)
        io_layout.setSpacing(5)

        self.btn_import_csv   = QPushButton("Импорт CSV")
        self.btn_import_excel = QPushButton("Импорт Excel (.xlsx/.xlsm)")
        self.btn_export_csv   = QPushButton("Экспорт CSV")
        self.btn_clear        = QPushButton("Очистить таблицу")

        self.btn_import_csv.clicked.connect(self._import_csv)
        self.btn_import_excel.clicked.connect(self._import_excel)
        self.btn_export_csv.clicked.connect(self._export_csv)
        self.btn_clear.clicked.connect(self._clear_table)

        for btn in [self.btn_import_csv, self.btn_import_excel,
                    self.btn_export_csv, self.btn_clear]:
            io_layout.addWidget(btn)
        layout.addWidget(io_group)

        layout.addStretch()
        return panel

    # ---------- Правая панель (таблица) ----------

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 12, 12, 12)
        layout.setSpacing(6)

        # Шапка
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Таблица данных")
        title.setObjectName("lbl_section")
        self.row_count_lbl = QLabel("0 строк")
        self.row_count_lbl.setObjectName("lbl_muted")

        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(self.row_count_lbl)
        layout.addWidget(header)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.itemChanged.connect(lambda _: self._update_row_count())

        # Ширина столбцов
        col_widths = [60, 100, 105, 68, 75, 95, 95]
        for i, w in enumerate(col_widths):
            self.table.setColumnWidth(i, w)

        layout.addWidget(self.table)

        hint = QLabel(
            "Двойной клик — редактирование ячейки.  "
            "ПКМ — контекстное меню.  "
            "Широту и долготу можно вписать вручную."
        )
        hint.setObjectName("lbl_muted")
        layout.addWidget(hint)

        return panel

    # ──────────────────────────────────────────────────────────
    #  Логика
    # ──────────────────────────────────────────────────────────

    def _on_mode_changed(self, checked: bool):
        mode = "lesoseka" if self.radio_lesoseka.isChecked() else "proseki"
        self.cfg["mode"] = mode
        self.cfg.save()

    # --- Генерация ---

    def _generate_rows(self):
        quarter      = self.quarter_input.text().strip()
        section      = self.section_input.text().strip()
        count        = self.points_spin.value()
        date         = self.date_input.text().strip()
        time_str     = self.time_input.text().strip()
        ival_min     = self.interval_min.value()
        ival_max     = self.interval_max.value()

        if not quarter or not section:
            QMessageBox.warning(self, "Ошибка", "Укажите квартал и выдел!")
            return
        if ival_min > ival_max:
            QMessageBox.warning(
                self, "Ошибка",
                "Минимальный интервал не может быть больше максимального!"
            )
            return

        rows = generate_rows(
            quarter=quarter,
            section=section,
            count=count,
            date=date,
            start_time=time_str,
            interval_min=ival_min,
            interval_max=ival_max,
            accuracy_min=self.cfg.get("accuracy_min", 1.3),
            accuracy_max=self.cfg.get("accuracy_max", 14.7),
        )

        self.cfg["interval_min"] = ival_min
        self.cfg["interval_max"] = ival_max
        self.cfg.save()

        for row in rows:
            self._append_row(row)
        self._update_row_count()
        self.data_changed.emit()

    # --- Работа с таблицей ---

    def _append_row(self, row_data: Dict):
        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        self.table.blockSignals(True)
        for col_idx, col_name in enumerate(COLUMNS):
            value = str(row_data.get(col_name, "") or "")
            item  = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_num, col_idx, item)
        self.table.blockSignals(False)

    def _add_empty_row(self):
        row_num = self.table.rowCount()
        self.table.insertRow(row_num)
        for col_idx in range(len(COLUMNS)):
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_num, col_idx, item)
        self._update_row_count()
        self.data_changed.emit()

    def _delete_selected(self):
        selected = sorted(
            {idx.row() for idx in self.table.selectedIndexes()},
            reverse=True,
        )
        for row in selected:
            self.table.removeRow(row)
        self._update_row_count()
        self.data_changed.emit()

    def _move_up(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not rows or rows[0] == 0:
            return
        for row in rows:
            self._swap_rows(row - 1, row)
        # Сдвинуть выделение
        self.table.clearSelection()
        for row in rows:
            self.table.selectRow(row - 1)

    def _move_down(self):
        rows = sorted(
            {idx.row() for idx in self.table.selectedIndexes()},
            reverse=True,
        )
        if not rows or rows[0] >= self.table.rowCount() - 1:
            return
        for row in rows:
            self._swap_rows(row, row + 1)
        self.table.clearSelection()
        for row in rows:
            self.table.selectRow(row + 1)

    def _swap_rows(self, a: int, b: int):
        self.table.blockSignals(True)
        for col in range(self.table.columnCount()):
            item_a = self.table.item(a, col)
            item_b = self.table.item(b, col)
            text_a = item_a.text() if item_a else ""
            text_b = item_b.text() if item_b else ""
            self.table.setItem(a, col, QTableWidgetItem(text_b))
            self.table.setItem(b, col, QTableWidgetItem(text_a))
        self.table.blockSignals(False)

    def _context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction(QAction("Вставить строку выше", self,
                                triggered=self._insert_above))
        menu.addAction(QAction("Вставить строку ниже", self,
                                triggered=self._insert_below))
        menu.addAction(QAction("Дублировать строку", self,
                                triggered=self._duplicate_row))
        menu.addSeparator()
        menu.addAction(QAction("Удалить строку(и)", self,
                                triggered=self._delete_selected))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _insert_above(self):
        row = self.table.currentRow()
        if row < 0:
            row = 0
        self.table.insertRow(row)
        for col in range(len(COLUMNS)):
            self.table.setItem(row, col, QTableWidgetItem(""))
        self._update_row_count()

    def _insert_below(self):
        row = self.table.currentRow()
        if row < 0:
            row = self.table.rowCount() - 1
        self.table.insertRow(row + 1)
        for col in range(len(COLUMNS)):
            self.table.setItem(row + 1, col, QTableWidgetItem(""))
        self._update_row_count()

    def _duplicate_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        new_row = row + 1
        self.table.insertRow(new_row)
        self.table.blockSignals(True)
        for col in range(len(COLUMNS)):
            item = self.table.item(row, col)
            text = item.text() if item else ""
            new_item = QTableWidgetItem(text)
            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(new_row, col, new_item)
        self.table.blockSignals(False)
        self._update_row_count()

    def _clear_table(self):
        reply = QMessageBox.question(
            self, "Очистить таблицу",
            "Удалить все строки? Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)
            self._update_row_count()
            self.data_changed.emit()

    def _update_row_count(self):
        n = self.table.rowCount()
        self.row_count_lbl.setText(f"{n} строк")

    # --- Импорт / Экспорт ---

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть CSV",
            os.path.dirname(self.cfg.get("csv_path", "")),
            "CSV файлы (*.csv);;Все файлы (*.*)",
        )
        if not path:
            return
        try:
            rows = load_csv(path)
            self._load_rows_to_table(rows)
            self.cfg["csv_path"] = path
            self.cfg.save()
        except RuntimeError as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Открыть Excel",
            "",
            "Excel файлы (*.xlsx *.xlsm *.xls);;Все файлы (*.*)",
        )
        if not path:
            return
        try:
            rows = load_excel(path)
            self._load_rows_to_table(rows)
        except RuntimeError as e:
            QMessageBox.critical(self, "Ошибка импорта", str(e))

    def _load_rows_to_table(self, rows: List[Dict]):
        self.table.setRowCount(0)
        for row in rows:
            self._append_row(row)
        self._update_row_count()
        self.data_changed.emit()

    def _export_csv(self):
        default = self.cfg.get("csv_path", "gps.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV",
            default,
            "CSV файлы (*.csv);;Все файлы (*.*)",
        )
        if not path:
            return
        try:
            rows = self.get_rows()
            save_csv(path, rows)
            self.cfg["csv_path"] = path
            self.cfg.save()
            QMessageBox.information(self, "Экспорт", f"✅ Сохранено:\n{path}")
        except RuntimeError as e:
            QMessageBox.critical(self, "Ошибка экспорта", str(e))

    # ──────────────────────────────────────────────────────────
    #  Публичный API
    # ──────────────────────────────────────────────────────────

    def get_rows(self) -> List[Dict]:
        """Возвращает все строки таблицы как список словарей."""
        rows = []
        for row_idx in range(self.table.rowCount()):
            row_data: Dict = {}
            for col_idx, col_name in enumerate(COLUMNS):
                item = self.table.item(row_idx, col_idx)
                row_data[col_name] = item.text().strip() if item else ""
            rows.append(row_data)
        return rows

    def get_non_empty_rows(self) -> List[Dict]:
        """Возвращает только строки, где заполнено хотя бы одно поле."""
        return [r for r in self.get_rows() if any(v for v in r.values())]
