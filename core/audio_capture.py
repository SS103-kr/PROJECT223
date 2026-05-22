import queue
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44100
CHANNELS = 2
DTYPE = "int16"
BLOCKSIZE = 1024


def get_wasapi_hostapi_index() -> int:
    for i, api in enumerate(sd.query_hostapis()):
        if "WASAPI" in api["name"]:
            return i
    return -1


class AudioCapture:
    def __init__(self):
        self._mic_stream = None
        self._sys_stream = None
        self._audio_queue = None

    def start(self, audio_queue: queue.Queue, mic_device=None, system_device=None,
              mic_enabled=True, system_enabled=True):
        self._audio_queue = audio_queue

        if mic_enabled:
            try:
                kwargs = {"channels": CHANNELS, "samplerate": SAMPLE_RATE,
                          "dtype": DTYPE, "blocksize": BLOCKSIZE,
                          "callback": self._make_callback("mic")}
                if mic_device is not None and mic_device >= 0:
                    kwargs["device"] = mic_device
                self._mic_stream = sd.InputStream(**kwargs)
                self._mic_stream.start()
            except Exception as e:
                print(f"[AudioCapture] 마이크 오류: {e}")
                self._mic_stream = None

        if system_enabled:
            try:
                dev_idx = system_device
                if dev_idx is None or dev_idx < 0:
                    dev_idx = sd.default.device[1]
                self._sys_stream = sd.InputStream(
                    device=dev_idx,
                    channels=CHANNELS,
                    samplerate=SAMPLE_RATE,
                    dtype=DTYPE,
                    blocksize=BLOCKSIZE,
                    callback=self._make_callback("system"),
                    extra_settings=sd.WasapiSettings(loopback=True),
                )
                self._sys_stream.start()
            except Exception as e:
                print(f"[AudioCapture] 시스템 오디오 오류: {e}")
                self._sys_stream = None

    def _make_callback(self, source: str):
        def callback(indata, frames, time_info, status):
            if self._audio_queue is not None:
                try:
                    self._audio_queue.put_nowait((source, indata.copy()))
                except queue.Full:
                    pass
        return callback

    def stop(self):
        for stream in (self._mic_stream, self._sys_stream):
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
        self._mic_stream = None
        self._sys_stream = None
