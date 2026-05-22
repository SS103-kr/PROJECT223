import keyboard
from PyQt6.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    hotkey_triggered = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._registered = {}

    def register_all(self):
        self.unregister_all()
        actions = {
            "screenshot_full": self._config.get("hotkeys.screenshot_full"),
            "screenshot_region": self._config.get("hotkeys.screenshot_region"),
            "screenshot_window": self._config.get("hotkeys.screenshot_window"),
            "record_toggle": self._config.get("hotkeys.record_toggle"),
        }
        for action, combo in actions.items():
            if combo:
                try:
                    keyboard.add_hotkey(
                        combo,
                        self.hotkey_triggered.emit,
                        args=(action,),
                        suppress=False,
                    )
                    self._registered[action] = combo
                except Exception as e:
                    print(f"[HotkeyManager] 단축키 등록 실패 {action}={combo}: {e}")

    def unregister_all(self):
        try:
            keyboard.clear_all_hotkeys()
        except Exception:
            pass
        self._registered.clear()

    def update(self, action: str, combo: str):
        self.unregister_all()
        self._config.set(f"hotkeys.{action}", combo)
        self.register_all()
