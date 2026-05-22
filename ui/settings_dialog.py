import sounddevice as sd
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox,
    QLabel, QKeySequenceEdit, QPushButton, QComboBox,
    QSpinBox, QDialogButtonBox, QFileDialog, QLineEdit,
    QCheckBox, QGridLayout,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence


_ACTIONS = [
    ("screenshot_full", "전체화면 스크린샷"),
    ("screenshot_region", "영역 선택 스크린샷"),
    ("screenshot_window", "창 캡처"),
    ("record_toggle", "녹화 시작/정지"),
]


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("설정")
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        # Hotkeys
        hk_group = QGroupBox("단축키")
        hk_layout = QGridLayout(hk_group)
        self._hk_edits = {}
        for row, (action, label) in enumerate(_ACTIONS):
            combo = config.get(f"hotkeys.{action}") or ""
            lbl = QLabel(label)
            edit = QKeySequenceEdit(QKeySequence(combo.replace("+", "+")))
            self._hk_edits[action] = edit
            hk_layout.addWidget(lbl, row, 0)
            hk_layout.addWidget(edit, row, 1)
        layout.addWidget(hk_group)

        # Output
        out_group = QGroupBox("출력 설정")
        out_layout = QGridLayout(out_group)

        out_layout.addWidget(QLabel("저장 폴더:"), 0, 0)
        self._dir_edit = QLineEdit(config.get("output.directory") or "")
        browse_btn = QPushButton("찾기")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_dir)
        out_layout.addWidget(self._dir_edit, 0, 1)
        out_layout.addWidget(browse_btn, 0, 2)

        out_layout.addWidget(QLabel("스크린샷 형식:"), 1, 0)
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["PNG", "JPEG"])
        self._fmt_combo.setCurrentText(config.get("output.screenshot_format") or "PNG")
        out_layout.addWidget(self._fmt_combo, 1, 1)

        out_layout.addWidget(QLabel("JPEG 품질:"), 2, 0)
        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(1, 100)
        self._quality_spin.setValue(config.get("output.jpeg_quality") or 95)
        out_layout.addWidget(self._quality_spin, 2, 1)

        out_layout.addWidget(QLabel("녹화 FPS:"), 3, 0)
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["15", "30", "60"])
        self._fps_combo.setCurrentText(str(config.get("output.fps") or 30))
        out_layout.addWidget(self._fps_combo, 3, 1)

        layout.addWidget(out_group)

        # Audio
        audio_group = QGroupBox("오디오 설정")
        audio_layout = QGridLayout(audio_group)

        input_devices = [d for d in sd.query_devices() if d["max_input_channels"] > 0]
        output_devices = [d for d in sd.query_devices() if d["max_output_channels"] > 0]

        self._mic_check = QCheckBox("마이크 녹음")
        self._mic_check.setChecked(bool(config.get("audio.mic_enabled")))
        audio_layout.addWidget(self._mic_check, 0, 0)

        self._mic_combo = QComboBox()
        self._mic_combo.addItem("기본 장치", -1)
        for i, d in enumerate(input_devices):
            self._mic_combo.addItem(d["name"], i)
        audio_layout.addWidget(self._mic_combo, 0, 1)

        self._sys_check = QCheckBox("시스템 소리 녹음")
        self._sys_check.setChecked(bool(config.get("audio.system_enabled")))
        audio_layout.addWidget(self._sys_check, 1, 0)

        self._sys_combo = QComboBox()
        self._sys_combo.addItem("기본 출력 장치", -1)
        for i, d in enumerate(output_devices):
            self._sys_combo.addItem(d["name"], i)
        audio_layout.addWidget(self._sys_combo, 1, 1)

        layout.addWidget(audio_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", self._dir_edit.text())
        if d:
            self._dir_edit.setText(d)

    def _save_and_accept(self):
        for action, _ in _ACTIONS:
            seq = self._hk_edits[action].keySequence().toString()
            if seq:
                self._config.set(f"hotkeys.{action}", seq.lower())

        self._config.set("output.directory", self._dir_edit.text())
        self._config.set("output.screenshot_format", self._fmt_combo.currentText())
        self._config.set("output.jpeg_quality", self._quality_spin.value())
        self._config.set("output.fps", int(self._fps_combo.currentText()))
        self._config.set("audio.mic_enabled", self._mic_check.isChecked())
        self._config.set("audio.system_enabled", self._sys_check.isChecked())
        self._config.set("audio.mic_device", self._mic_combo.currentData())
        self._config.set("audio.system_device", self._sys_combo.currentData())

        self.accept()
