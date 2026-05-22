import numpy as np


def mix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    min_len = min(len(a), len(b))
    mixed = a[:min_len].astype(np.int32) + b[:min_len].astype(np.int32)
    return np.clip(mixed, -32768, 32767).astype(np.int16)


def normalize_length(a: np.ndarray, b: np.ndarray):
    if len(a) < len(b):
        a = np.pad(a, ((0, len(b) - len(a)), (0, 0)), mode="constant")
    elif len(b) < len(a):
        b = np.pad(b, ((0, len(a) - len(b)), (0, 0)), mode="constant")
    return a, b
