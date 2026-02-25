#!/usr/bin/env python3
"""
GPS Photo Overlay v3.0
Точка входа приложения.
"""
import sys
import os

# Убеждаемся, что рабочий каталог — папка со скриптом
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtGui import QFont
except ImportError:
    print(
        "Ошибка: PyQt6 не установлен.\n"
        "Выполните: pip install PyQt6 Pillow openpyxl"
    )
    sys.exit(1)

from ui.styles      import STYLESHEET
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GPS Photo Overlay")
    app.setApplicationVersion("3.0")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Шрифт по умолчанию
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
