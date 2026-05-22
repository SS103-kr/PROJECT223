from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QFont


class RecordingToolbar(QWidget):
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(240, 48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self._dot_label = QLabel("●")
        self._dot_label.setStyleSheet("color: #f38ba8; font-size: 16px;")
        layout.addWidget(self._dot_label)

        self._rec_label = QLabel("REC")
        self._rec_label.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 12px;")
        layout.addWidget(self._rec_label)

        self._time_label = QLabel("00:00")
        self._time_label.setStyleSheet("color: #cdd6f4; font-size: 13px; font-family: 'Consolas';")
        self._time_label.setMinimumWidth(50)
        layout.addWidget(self._time_label)

        layout.addStretch()

        btn_stop = QPushButton("■ 정지")
        btn_stop.setFixedSize(64, 28)
        btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #585b70;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6c7086; }
        """)
        btn_stop.clicked.connect(self.stop_requested)
        layout.addWidget(btn_stop)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_visible = True

        self._drag_pos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(30, 30, 46, 220))
        painter.setPen(QColor(69, 71, 90))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

    def set_time(self, seconds: int):
        m, s = divmod(seconds, 60)
        self._time_label.setText(f"{m:02d}:{s:02d}")

    def show_toolbar(self):
        self._blink_timer.start(500)
        self.show()
        self.raise_()

    def hide_toolbar(self):
        self._blink_timer.stop()
        self.hide()

    def _blink(self):
        self._blink_visible = not self._blink_visible
        self._dot_label.setVisible(self._blink_visible)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
