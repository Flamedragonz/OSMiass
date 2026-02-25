"""
Вкладка «Обработка» — статус, предпросмотр, запуск обработки,
прогресс и журнал.
"""
import os
import sys
from typing import List, Dict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QProgressBar, QTextEdit, QComboBox,
    QLineEdit, QFileDialog, QDialog, QScrollArea,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QTextCursor

from core.config import Config
from core.processor import Processor, list_images


# ──────────────────────────────────────────────────────────
#  Фоновый поток обработки
# ──────────────────────────────────────────────────────────

class ProcessWorker(QThread):
    log_signal      = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(int, int)

    def __init__(self, cfg: Config, rows: List[Dict], parent=None):
        super().__init__(parent)
        self.cfg  = cfg
        self.rows = rows

    def run(self):
        try:
            proc = Processor(self.cfg)
            ok, fail = proc.process_batch(
                self.rows,
                on_log      = lambda m: self.log_signal.emit(m),
                on_progress = lambda cur, tot: self.progress_signal.emit(cur, tot),
            )
            self.finished_signal.emit(ok, fail)
        except Exception as e:
            self.log_signal.emit(f"❌  Критическая ошибка: {e}")
            self.finished_signal.emit(0, 0)


# ──────────────────────────────────────────────────────────
#  Диалог предпросмотра
# ──────────────────────────────────────────────────────────

class PreviewDialog(QDialog):
    def __init__(self, pixmap: QPixmap, title: str, info: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(lbl)
        layout.addWidget(scroll)

        info_lbl = QLabel(info)
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_lbl.setObjectName("lbl_muted")
        layout.addWidget(info_lbl)

        btn = QPushButton("Закрыть")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)


# ──────────────────────────────────────────────────────────
#  Вкладка
# ──────────────────────────────────────────────────────────

class ProcessTab(QWidget):
    def __init__(self, cfg: Config, data_tab, photo_tab):
        super().__init__()
        self.cfg       = cfg
        self.data_tab  = data_tab
        self.photo_tab = photo_tab
        self._worker: ProcessWorker | None = None
        self._setup_ui()
        QTimer.singleShot(300, self._refresh_status)

    # ──────────────────────────────────────────────────────────
    #  Построение UI
    # ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- Статус ---
        status_group = QGroupBox("Статус")
        sl = QVBoxLayout(status_group)

        row1 = QWidget()
        r1l  = QHBoxLayout(row1)
        r1l.setContentsMargins(0, 0, 0, 0)
        r1l.setSpacing(24)

        self.lbl_data  = QLabel("Данных: —")
        self.lbl_photo = QLabel("Фото: —")
        self.lbl_wm    = QLabel("Вотермарка: —")

        r1l.addWidget(self.lbl_data)
        r1l.addWidget(self.lbl_photo)
        r1l.addWidget(self.lbl_wm)
        r1l.addStretch()
        sl.addWidget(row1)

        self.lbl_match = QLabel("")
        sl.addWidget(self.lbl_match)
        layout.addWidget(status_group)

        # --- Параметры вывода ---
        out_group = QGroupBox("Параметры вывода")
        ol = QHBoxLayout(out_group)
        ol.setSpacing(10)

        ol.addWidget(QLabel("Папка:"))
        self.output_input = QLineEdit(self.cfg.get("output_dir", "output"))
        ol.addWidget(self.output_input, 1)

        self.btn_browse_out = QPushButton("Обзор...")
        self.btn_browse_out.clicked.connect(self._browse_output)
        ol.addWidget(self.btn_browse_out)

        ol.addSpacing(16)
        ol.addWidget(QLabel("Сортировка:"))

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "По точкам  (папки: Точка 1, Точка 2 …)",
            "По кварталам  (папки: кв 16, кв 18 …)",
            "Без сортировки",
        ])
        sort_map = {"points": 0, "quarter": 1, "none": 2}
        self.sort_combo.setCurrentIndex(
            sort_map.get(self.cfg.get("sort_mode", "points"), 0)
        )
        ol.addWidget(self.sort_combo)
        layout.addWidget(out_group)

        # --- Кнопки действий ---
        btn_row = QWidget()
        bl = QHBoxLayout(btn_row)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)

        self.btn_refresh = QPushButton("Обновить статус")
        self.btn_preview = QPushButton("Предпросмотр (1-е фото)")
        self.btn_open    = QPushButton("Открыть папку вывода")
        self.btn_start   = QPushButton("▶▶  ЗАПУСТИТЬ ОБРАБОТКУ")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setMinimumHeight(40)

        self.btn_refresh.clicked.connect(self._refresh_status)
        self.btn_preview.clicked.connect(self._show_preview)
        self.btn_open.clicked.connect(self._open_output_folder)
        self.btn_start.clicked.connect(self._start)

        bl.addWidget(self.btn_refresh)
        bl.addWidget(self.btn_preview)
        bl.addWidget(self.btn_open)
        bl.addStretch()
        bl.addWidget(self.btn_start)
        layout.addWidget(btn_row)

        # --- Прогресс ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m")
        layout.addWidget(self.progress_bar)

        # --- Журнал ---
        log_group = QGroupBox("Журнал")
        ll = QVBoxLayout(log_group)

        log_top = QWidget()
        ltl = QHBoxLayout(log_top)
        ltl.setContentsMargins(0, 0, 0, 0)
        ltl.addStretch()
        self.btn_clear_log = QPushButton("Очистить лог")
        self.btn_clear_log.clicked.connect(lambda: self.log_text.clear())
        ltl.addWidget(self.btn_clear_log)
        ll.addWidget(log_top)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(220)
        ll.addWidget(self.log_text)
        layout.addWidget(log_group)

    # ──────────────────────────────────────────────────────────
    #  Логика
    # ──────────────────────────────────────────────────────────

    def _refresh_status(self):
        rows    = self.data_tab.get_non_empty_rows()
        n_data  = len(rows)
        n_photo = self.photo_tab.get_photo_count()
        wm_path = self.cfg.get("watermark_path", "")
        wm_ok   = os.path.isfile(wm_path)

        self.lbl_data.setText(f"Данных: {n_data} строк")
        self.lbl_photo.setText(f"Фото: {n_photo} файлов")

        if wm_ok:
            self.lbl_wm.setText(f"Вотермарка: ✅ {os.path.basename(wm_path)}")
            self.lbl_wm.setObjectName("lbl_status_ok")
        else:
            self.lbl_wm.setText("Вотермарка: ⚠️ не найдена")
            self.lbl_wm.setObjectName("lbl_status_warn")
        self.lbl_wm.style().unpolish(self.lbl_wm)
        self.lbl_wm.style().polish(self.lbl_wm)

        if n_data == 0 or n_photo == 0:
            self.lbl_match.setText("⚠️  Нет данных или фото для обработки")
            self.lbl_match.setObjectName("lbl_status_warn")
        elif n_data == n_photo:
            self.lbl_match.setText(
                f"✅  Полное совпадение: {n_data} пар  "
                f"(данные ↔ фото)"
            )
            self.lbl_match.setObjectName("lbl_status_ok")
        else:
            will = min(n_data, n_photo)
            self.lbl_match.setText(
                f"⚠️  Несовпадение: данных {n_data}, фото {n_photo}  "
                f"→ будет обработано {will}"
            )
            self.lbl_match.setObjectName("lbl_status_warn")
        self.lbl_match.style().unpolish(self.lbl_match)
        self.lbl_match.style().polish(self.lbl_match)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Папка вывода", self.output_input.text()
        )
        if path:
            self.output_input.setText(path)

    def _open_output_folder(self):
        d = self.output_input.text().strip()
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(d)
        elif sys.platform == "darwin":
            os.system(f'open "{d}"')
        else:
            os.system(f'xdg-open "{d}"')

    def _show_preview(self):
        self._sync_config()
        rows   = self.data_tab.get_non_empty_rows()
        folder = self.photo_tab.get_folder()
        files  = list_images(folder)

        if not files:
            self._log("⚠️  Нет фото для предпросмотра")
            return
        if not rows:
            self._log("⚠️  Нет данных для предпросмотра")
            return

        try:
            from PIL import Image as PILImage
            proc    = Processor(self.cfg)
            result, name = proc.process_one(
                os.path.join(folder, files[0]), rows[0]
            )
            orig_w, orig_h = result.size

            # Масштаб под экран
            max_w, max_h = 1200, 800
            ratio   = min(max_w / orig_w, max_h / orig_h, 1.0)
            new_w   = int(orig_w * ratio)
            new_h   = int(orig_h * ratio)
            preview = result.convert("RGB").resize(
                (new_w, new_h), PILImage.Resampling.LANCZOS
            )

            data  = preview.tobytes("raw", "RGB")
            qimg  = QImage(data, new_w, new_h, QImage.Format.Format_RGB888)
            px    = QPixmap.fromImage(qimg)

            dlg = PreviewDialog(
                px, f"Предпросмотр: {name}",
                f"{name}  |  {orig_w}×{orig_h} пикселей",
                self,
            )
            dlg.exec()
        except Exception as e:
            self._log(f"❌  Ошибка предпросмотра: {e}")

    def _start(self):
        if self._worker and self._worker.isRunning():
            return

        self._sync_config()
        rows = self.data_tab.get_non_empty_rows()

        if not rows:
            self._log("❌  Таблица данных пуста!")
            return

        folder = self.photo_tab.get_folder()
        if not os.path.isdir(folder):
            self._log(f"❌  Папка с фото не найдена: {folder}")
            return

        self.btn_start.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(min(len(rows), len(list_images(folder))))
        self._log("─" * 50)
        self._log("🚀  Запуск обработки…")

        self._worker = ProcessWorker(self.cfg, rows, self)
        self._worker.log_signal.connect(self._log)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def _on_finished(self, ok: int, fail: int):
        self.btn_start.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log("─" * 50)
        self._log(
            f"🏁  Готово!   ✅ Успешно: {ok}   ❌ Ошибок: {fail}"
        )

    def _sync_config(self):
        sort_keys = ["points", "quarter", "none"]
        self.cfg["output_dir"] = self.output_input.text().strip()
        self.cfg["sort_mode"]  = sort_keys[self.sort_combo.currentIndex()]
        self.photo_tab.apply_settings_to_config()
        self.cfg.save()

    def _log(self, message: str):
        self.log_text.append(message)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
