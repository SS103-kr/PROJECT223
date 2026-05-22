import os
import subprocess
import mss
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QComboBox,
    QCheckBox, QFileDialog, QLineEdit,
    QStatusBar, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from core.capture import ScreenCapture
from core.recorder import ScreenRecorder
from core.hotkeys import HotkeyManager
from ui.region_selector import RegionSelector
from ui.window_picker import WindowPicker
from ui.recording_toolbar import RecordingToolbar
from ui.settings_dialog import SettingsDialog
from utils import file_namer


def _build_monitor_list() -> list:
    """Return list of (label, mss_monitor_dict) tuples."""
    result = []
    with mss.mss() as sct:
        monitors = sct.monitors  # [0]=all, [1..n]=individual
        for i, m in enumerate(monitors[1:], start=1):
            label = f"모니터 {i}  ({m['width']}x{m['height']})"
            result.append((label, dict(m)))
        if len(monitors) > 2:
            # Multiple physical monitors: add "전체" option at the end
            all_m = dict(monitors[0])
            result.append(("전체 (모두)", all_m))
    return result


class MainWindow(QMainWindow):
    def __init__(self, config, hotkeys: HotkeyManager):
        super().__init__()
        self._config = config
        self._hotkeys = hotkeys
        self._capture = ScreenCapture()
        self._recorder = ScreenRecorder()
        self._region_selector = RegionSelector()
        self._recording_toolbar = RecordingToolbar()
        self._last_saved = ""
        self._screenshot_mode = "full"  # full / region / window
        self._record_mode = "full"      # full / region

        self._monitor_list = _build_monitor_list()  # [(label, mss_dict), ...]

        self._recorder.recording_stopped.connect(self._on_recording_done)

        self._recording_toolbar.stop_requested.connect(self._on_record_toggle)

        self._region_selector.region_selected.connect(self._on_region_selected_screenshot)
        self._region_selector.cancelled.connect(lambda: None)

        self._hotkeys.hotkey_triggered.connect(self._dispatch_hotkey)

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(500)
        self._elapsed_timer.timeout.connect(self._update_timer)

        self._setup_ui()
        self._position_toolbar()

    def _setup_ui(self):
        self.setWindowTitle("CapturePy")
        self.setFixedWidth(400)
        self.setMinimumHeight(480)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Title bar area
        title_row = QHBoxLayout()
        title_lbl = QLabel("CapturePy")
        title_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #89b4fa;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        settings_btn = QPushButton("⚙ 설정")
        settings_btn.setFixedSize(70, 28)
        settings_btn.clicked.connect(self._open_settings)
        title_row.addWidget(settings_btn)
        root.addLayout(title_row)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_screenshot_tab(), "📷 스크린샷")
        tabs.addTab(self._build_record_tab(), "🎥 녹화")
        root.addWidget(tabs)

        # Recent file
        self._recent_group = QGroupBox("최근 저장")
        recent_layout = QHBoxLayout(self._recent_group)
        self._recent_label = QLabel("없음")
        self._recent_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self._recent_label.setWordWrap(True)
        recent_layout.addWidget(self._recent_label, 1)
        open_btn = QPushButton("열기")
        open_btn.setFixedSize(50, 26)
        open_btn.clicked.connect(self._open_last_file)
        folder_btn = QPushButton("폴더")
        folder_btn.setFixedSize(50, 26)
        folder_btn.clicked.connect(self._show_in_folder)
        recent_layout.addWidget(open_btn)
        recent_layout.addWidget(folder_btn)
        root.addWidget(self._recent_group)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("준비")

    def _build_screenshot_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        mode_row = QHBoxLayout()
        self._ss_full_btn = QPushButton("전체화면")
        self._ss_full_btn.setCheckable(True)
        self._ss_full_btn.setChecked(True)
        self._ss_region_btn = QPushButton("영역선택")
        self._ss_region_btn.setCheckable(True)
        self._ss_window_btn = QPushButton("창캡처")
        self._ss_window_btn.setCheckable(True)
        for btn in (self._ss_full_btn, self._ss_region_btn, self._ss_window_btn):
            mode_row.addWidget(btn)
        layout.addLayout(mode_row)

        self._ss_full_btn.clicked.connect(lambda: self._set_ss_mode("full"))
        self._ss_region_btn.clicked.connect(lambda: self._set_ss_mode("region"))
        self._ss_window_btn.clicked.connect(lambda: self._set_ss_mode("window"))

        # Monitor selector row (only for full-screen mode)
        mon_row = QHBoxLayout()
        mon_row.addWidget(QLabel("모니터:"))
        self._ss_monitor_combo = QComboBox()
        for label, _ in self._monitor_list:
            self._ss_monitor_combo.addItem(label)
        # Default: first monitor (or "전체" if multiple)
        self._ss_monitor_combo.setCurrentIndex(0)
        mon_row.addWidget(self._ss_monitor_combo, 1)
        layout.addLayout(mon_row)

        # Format row
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("형식:"))
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["PNG", "JPEG"])
        self._fmt_combo.setCurrentText(self._config.get("output.screenshot_format") or "PNG")
        self._fmt_combo.setFixedWidth(80)
        fmt_row.addWidget(self._fmt_combo)
        fmt_row.addStretch()

        fmt_row.addWidget(QLabel("저장 폴더:"))
        self._ss_dir_edit = QLineEdit(self._config.get("output.directory") or "")
        self._ss_dir_edit.setReadOnly(True)
        self._ss_dir_edit.setFixedWidth(120)
        browse = QPushButton("...")
        browse.setFixedSize(28, 26)
        browse.clicked.connect(lambda: self._browse_dir(self._ss_dir_edit))
        fmt_row.addWidget(self._ss_dir_edit)
        fmt_row.addWidget(browse)
        layout.addLayout(fmt_row)

        # Hotkey hint
        hk = self._config.get("hotkeys.screenshot_full") or "Ctrl+Shift+F"
        self._ss_btn = QPushButton(f"스크린샷 찍기  [{hk.upper()}]")
        self._ss_btn.setObjectName("btn_screenshot")
        self._ss_btn.setMinimumHeight(44)
        self._ss_btn.clicked.connect(self._on_screenshot_action)
        layout.addWidget(self._ss_btn)
        layout.addStretch()
        return w

    def _build_record_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        mode_row = QHBoxLayout()
        self._rec_full_btn = QPushButton("전체화면")
        self._rec_full_btn.setCheckable(True)
        self._rec_full_btn.setChecked(True)
        self._rec_region_btn = QPushButton("영역선택")
        self._rec_region_btn.setCheckable(True)
        for btn in (self._rec_full_btn, self._rec_region_btn):
            mode_row.addWidget(btn)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        self._rec_full_btn.clicked.connect(lambda: self._set_rec_mode("full"))
        self._rec_region_btn.clicked.connect(lambda: self._set_rec_mode("region"))

        # Monitor selector
        rec_mon_row = QHBoxLayout()
        rec_mon_row.addWidget(QLabel("모니터:"))
        self._rec_monitor_combo = QComboBox()
        for label, _ in self._monitor_list:
            self._rec_monitor_combo.addItem(label)
        self._rec_monitor_combo.setCurrentIndex(0)
        rec_mon_row.addWidget(self._rec_monitor_combo, 1)
        layout.addLayout(rec_mon_row)

        # FPS + save dir
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("FPS:"))
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["15", "30", "60"])
        self._fps_combo.setCurrentText(str(self._config.get("output.fps") or 30))
        self._fps_combo.setFixedWidth(60)
        opt_row.addWidget(self._fps_combo)
        opt_row.addSpacing(10)
        opt_row.addWidget(QLabel("저장 폴더:"))
        self._rec_dir_edit = QLineEdit(self._config.get("output.directory") or "")
        self._rec_dir_edit.setReadOnly(True)
        browse2 = QPushButton("...")
        browse2.setFixedSize(28, 26)
        browse2.clicked.connect(lambda: self._browse_dir(self._rec_dir_edit))
        opt_row.addWidget(self._rec_dir_edit)
        opt_row.addWidget(browse2)
        layout.addLayout(opt_row)

        # Audio options
        audio_row = QHBoxLayout()
        self._mic_check = QCheckBox("마이크")
        self._mic_check.setChecked(bool(self._config.get("audio.mic_enabled")))
        self._sys_check = QCheckBox("시스템 소리")
        self._sys_check.setChecked(bool(self._config.get("audio.system_enabled")))
        audio_row.addWidget(QLabel("오디오:"))
        audio_row.addWidget(self._mic_check)
        audio_row.addWidget(self._sys_check)
        audio_row.addStretch()
        layout.addLayout(audio_row)

        # Record button
        hk = self._config.get("hotkeys.record_toggle") or "Ctrl+Shift+V"
        self._rec_btn = QPushButton(f"녹화 시작  [{hk.upper()}]")
        self._rec_btn.setObjectName("btn_record")
        self._rec_btn.setMinimumHeight(44)
        self._rec_btn.clicked.connect(self._on_record_toggle)
        layout.addWidget(self._rec_btn)

        self._timer_label = QLabel("00:00")
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._timer_label.setStyleSheet("color: #f38ba8; font-size: 22px; font-family: 'Consolas';")
        self._timer_label.hide()
        layout.addWidget(self._timer_label)
        layout.addStretch()
        return w

    def _set_ss_mode(self, mode: str):
        self._screenshot_mode = mode
        self._ss_full_btn.setChecked(mode == "full")
        self._ss_region_btn.setChecked(mode == "region")
        self._ss_window_btn.setChecked(mode == "window")

    def _set_rec_mode(self, mode: str):
        self._record_mode = mode
        self._rec_full_btn.setChecked(mode == "full")
        self._rec_region_btn.setChecked(mode == "region")

    def _browse_dir(self, line_edit: QLineEdit):
        d = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", line_edit.text())
        if d:
            line_edit.setText(d)
            self._config.set("output.directory", d)

    # ── Screenshot actions ──────────────────────────────────────────────

    def _on_screenshot_action(self):
        if self._screenshot_mode == "full":
            self._do_screenshot_full()
        elif self._screenshot_mode == "region":
            self._do_screenshot_region()
        else:
            self._do_screenshot_window()

    def _do_screenshot_full(self):
        self.hide()
        from PyQt6.QtCore import QTimer as _QT
        _QT.singleShot(200, self._capture_full_and_show)

    def _capture_full_and_show(self):
        idx = self._ss_monitor_combo.currentIndex()
        _, monitor = self._monitor_list[idx]
        img = self._capture.capture_region(
            monitor["left"], monitor["top"], monitor["width"], monitor["height"]
        )
        self._save_screenshot(img)
        self.show()

    def _do_screenshot_region(self):
        self.hide()
        from PyQt6.QtCore import QTimer as _QT
        self._region_selector.region_selected.disconnect()
        self._region_selector.region_selected.connect(self._on_region_selected_screenshot)
        _QT.singleShot(150, self._region_selector.show_fullscreen)

    def _on_region_selected_screenshot(self, x, y, w, h):
        img = self._capture.capture_region(x, y, w, h)
        self._save_screenshot(img)
        self.show()

    def _do_screenshot_window(self):
        picker = WindowPicker(self)
        picker.window_selected.connect(self._on_window_selected_screenshot)
        picker.exec()

    def _on_window_selected_screenshot(self, hwnd: int):
        self.hide()
        from PyQt6.QtCore import QTimer as _QT
        _QT.singleShot(300, lambda: self._capture_window_and_show(hwnd))

    def _capture_window_and_show(self, hwnd: int):
        img = self._capture.capture_window(hwnd)
        if img:
            self._save_screenshot(img)
        self.show()

    def _save_screenshot(self, img):
        if img is None:
            self._status_bar.showMessage("캡처 실패")
            return
        directory = self._ss_dir_edit.text() or self._config.get("output.directory") or ""
        os.makedirs(directory, exist_ok=True)
        fmt = self._fmt_combo.currentText()
        quality = self._config.get("output.jpeg_quality") or 95
        path = file_namer.screenshot_name(directory, fmt)
        self._capture.save_image(img, path, fmt, quality)
        self._set_recent(path)
        self._status_bar.showMessage(f"저장됨: {os.path.basename(path)}")

    # ── Recording actions ───────────────────────────────────────────────

    @pyqtSlot()
    def _on_record_toggle(self):
        if self._recorder.is_recording():
            self._stop_recording()
        else:
            if self._record_mode == "region":
                self._region_selector.region_selected.disconnect()
                self._region_selector.region_selected.connect(self._on_region_selected_record)
                self._region_selector.show_fullscreen()
            else:
                self._start_recording_full()

    def _on_region_selected_record(self, x, y, w, h):
        region = {"left": x, "top": y, "width": w, "height": h}
        self._start_recording(region)

    def _start_recording_full(self):
        idx = self._rec_monitor_combo.currentIndex()
        _, m = self._monitor_list[idx]
        region = {"left": m["left"], "top": m["top"], "width": m["width"], "height": m["height"]}
        self._start_recording(region)

    def _start_recording(self, region: dict):
        directory = self._rec_dir_edit.text() or self._config.get("output.directory") or ""
        os.makedirs(directory, exist_ok=True)
        fps = int(self._fps_combo.currentText())
        audio_config = {
            "mic_enabled": self._mic_check.isChecked(),
            "system_enabled": self._sys_check.isChecked(),
            "mic_device": self._config.get("audio.mic_device"),
            "system_device": self._config.get("audio.system_device"),
        }
        self._recorder.start(region, fps, directory, audio_config)
        self._rec_btn.setText("녹화 중지")
        self._rec_btn.setObjectName("btn_stop_record")
        self._rec_btn.setStyle(self._rec_btn.style())
        self._timer_label.show()
        self._elapsed_timer.start()
        self._position_toolbar()
        self._recording_toolbar.show_toolbar()
        self._status_bar.showMessage("녹화 중...")

    def _stop_recording(self):
        self._elapsed_timer.stop()
        self._recorder.stop()
        self._recording_toolbar.hide_toolbar()
        self._timer_label.hide()
        self._timer_label.setText("00:00")
        self._rec_btn.setText(f"녹화 시작  [{(self._config.get('hotkeys.record_toggle') or 'Ctrl+Shift+V').upper()}]")
        self._rec_btn.setObjectName("btn_record")
        self._rec_btn.setStyle(self._rec_btn.style())
        self._status_bar.showMessage("저장 중...")

    @pyqtSlot(str)
    def _on_recording_done(self, path: str):
        if path:
            self._set_recent(path)
            self._status_bar.showMessage(f"저장됨: {os.path.basename(path)}")
        else:
            self._status_bar.showMessage("녹화 저장 실패")

    def _update_timer(self):
        sec = int(self._recorder.elapsed_seconds())
        m, s = divmod(sec, 60)
        self._timer_label.setText(f"{m:02d}:{s:02d}")
        self._recording_toolbar.set_time(sec)

    # ── Utility ─────────────────────────────────────────────────────────

    def _set_recent(self, path: str):
        self._last_saved = path
        self._recent_label.setText(os.path.basename(path))

    def _open_last_file(self):
        if self._last_saved and os.path.exists(self._last_saved):
            os.startfile(self._last_saved)

    def _show_in_folder(self):
        if self._last_saved:
            subprocess.Popen(f'explorer /select,"{self._last_saved}"')

    def _open_settings(self):
        dlg = SettingsDialog(self._config, self)
        if dlg.exec():
            self._hotkeys.unregister_all()
            self._hotkeys.register_all()

    def _position_toolbar(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        tb = self._recording_toolbar
        tb.move(screen.center().x() - tb.width() // 2, screen.bottom() - 80)

    def _dispatch_hotkey(self, action: str):
        if action == "screenshot_full":
            self._set_ss_mode("full")
            self._do_screenshot_full()
        elif action == "screenshot_region":
            self._set_ss_mode("region")
            self._do_screenshot_region()
        elif action == "screenshot_window":
            self._set_ss_mode("window")
            self._do_screenshot_window()
        elif action == "record_toggle":
            self._on_record_toggle()

    def closeEvent(self, event):
        if self._recorder.is_recording():
            self._stop_recording()
        self._hotkeys.unregister_all()
        event.accept()
