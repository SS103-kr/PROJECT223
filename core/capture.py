import numpy as np
from PIL import Image
import mss
import win32gui


class ScreenCapture:
    def __init__(self):
        self._sct = mss.mss()

    def capture_region(self, x: int, y: int, w: int, h: int) -> Image.Image:
        region = {"left": x, "top": y, "width": w, "height": h}
        raw = self._sct.grab(region)
        arr = np.frombuffer(raw.raw, dtype=np.uint8).reshape(raw.height, raw.width, 4)
        return Image.fromarray(arr[:, :, :3][..., ::-1])

    def capture_window(self, hwnd: int) -> Image.Image:
        try:
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            w, h = x2 - x, y2 - y
            if w <= 0 or h <= 0:
                return None
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        return self.capture_region(x, y, w, h)

    def save_image(self, image: Image.Image, path: str, fmt: str, quality: int = 95):
        if fmt.upper() == "JPEG" or fmt.upper() == "JPG":
            image.save(path, format="JPEG", quality=quality)
        else:
            image.save(path, format="PNG")

    def __del__(self):
        try:
            self._sct.close()
        except Exception:
            pass
