import json
import os
import tempfile
from pathlib import Path

_DEFAULTS = {
    "hotkeys": {
        "screenshot_full": "ctrl+shift+f",
        "screenshot_region": "ctrl+shift+r",
        "screenshot_window": "ctrl+shift+w",
        "record_toggle": "ctrl+shift+v",
    },
    "output": {
        "directory": str(Path.home() / "Desktop"),
        "screenshot_format": "PNG",
        "jpeg_quality": 95,
        "fps": 30,
    },
    "audio": {
        "mic_enabled": True,
        "system_enabled": True,
        "mic_device": -1,
        "system_device": -1,
    },
}

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class ConfigManager:
    def __init__(self):
        self._data = {}
        self.load()

    def load(self):
        self._data = _deep_merge(_DEFAULTS, {})
        if os.path.exists(_CONFIG_PATH):
            try:
                with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data = _deep_merge(self._data, saved)
            except Exception:
                pass

    def save(self):
        tmp = _CONFIG_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, _CONFIG_PATH)
        except Exception:
            pass

    def get(self, key_path: str):
        parts = key_path.split(".")
        val = self._data
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                return None
        return val

    def set(self, key_path: str, value):
        parts = key_path.split(".")
        d = self._data
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value
        self.save()


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
