"""
Главное окно приложения — QMainWindow с пятью вкладками.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QStatusBar, QLabel,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.config import Config
from ui.data_tab     import DataTab
from ui.photo_tab    import PhotoTab
from ui.process_tab  import ProcessTab
from ui.settings_tab import SettingsTab
from ui.map_tab      import MapTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = Config()

        self.setWindowTitle("GPS Photo Overlay  v3.0")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(0)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        layout.addWidget(self.tabs)

        # Создаём вкладки
        self.data_tab     = DataTab(self.cfg)
        self.photo_tab    = PhotoTab(self.cfg)
        self.process_tab  = ProcessTab(self.cfg, self.data_tab, self.photo_tab)
        self.settings_tab = SettingsTab(self.cfg)
        self.map_tab      = MapTab(self.cfg, self.data_tab)

        self.tabs.addTab(self.data_tab,     "  📊 Данные  ")
        self.tabs.addTab(self.photo_tab,    "  📷 Фото  ")
        self.tabs.addTab(self.process_tab,  "  ⚙️ Обработка  ")
        self.tabs.addTab(self.settings_tab, "  🔧 Настройки  ")
        self.tabs.addTab(self.map_tab,      "  🗺️ Карта  ")

        # При переключении вкладок — обновлять нужные
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_lbl = QLabel("Готово  |  GPS Photo Overlay v3.0")
        self.status_bar.addWidget(self.status_lbl)

        # Реагировать на изменения данных и настроек
        self.data_tab.data_changed.connect(self._on_data_changed)
        self.settings_tab.settings_changed.connect(self._on_settings_saved)

    # ──────────────────────────────────────────────────────────

    def _on_tab_changed(self, index: int):
        if index == 2:   # Вкладка «Обработка»
            self.process_tab._refresh_status()
        elif index == 4:  # Вкладка «Карта»
            self.map_tab.refresh()

    def _on_data_changed(self):
        n = self.data_tab.table.rowCount()
        self.status_lbl.setText(f"Строк в таблице: {n}")

    def _on_settings_saved(self):
        self.status_lbl.setText("Настройки сохранены")
        QTimer.singleShot(3000, lambda: self.status_lbl.setText("Готово"))
