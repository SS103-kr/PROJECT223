import win32gui
import win32con
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt


def _enum_windows():
    results = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if not title or title.strip() == "":
            return True
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if not (style & win32con.WS_CAPTION):
            return True
        rect = win32gui.GetWindowRect(hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w < 10 or h < 10:
            return True
        results.append((hwnd, title))
        return True

    win32gui.EnumWindows(callback, None)
    return results


class WindowPicker(QDialog):
    window_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("캡처할 창 선택")
        self.setMinimumSize(420, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("캡처할 창을 선택하세요:"))

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._accept_selection)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._windows = []
        self._populate()

    def _populate(self):
        self._list.clear()
        self._windows = _enum_windows()
        for hwnd, title in self._windows:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, hwnd)
            self._list.addItem(item)

    def _accept_selection(self):
        item = self._list.currentItem()
        if item is None:
            return
        hwnd = item.data(Qt.ItemDataRole.UserRole)
        self.window_selected.emit(hwnd)
        self.accept()
