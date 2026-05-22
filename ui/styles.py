DARK_THEME = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #1e1e2e;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton:checked {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: 1px solid #89b4fa;
}
QPushButton#btn_screenshot {
    background-color: #a6e3a1;
    color: #1e1e2e;
    font-weight: bold;
    font-size: 14px;
    padding: 10px;
    border: none;
    border-radius: 8px;
}
QPushButton#btn_screenshot:hover {
    background-color: #94e2a0;
}
QPushButton#btn_record {
    background-color: #f38ba8;
    color: #1e1e2e;
    font-weight: bold;
    font-size: 14px;
    padding: 10px;
    border: none;
    border-radius: 8px;
}
QPushButton#btn_record:hover {
    background-color: #eb6f92;
}
QPushButton#btn_stop_record {
    background-color: #585b70;
    color: #cdd6f4;
    font-weight: bold;
    font-size: 14px;
    padding: 10px;
    border: none;
    border-radius: 8px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    border-radius: 6px;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #313244;
    color: #a6adc8;
    padding: 8px 20px;
    border-radius: 4px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    selection-background-color: #45475a;
    color: #cdd6f4;
}
QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QCheckBox {
    color: #cdd6f4;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #45475a;
    border-radius: 3px;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QLabel {
    color: #cdd6f4;
}
QLabel#label_section {
    color: #89b4fa;
    font-weight: bold;
    font-size: 12px;
}
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    font-size: 12px;
}
QSlider::groove:horizontal {
    height: 4px;
    background-color: #45475a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background-color: #89b4fa;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QListWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 5px;
    color: #cdd6f4;
}
QListWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QDialog {
    background-color: #1e1e2e;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    color: #89b4fa;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
"""
