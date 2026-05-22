import cv2
import numpy as np


class VideoWriter:
    def __init__(self):
        self._writer = None

    def open(self, path: str, fps: int, width: int, height: int):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(path, fourcc, fps, (width, height))

    def write_frame(self, bgra_array: np.ndarray):
        if self._writer is None:
            return
        bgr = cv2.cvtColor(bgra_array, cv2.COLOR_BGRA2BGR)
        self._writer.write(bgr)

    def close(self):
        if self._writer is not None:
            self._writer.release()
            self._writer = None

    def is_open(self) -> bool:
        return self._writer is not None
