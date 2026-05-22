import ctypes
import ctypes.wintypes

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


def _physical_cursor_pos() -> tuple:
    """Return cursor position in physical screen pixels (bypasses Qt DPI scaling)."""
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetPhysicalCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def _all_screens_physical_rect() -> tuple:
    """Return (x, y, w, h) bounding box of all monitors in physical pixels."""
    left = ctypes.windll.user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
    top  = ctypes.windll.user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
    w    = ctypes.windll.user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
    h    = ctypes.windll.user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
    return left, top, w, h


class RegionSelector(QWidget):
    # Emits physical pixel coordinates
    region_selected = pyqtSignal(int, int, int, int)
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Physical pixel tracking (for accurate selection)
        self._start_phys = None
        self._cur_phys = None
        # Logical (widget-local) tracking (for painting only)
        self._start_vis = None
        self._cur_vis = None

    def show_fullscreen(self):
        """Cover the entire virtual desktop (all monitors)."""
        # Use the Windows virtual screen metrics to get physical bounds,
        # then convert to logical coords for Qt geometry.
        px, py, pw, ph = _all_screens_physical_rect()
        dpr = QApplication.primaryScreen().devicePixelRatio()
        lx = int(px / dpr)
        ly = int(py / dpr)
        # Height in logical: use virtualGeometry which correctly spans all monitors
        virtual = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(lx, ly, virtual.width(), virtual.height())
        self._start_phys = None
        self._cur_phys = None
        self._start_vis = None
        self._cur_vis = None
        self.show()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self._start_vis and self._cur_vis:
            sel = QRect(self._start_vis, self._cur_vis).normalized()
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(sel, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            painter.setPen(QPen(QColor(137, 180, 250), 2))
            painter.drawRect(sel)

            if self._start_phys and self._cur_phys:
                x1, y1 = self._start_phys
                x2, y2 = self._cur_phys
                pw, ph = abs(x2 - x1), abs(y2 - y1)
                painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                painter.setPen(QColor(255, 255, 255))
                label = f"{pw} x {ph}"
                lx = sel.left() + 4
                ly = sel.top() - 6
                if ly < 16:
                    ly = sel.bottom() + 16
                painter.drawText(lx, ly, label)

    # ------------------------------------------------------------------
    # Mouse events — physical coords via Win32, logical for visuals
    # ------------------------------------------------------------------

    def mousePressEvent(self, e):
        self._start_phys = _physical_cursor_pos()
        self._cur_phys = self._start_phys
        self._start_vis = e.position().toPoint()
        self._cur_vis = self._start_vis
        self.update()

    def mouseMoveEvent(self, e):
        self._cur_phys = _physical_cursor_pos()
        self._cur_vis = e.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, e):
        self._cur_phys = _physical_cursor_pos()
        self._cur_vis = e.position().toPoint()
        self.hide()

        if self._start_phys is None:
            self.cancelled.emit()
            return

        x1, y1 = self._start_phys
        x2, y2 = self._cur_phys
        x, y = min(x1, x2), min(y1, y2)
        w, h = abs(x2 - x1), abs(y2 - y1)

        if w > 5 and h > 5:
            self.region_selected.emit(x, y, w, h)
        else:
            self.cancelled.emit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
            self.cancelled.emit()
