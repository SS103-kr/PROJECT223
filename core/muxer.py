import os
import shutil
import subprocess

_TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")


def find_ffmpeg() -> str | None:
    bundled = os.path.join(_TOOLS_DIR, "ffmpeg.exe")
    if os.path.isfile(bundled):
        return bundled
    return shutil.which("ffmpeg")


def is_available() -> bool:
    return find_ffmpeg() is not None


def mux(video_path: str, audio_path: str, output_path: str) -> bool:
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        return False
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0
    except Exception:
        return False


def mux_video_only(video_path: str, output_path: str) -> bool:
    try:
        shutil.move(video_path, output_path)
        return True
    except Exception:
        return False
