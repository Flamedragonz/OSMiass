"""
Тёмная тема оформления приложения (Catppuccin Mocha).
"""

STYLESHEET = """
/* ══════════════════════════════════════════════════════
   БАЗОВЫЕ ВИДЖЕТЫ
══════════════════════════════════════════════════════ */

QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QMainWindow {
    background-color: #1e1e2e;
}

/* ══════════════════════════════════════════════════════
   ВКЛАДКИ
══════════════════════════════════════════════════════ */

QTabWidget::pane {
    border: 1px solid #45475a;
    background-color: #1e1e2e;
    border-radius: 0px 6px 6px 6px;
    top: -1px;
}

QTabBar {
    background-color: transparent;
}

QTabBar::tab {
    background-color: #27273a;
    color: #a6adc8;
    padding: 9px 22px;
    margin-right: 3px;
    border: 1px solid #45475a;
    border-bottom: none;
    border-radius: 6px 6px 0px 0px;
    font-weight: 500;
    min-width: 90px;
}

QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #89b4fa;
    border-color: #45475a;
    border-bottom: 1px solid #1e1e2e;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #313244;
    color: #cdd6f4;
}

/* ══════════════════════════════════════════════════════
   КНОПКИ
══════════════════════════════════════════════════════ */

QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
    color: #cdd6f4;
}

QPushButton:pressed {
    background-color: #181825;
    border-color: #74c7ec;
}

QPushButton:disabled {
    background-color: #27273a;
    color: #6c7086;
    border-color: #313244;
}

/* Главная кнопка — синяя */
QPushButton#btn_primary {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
    font-size: 11pt;
}

QPushButton#btn_primary:hover {
    background-color: #74c7ec;
}

QPushButton#btn_primary:pressed {
    background-color: #7287fd;
}

QPushButton#btn_primary:disabled {
    background-color: #45475a;
    color: #6c7086;
}

/* Зелёная кнопка */
QPushButton#btn_success {
    background-color: #a6e3a1;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}

QPushButton#btn_success:hover {
    background-color: #94e2d5;
}

/* ══════════════════════════════════════════════════════
   ПОЛЯ ВВОДА
══════════════════════════════════════════════════════ */

QLineEdit {
    background-color: #27273a;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #cdd6f4;
    selection-background-color: #45475a;
    min-height: 26px;
}

QLineEdit:focus {
    border-color: #89b4fa;
    background-color: #2a2a3e;
}

QLineEdit:disabled {
    background-color: #1e1e2e;
    color: #6c7086;
    border-color: #313244;
}

/* ══════════════════════════════════════════════════════
   СПИНБОКСЫ
══════════════════════════════════════════════════════ */

QSpinBox, QDoubleSpinBox {
    background-color: #27273a;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
    color: #cdd6f4;
    min-height: 26px;
    min-width: 64px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #89b4fa;
}

QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #1e1e2e;
    color: #6c7086;
    border-color: #313244;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #313244;
    border: none;
    width: 18px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #45475a;
}

/* ══════════════════════════════════════════════════════
   КОМБОБОКС
══════════════════════════════════════════════════════ */

QComboBox {
    background-color: #27273a;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #cdd6f4;
    min-height: 26px;
    min-width: 120px;
}

QComboBox:focus {
    border-color: #89b4fa;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right;
    width: 24px;
    border: none;
    background-color: #313244;
    border-radius: 0 6px 6px 0;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #a6adc8;
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: #27273a;
    color: #cdd6f4;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    outline: none;
}

/* ══════════════════════════════════════════════════════
   НАДПИСИ
══════════════════════════════════════════════════════ */

QLabel {
    color: #cdd6f4;
    background: transparent;
}

QLabel#lbl_muted {
    color: #6c7086;
    font-size: 9pt;
}

QLabel#lbl_section {
    color: #cba6f7;
    font-size: 12pt;
    font-weight: bold;
}

QLabel#lbl_status_ok {
    color: #a6e3a1;
    font-weight: bold;
}

QLabel#lbl_status_warn {
    color: #f9e2af;
    font-weight: bold;
}

QLabel#lbl_status_err {
    color: #f38ba8;
    font-weight: bold;
}

/* ══════════════════════════════════════════════════════
   ТАБЛИЦА
══════════════════════════════════════════════════════ */

QTableWidget {
    background-color: #181825;
    color: #cdd6f4;
    gridline-color: #313244;
    selection-background-color: #313244;
    selection-color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    alternate-background-color: #1e1e2e;
    outline: none;
}

QTableWidget::item {
    padding: 5px 8px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #45475a;
    color: #cdd6f4;
}

QTableWidget::item:hover {
    background-color: #2a2a3e;
}

QHeaderView::section {
    background-color: #27273a;
    color: #89b4fa;
    padding: 7px 8px;
    border: none;
    border-right: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
    font-weight: bold;
    font-size: 9pt;
}

QHeaderView::section:first {
    border-radius: 6px 0 0 0;
}

QHeaderView::section:last {
    border-right: none;
    border-radius: 0 6px 0 0;
}

/* ══════════════════════════════════════════════════════
   ПОЛОСЫ ПРОКРУТКИ
══════════════════════════════════════════════════════ */

QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 10px;
    border: none;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6c7086;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 10px;
    border: none;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #6c7086;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ══════════════════════════════════════════════════════
   ПРОГРЕСС-БАР
══════════════════════════════════════════════════════ */

QProgressBar {
    background-color: #27273a;
    border: 1px solid #45475a;
    border-radius: 8px;
    text-align: center;
    color: #cdd6f4;
    min-height: 22px;
    font-weight: bold;
    font-size: 9pt;
}

QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 7px;
}

/* ══════════════════════════════════════════════════════
   ГРУППЫ
══════════════════════════════════════════════════════ */

QGroupBox {
    font-weight: bold;
    color: #cba6f7;
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 6px;
    padding-left: 6px;
    padding-right: 6px;
    padding-bottom: 6px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #cba6f7;
}

/* ══════════════════════════════════════════════════════
   ТЕКСТОВЫЙ РЕДАКТОР (ЛОГ)
══════════════════════════════════════════════════════ */

QTextEdit, QPlainTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    selection-background-color: #45475a;
}

/* ══════════════════════════════════════════════════════
   ЧЕКБОКС / РАДИОКНОПКА
══════════════════════════════════════════════════════ */

QRadioButton {
    color: #cdd6f4;
    spacing: 8px;
    font-size: 10pt;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #45475a;
    border-radius: 9px;
    background-color: #27273a;
}

QRadioButton::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QRadioButton::indicator:hover {
    border-color: #89b4fa;
}

QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
    font-size: 10pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #45475a;
    border-radius: 4px;
    background-color: #27273a;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QCheckBox::indicator:hover {
    border-color: #89b4fa;
}

QCheckBox:disabled {
    color: #6c7086;
}

/* ══════════════════════════════════════════════════════
   СЛАЙДЕР
══════════════════════════════════════════════════════ */

QSlider::groove:horizontal {
    background-color: #313244;
    height: 6px;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #89b4fa;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
    border: 2px solid #1e1e2e;
}

QSlider::handle:horizontal:hover {
    background-color: #74c7ec;
}

QSlider::sub-page:horizontal {
    background-color: #89b4fa;
    border-radius: 3px;
}

/* ══════════════════════════════════════════════════════
   СПЛИТТЕР
══════════════════════════════════════════════════════ */

QSplitter::handle:horizontal {
    background-color: #45475a;
    width: 2px;
}

QSplitter::handle:vertical {
    background-color: #45475a;
    height: 2px;
}

/* ══════════════════════════════════════════════════════
   КОНТЕКСТНОЕ МЕНЮ
══════════════════════════════════════════════════════ */

QMenu {
    background-color: #27273a;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 0;
}

QMenu::item {
    padding: 7px 20px;
    border-radius: 3px;
    margin: 1px 4px;
}

QMenu::item:selected {
    background-color: #45475a;
    color: #cdd6f4;
}

QMenu::separator {
    height: 1px;
    background-color: #45475a;
    margin: 4px 8px;
}

/* ══════════════════════════════════════════════════════
   СТАТУС-БАР
══════════════════════════════════════════════════════ */

QStatusBar {
    background-color: #181825;
    color: #6c7086;
    border-top: 1px solid #313244;
    font-size: 9pt;
}

QStatusBar QLabel {
    color: #6c7086;
}

/* ══════════════════════════════════════════════════════
   ОБЛАСТЬ ПРОКРУТКИ
══════════════════════════════════════════════════════ */

QScrollArea {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #181825;
}

QScrollArea > QWidget > QWidget {
    background-color: #181825;
}

/* ══════════════════════════════════════════════════════
   ДИАЛОГИ
══════════════════════════════════════════════════════ */

QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

QMessageBox {
    background-color: #1e1e2e;
}

QMessageBox QLabel {
    color: #cdd6f4;
}

/* Панель левого сайдбара */
QWidget#left_panel {
    background-color: #181825;
    border-right: 1px solid #313244;
}
"""
