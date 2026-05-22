import os
import queue
import threading
import time
import wave
import numpy as np
import mss

from PyQt6.QtCore import QObject, pyqtSignal

from core.video_writer import VideoWriter
from core.audio_capture import AudioCapture
from core import audio_mixer
from core import muxer
from utils import file_namer


class ScreenRecorder(QObject):
    recording_stopped = pyqtSignal(str)
    frame_count_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._stop_event = threading.Event()
        self._frame_queue = queue.Queue(maxsize=120)
        self._audio_queue = queue.Queue(maxsize=400)
        self._video_writer = VideoWriter()
        self._audio_capture = AudioCapture()
        self._threads = []
        self._temp_video = None
        self._temp_audio = None
        self._output_dir = None
        self._fps = 30
        self._region = None
        self._audio_config = {}
        self._frame_count = 0
        self._start_time = 0.0
        self._recording = False

    def is_recording(self) -> bool:
        return self._recording

    def elapsed_seconds(self) -> float:
        if not self._recording:
            return 0.0
        return time.perf_counter() - self._start_time

    def start(self, region: dict, fps: int, output_dir: str, audio_config: dict):
        if self._recording:
            return
        self._region = region
        self._fps = fps
        self._output_dir = output_dir
        self._audio_config = audio_config
        self._stop_event.clear()
        self._frame_count = 0

        self._temp_video = file_namer.temp_video_name()
        self._temp_audio = file_namer.temp_audio_name()

        self._video_writer.open(
            self._temp_video, fps, region["width"], region["height"]
        )

        mic_enabled = audio_config.get("mic_enabled", False)
        sys_enabled = audio_config.get("system_enabled", False)
        has_audio = mic_enabled or sys_enabled

        self._threads = []

        capture_t = threading.Thread(target=self._capture_loop, daemon=True)
        encode_t = threading.Thread(target=self._encode_loop, daemon=True)
        self._threads = [capture_t, encode_t]

        if has_audio:
            self._audio_capture.start(
                self._audio_queue,
                mic_device=audio_config.get("mic_device"),
                system_device=audio_config.get("system_device"),
                mic_enabled=mic_enabled,
                system_enabled=sys_enabled,
            )
            audio_t = threading.Thread(target=self._audio_write_loop, daemon=True)
            self._threads.append(audio_t)

        self._start_time = time.perf_counter()
        self._recording = True

        for t in self._threads:
            t.start()

    def stop(self):
        if not self._recording:
            return
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=10)
        self._threads = []

        self._video_writer.close()
        self._audio_capture.stop()
        self._recording = False

        output_path = file_namer.recording_name(self._output_dir)
        has_audio = (
            self._audio_config.get("mic_enabled", False)
            or self._audio_config.get("system_enabled", False)
        )

        success = False
        if has_audio and os.path.exists(self._temp_audio) and os.path.getsize(self._temp_audio) > 44:
            success = muxer.mux(self._temp_video, self._temp_audio, output_path)
        if not success:
            success = muxer.mux_video_only(self._temp_video, output_path)

        for tmp in (self._temp_video, self._temp_audio):
            if tmp and os.path.exists(tmp):
                try:
                    os.unlink(tmp)
                except Exception:
                    pass

        self.recording_stopped.emit(output_path if success else "")

    def _capture_loop(self):
        target_interval = 1.0 / self._fps
        next_frame_time = time.perf_counter()
        sct = mss.mss()
        region = self._region
        last_frame = None

        while not self._stop_event.is_set():
            now = time.perf_counter()
            if now >= next_frame_time:
                try:
                    raw = sct.grab(region)
                    frame = np.frombuffer(raw.raw, dtype=np.uint8).reshape(
                        raw.height, raw.width, 4
                    )
                    last_frame = frame.copy()
                    self._frame_queue.put(last_frame, block=False)
                except queue.Full:
                    pass
                except Exception:
                    pass
                next_frame_time += target_interval
                # 뒤처진 슬롯을 마지막 프레임으로 채워서 재생 속도 유지
                while next_frame_time < time.perf_counter() and last_frame is not None:
                    try:
                        self._frame_queue.put(last_frame, block=False)
                    except queue.Full:
                        break
                    next_frame_time += target_interval
            else:
                remaining = next_frame_time - now
                if remaining > 0.002:
                    time.sleep(remaining - 0.002)
        sct.close()

    def _encode_loop(self):
        while not self._stop_event.is_set() or not self._frame_queue.empty():
            try:
                frame = self._frame_queue.get(timeout=0.1)
                self._video_writer.write_frame(frame)
                self._frame_count += 1
                if self._frame_count % self._fps == 0:
                    self.frame_count_updated.emit(self._frame_count)
            except queue.Empty:
                continue

    def _audio_write_loop(self):
        mic_buf = np.zeros((0, 2), dtype=np.int16)
        sys_buf = np.zeros((0, 2), dtype=np.int16)

        wf = wave.open(self._temp_audio, "wb")
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)

        while not self._stop_event.is_set() or not self._audio_queue.empty():
            try:
                source, data = self._audio_queue.get(timeout=0.05)
                chunk = data.reshape(-1, 2)
                if source == "mic":
                    mic_buf = np.concatenate([mic_buf, chunk])
                else:
                    sys_buf = np.concatenate([sys_buf, chunk])

                # Write when we have enough from at least one source
                min_len = 1024
                mic_has = len(mic_buf) >= min_len
                sys_has = len(sys_buf) >= min_len

                if mic_has or sys_has:
                    if mic_has and sys_has:
                        a, b = audio_mixer.normalize_length(mic_buf, sys_buf)
                        out = audio_mixer.mix(a, b)
                        mic_buf = np.zeros((0, 2), dtype=np.int16)
                        sys_buf = np.zeros((0, 2), dtype=np.int16)
                    elif mic_has:
                        out = mic_buf
                        mic_buf = np.zeros((0, 2), dtype=np.int16)
                    else:
                        out = sys_buf
                        sys_buf = np.zeros((0, 2), dtype=np.int16)
                    wf.writeframes(out.tobytes())
            except queue.Empty:
                continue

        # Flush remaining
        for buf in (mic_buf, sys_buf):
            if len(buf) > 0:
                wf.writeframes(buf.tobytes())
        wf.close()
