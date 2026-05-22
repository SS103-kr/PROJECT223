import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from utils.config_manager import ConfigManager
from core.hotkeys import HotkeyManager
from ui.main_window import MainWindow
from ui.styles import DARK_THEME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CapturePy")
    app.setOrganizationName("CapturePy")
    app.setStyleSheet(DARK_THEME)

    config = ConfigManager()
    hotkeys = HotkeyManager(config)

    window = MainWindow(config, hotkeys)
    window.show()

    hotkeys.register_all()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
