import os
import tempfile
from datetime import datetime


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def screenshot_name(directory: str, fmt: str) -> str:
    ext = fmt.lower()
    return os.path.join(directory, f"screenshot_{_timestamp()}.{ext}")


def recording_name(directory: str) -> str:
    return os.path.join(directory, f"recording_{_timestamp()}.mp4")


def temp_video_name() -> str:
    fd, path = tempfile.mkstemp(suffix="_capturepyv.mp4")
    os.close(fd)
    return path


def temp_audio_name() -> str:
    fd, path = tempfile.mkstemp(suffix="_capturepya.wav")
    os.close(fd)
    return path
